"""Domain services that orchestrate the store + cross-cutting concerns."""

from __future__ import annotations

from datetime import datetime, time, timedelta

from .models import (
    Appointment,
    CareRecipient,
    HandoffLog,
    Medication,
    TodaySummary,
)
from .store import Store


def init_recipient(store: Store, name: str, age: int | None = None) -> CareRecipient:
    r = CareRecipient(name=name, age=age)
    store.set_recipient(r)
    return r


def require_recipient(store: Store) -> CareRecipient:
    r = store.get_recipient()
    if r is None:
        raise RuntimeError("No care recipient configured. Run: caregiver-os init --care-recipient '<name>'")
    return r


def medications_due_today(meds: list[Medication], now: datetime | None = None) -> list[Medication]:
    """Return medications that have a scheduled time on the current date."""
    now = now or datetime.now()
    today = now.date()
    out: list[Medication] = []
    for m in meds:
        if not m.active:
            continue
        for t in m.times:
            dt = datetime.combine(today, t)
            if dt.date() == today:
                out.append(m)
                break
    return out


def upcoming_appointments(
    appts: list[Appointment],
    within_hours: int = 48,
    now: datetime | None = None,
) -> list[Appointment]:
    now = now or datetime.now()
    horizon = now + timedelta(hours=within_hours)
    return sorted(
        [a for a in appts if not a.completed and now <= a.at <= horizon],
        key=lambda a: a.at,
    )


def today_summary(store: Store, now: datetime | None = None) -> TodaySummary:
    r = require_recipient(store)
    meds = store.list_meds()
    appts = store.list_appointments()
    handoffs = sorted(store.list_handoffs(), key=lambda h: h.shift_start, reverse=True)
    open_handoff = next((h for h in handoffs if h.shift_end is None), None)
    recent_incidents = []
    for h in handoffs[:5]:
        for inc in h.incidents:
            recent_incidents.append(inc)
    return TodaySummary(
        recipient=r,
        upcoming_appointments=upcoming_appointments(appts, now=now),
        medications_due=medications_due_today(meds, now=now),
        open_handoff=open_handoff,
        recent_incidents=recent_incidents[:10],
    )


def start_handoff(store: Store, caregiver: str) -> HandoffLog:
    r = require_recipient(store)
    h = HandoffLog(care_recipient_id=r.id, caregiver=caregiver)
    store.add_handoff(h)
    return h


def parse_times(spec: str) -> list[time]:
    """Parse "09:00,21:00" into [time(9,0), time(21,0)]."""
    out: list[time] = []
    for chunk in spec.split(","):
        chunk = chunk.strip()
        if not chunk:
            continue
        hh, mm = chunk.split(":", 1)
        out.append(time(int(hh), int(mm)))
    return out
