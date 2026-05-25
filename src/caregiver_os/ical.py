"""iCal feed parser and synchronization for caregiver-os."""

from __future__ import annotations

import re
import urllib.request
from datetime import datetime, timezone
from uuid import NAMESPACE_OID, uuid5

from .models import Appointment
from .store import Store


def parse_ical_datetime(val: str) -> datetime:
    """Parse iCal DTSTART values safely into datetime objects."""
    # Remove timezone suffix Z if present
    val = val.strip()
    clean_val = val.rstrip("Z")
    
    # Try parsing different formats
    # 1. YYYYMMDDTHHMMSS (15 chars)
    if "T" in clean_val:
        parts = clean_val.split("T")
        date_part = parts[0]
        time_part = parts[1]
        
        # Strip any extra offset if exists e.g. 20260525T100000+0200
        time_part = re.split(r"[+-]", time_part)[0]
        
        try:
            return datetime.strptime(f"{date_part}T{time_part[:6]}", "%Y%m%dT%H%M%S")
        except ValueError:
            pass
            
    # 2. YYYYMMDD (8 chars, date only)
    if len(clean_val) >= 8:
        try:
            return datetime.strptime(clean_val[:8], "%Y%m%d")
        except ValueError:
            pass

    return datetime.now(timezone.utc)


def parse_ical_text(val: str) -> str:
    """Clean up escaped characters in iCal text fields."""
    val = val.replace("\\,", ",").replace("\\;", ";").replace("\\n", "\n").replace("\\N", "\n")
    return val.strip()


def sync_ical_feed(url: str, store: Store) -> int:
    """Download, parse, and upsert appointments from an iCal feed.

    Returns the number of synchronized appointments.
    """
    try:
        req = urllib.request.Request(
            url, 
            headers={"User-Agent": "Mozilla/5.0 (CaregiverOS iCal Synchronizer)"}
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            content = response.read().decode("utf-8", errors="ignore")
    except Exception as e:
        print(f"Failed to fetch iCal feed from {url}: {e}")
        return 0

    recipient = store.get_recipient()
    if not recipient:
        return 0

    # Locate VEVENT blocks
    events = re.findall(r"BEGIN:VEVENT(.*?)END:VEVENT", content, re.DOTALL)
    imported_count = 0

    for ev in events:
        # Extract fields using regex
        summary_m = re.search(r"^SUMMARY:(.*)$", ev, re.MULTILINE)
        dtstart_m = re.search(r"^DTSTART(?:;[^:]*)?:(.*)$", ev, re.MULTILINE)
        uid_m = re.search(r"^UID:(.*)$", ev, re.MULTILINE)
        loc_m = re.search(r"^LOCATION:(.*)$", ev, re.MULTILINE)
        desc_m = re.search(r"^DESCRIPTION:(.*)$", ev, re.MULTILINE)

        if not dtstart_m:
            continue

        # Get values
        summary = parse_ical_text(summary_m.group(1)) if summary_m else "Appointment"
        dtstart_val = dtstart_m.group(1).strip()
        at_dt = parse_ical_datetime(dtstart_val)
        
        # Use UID to generate deterministic UUID, ensuring idempotency
        uid_str = uid_m.group(1).strip() if uid_m else f"{summary}-{dtstart_val}"
        deterministic_id = uuid5(NAMESPACE_OID, uid_str)

        location = parse_ical_text(loc_m.group(1)) if loc_m else None
        purpose = parse_ical_text(desc_m.group(1)) if desc_m else None

        # Build appointment
        appt = Appointment(
            id=deterministic_id,
            care_recipient_id=recipient.id,
            provider=summary,
            at=at_dt,
            location=location,
            purpose=purpose,
            completed=False
        )

        # Upsert: check if already exists, otherwise add it
        session = store.SessionLocal()
        try:
            from .store import DBAppointment
            existing = session.query(DBAppointment).filter(DBAppointment.id == deterministic_id).first()
            if existing:
                # Update editable fields from calendar if not completed
                if not existing.completed:
                    existing.provider = appt.provider
                    existing.at = appt.at
                    existing.location = appt.location
                    existing.purpose = appt.purpose
            else:
                db_appt = DBAppointment(
                    id=appt.id,
                    care_recipient_id=appt.care_recipient_id,
                    provider=appt.provider,
                    at=appt.at,
                    location=appt.location,
                    purpose=appt.purpose,
                    completed=appt.completed
                )
                session.add(db_appt)
            session.commit()
            imported_count += 1
        except Exception as e:
            session.rollback()
            print(f"Error syncing event {summary}: {e}")
        finally:
            session.close()

    return imported_count
