"""SQLAlchemy + SQLite store for caregiver-os."""

from __future__ import annotations

import json
from datetime import datetime, time, timezone
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    TypeDecorator,
    create_engine,
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

from .models import (
    Appointment,
    CarePlan,
    CareRecipient,
    HandoffLog,
    Incident,
    Medication,
)

DEFAULT_DIR = Path.home() / ".caregiver-os"
Base = declarative_base()


class UUIDString(TypeDecorator):
    """Platform-independent UUID type stored as string."""

    impl = String(36)
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if isinstance(value, UUID):
            return str(value)
        return value

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return UUID(value)


class JSONText(TypeDecorator):
    """Store JSON as Text in SQLite."""

    impl = Text
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        return json.dumps(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return json.loads(value)


# --- SQLAlchemy Database Models ---

class DBCareRecipient(Base):
    __tablename__ = "care_recipients"

    id = Column(UUIDString, primary_key=True, default=uuid4)
    name = Column(String(255), nullable=False)
    age = Column(Integer, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class DBMedication(Base):
    __tablename__ = "medications"

    id = Column(UUIDString, primary_key=True, default=uuid4)
    care_recipient_id = Column(UUIDString, ForeignKey("care_recipients.id"), nullable=False)
    name = Column(String(255), nullable=False)
    dose = Column(String(100), nullable=False)
    times = Column(JSONText, nullable=False)  # list of strings "HH:MM:SS"
    instructions = Column(Text, nullable=True)
    refill_at_days_left = Column(Integer, default=7)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class DBAppointment(Base):
    __tablename__ = "appointments"

    id = Column(UUIDString, primary_key=True, default=uuid4)
    care_recipient_id = Column(UUIDString, ForeignKey("care_recipients.id"), nullable=False)
    provider = Column(String(255), nullable=False)
    at = Column(DateTime, nullable=False)
    location = Column(String(500), nullable=True)
    purpose = Column(Text, nullable=True)
    completed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class DBHandoffLog(Base):
    __tablename__ = "handoff_logs"

    id = Column(UUIDString, primary_key=True, default=uuid4)
    care_recipient_id = Column(UUIDString, ForeignKey("care_recipients.id"), nullable=False)
    shift_start = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    shift_end = Column(DateTime, nullable=True)
    caregiver = Column(String(255), nullable=False)
    vitals = Column(Text, nullable=True)
    mood = Column(String(255), nullable=True)
    meals = Column(Text, nullable=True)
    medications_given = Column(JSONText, nullable=False)  # list of UUID strings
    notes = Column(Text, nullable=True)

    incidents = relationship("DBIncident", back_populates="handoff_log", cascade="all, delete-orphan")


class DBIncident(Base):
    __tablename__ = "incidents"

    id = Column(UUIDString, primary_key=True, default=uuid4)
    handoff_log_id = Column(UUIDString, ForeignKey("handoff_logs.id"), nullable=False)
    kind = Column(String(50), nullable=False)
    at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    description = Column(Text, nullable=False)
    severity = Column(String(50), default="info")

    handoff_log = relationship("DBHandoffLog", back_populates="incidents")


class DBCarePlan(Base):
    __tablename__ = "care_plans"

    id = Column(UUIDString, primary_key=True, default=uuid4)
    care_recipient_id = Column(UUIDString, ForeignKey("care_recipients.id"), nullable=False)
    version = Column(Integer, default=1)
    markdown = Column(Text, nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_by = Column(String(255), nullable=False)


class DBPendingApproval(Base):
    __tablename__ = "pending_approvals"

    id = Column(UUIDString, primary_key=True, default=uuid4)
    tool_name = Column(String(100), nullable=False)
    arguments = Column(Text, nullable=False)  # JSON string
    status = Column(String(50), default="pending")  # pending, approved, denied
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class DBProfile(Base):
    __tablename__ = "profiles"

    id = Column(UUIDString, primary_key=True, default=uuid4)
    name = Column(String(255), nullable=False, unique=True)
    role = Column(String(50), default="caregiver")  # admin, caregiver, viewer
    language = Column(String(10), default="en")  # en, ro
    pin = Column(String(10), nullable=True)  # simple 4-digit pin or passcode
    active = Column(Boolean, default=True)


class DBSetting(Base):
    __tablename__ = "settings"

    key = Column(String(255), primary_key=True)
    value = Column(Text, nullable=True)


# --- Store Implementation ---

class Store:
    """SQLAlchemy-based SQLite Store for caregiver-os."""

    def __init__(self, root: Path = DEFAULT_DIR) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.db_path = self.root / "store.sqlite"
        self.engine = create_engine(f"sqlite:///{self.db_path}", connect_args={"check_same_thread": False})
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine)
        
        # Check if migration from JSON is needed
        self._migrate_from_json()

    def _migrate_from_json(self) -> None:
        """Migrate any existing JSON store files into SQLite."""
        session = self.SessionLocal()
        try:
            # Check if any care recipients are already in SQLite
            if session.query(DBCareRecipient).first() is not None:
                return  # Database already populated

            # JSON store file paths
            recipient_path = self.root / "recipient.json"
            meds_path = self.root / "medications.json"
            appts_path = self.root / "appointments.json"
            handoffs_path = self.root / "handoffs.json"
            careplan_path = self.root / "careplan.json"

            # 1. Care Recipient
            r_id = None
            if recipient_path.exists():
                try:
                    data = json.loads(recipient_path.read_text())
                    if data:
                        r = data[0]
                        db_r = DBCareRecipient(
                            id=UUID(r["id"]),
                            name=r["name"],
                            age=r.get("age"),
                            notes=r.get("notes"),
                            created_at=datetime.fromisoformat(r["created_at"]) if "created_at" in r else datetime.now(timezone.utc)
                        )
                        session.add(db_r)
                        r_id = db_r.id
                except Exception as e:
                    print(f"Error migrating recipient: {e}")

            if not r_id:
                # No recipient to link, cannot migrate the rest safely
                session.commit()
                return

            # 2. Medications
            if meds_path.exists():
                try:
                    data = json.loads(meds_path.read_text())
                    for m in data:
                        # Convert times list to ISO format strings "HH:MM:SS"
                        times_list = m.get("times", [])
                        db_m = DBMedication(
                            id=UUID(m["id"]),
                            care_recipient_id=UUID(m["care_recipient_id"]),
                            name=m["name"],
                            dose=m["dose"],
                            times=times_list,
                            instructions=m.get("instructions"),
                            refill_at_days_left=m.get("refill_at_days_left", 7),
                            active=m.get("active", True),
                            created_at=datetime.fromisoformat(m["created_at"]) if "created_at" in m else datetime.now(timezone.utc)
                        )
                        session.add(db_m)
                except Exception as e:
                    print(f"Error migrating meds: {e}")

            # 3. Appointments
            if appts_path.exists():
                try:
                    data = json.loads(appts_path.read_text())
                    for a in data:
                        db_a = DBAppointment(
                            id=UUID(a["id"]),
                            care_recipient_id=UUID(a["care_recipient_id"]),
                            provider=a["provider"],
                            at=datetime.fromisoformat(a["at"]),
                            location=a.get("location"),
                            purpose=a.get("purpose"),
                            completed=a.get("completed", False),
                            created_at=datetime.fromisoformat(a["created_at"]) if "created_at" in a else datetime.now(timezone.utc)
                        )
                        session.add(db_a)
                except Exception as e:
                    print(f"Error migrating appointments: {e}")

            # 4. Handoff Logs
            if handoffs_path.exists():
                try:
                    data = json.loads(handoffs_path.read_text())
                    for h in data:
                        db_h = DBHandoffLog(
                            id=UUID(h["id"]),
                            care_recipient_id=UUID(h["care_recipient_id"]),
                            shift_start=datetime.fromisoformat(h["shift_start"]),
                            shift_end=datetime.fromisoformat(h["shift_end"]) if h.get("shift_end") else None,
                            caregiver=h["caregiver"],
                            vitals=h.get("vitals"),
                            mood=h.get("mood"),
                            meals=h.get("meals"),
                            medications_given=h.get("medications_given", []),
                            notes=h.get("notes")
                        )
                        session.add(db_h)

                        # Migrate nested incidents
                        for inc in h.get("incidents", []):
                            db_inc = DBIncident(
                                handoff_log_id=db_h.id,
                                kind=inc["kind"],
                                at=datetime.fromisoformat(inc["at"]) if "at" in inc else datetime.now(timezone.utc),
                                description=inc["description"],
                                severity=inc.get("severity", "info")
                            )
                            session.add(db_inc)
                except Exception as e:
                    print(f"Error migrating handoffs: {e}")

            # 5. Care Plan
            if careplan_path.exists():
                try:
                    data = json.loads(careplan_path.read_text())
                    for p in data:
                        db_p = DBCarePlan(
                            id=UUID(p["id"]),
                            care_recipient_id=UUID(p["care_recipient_id"]),
                            version=p.get("version", 1),
                            markdown=p["markdown"],
                            updated_at=datetime.fromisoformat(p["updated_at"]) if "updated_at" in p else datetime.now(timezone.utc),
                            updated_by=p["updated_by"]
                        )
                        session.add(db_p)
                except Exception as e:
                    print(f"Error migrating care plans: {e}")

            session.commit()
        except Exception as e:
            session.rollback()
            print(f"Migration failed: {e}")
        finally:
            session.close()

    # Recipient
    def get_recipient(self) -> CareRecipient | None:
        session = self.SessionLocal()
        try:
            r = session.query(DBCareRecipient).first()
            if not r:
                return None
            return CareRecipient(
                id=r.id,
                name=r.name,
                age=r.age,
                notes=r.notes,
                created_at=r.created_at
            )
        finally:
            session.close()

    def set_recipient(self, r: CareRecipient) -> None:
        session = self.SessionLocal()
        try:
            for recipient in session.query(DBCareRecipient).all():
                session.query(DBMedication).filter(DBMedication.care_recipient_id == recipient.id).delete()
                session.query(DBAppointment).filter(DBAppointment.care_recipient_id == recipient.id).delete()
                for handoff in session.query(DBHandoffLog).filter(DBHandoffLog.care_recipient_id == recipient.id).all():
                    session.query(DBIncident).filter(DBIncident.handoff_log_id == handoff.id).delete()
                session.query(DBHandoffLog).filter(DBHandoffLog.care_recipient_id == recipient.id).delete()
                session.query(DBCarePlan).filter(DBCarePlan.care_recipient_id == recipient.id).delete()
                session.delete(recipient)
            db_r = DBCareRecipient(
                id=r.id,
                name=r.name,
                age=r.age,
                notes=r.notes,
                created_at=r.created_at
            )
            session.add(db_r)
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    # Medications
    def list_meds(self) -> list[Medication]:
        session = self.SessionLocal()
        try:
            items = session.query(DBMedication).all()
            return [
                Medication(
                    id=m.id,
                    care_recipient_id=m.care_recipient_id,
                    name=m.name,
                    dose=m.dose,
                    times=[time.fromisoformat(t) for t in m.times],
                    instructions=m.instructions,
                    refill_at_days_left=m.refill_at_days_left,
                    active=m.active,
                    created_at=m.created_at
                )
                for m in items
            ]
        finally:
            session.close()

    def add_med(self, m: Medication) -> None:
        session = self.SessionLocal()
        try:
            db_m = DBMedication(
                id=m.id,
                care_recipient_id=m.care_recipient_id,
                name=m.name,
                dose=m.dose,
                times=[str(t) for t in m.times],
                instructions=m.instructions,
                refill_at_days_left=m.refill_at_days_left,
                active=m.active,
                created_at=m.created_at
            )
            session.add(db_m)
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def deactivate_med(self, med_id: UUID) -> None:
        session = self.SessionLocal()
        try:
            db_m = session.query(DBMedication).filter(DBMedication.id == med_id).first()
            if db_m:
                db_m.active = False
                session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    # Appointments
    def list_appointments(self) -> list[Appointment]:
        session = self.SessionLocal()
        try:
            items = session.query(DBAppointment).all()
            return [
                Appointment(
                    id=a.id,
                    care_recipient_id=a.care_recipient_id,
                    provider=a.provider,
                    at=a.at,
                    location=a.location,
                    purpose=a.purpose,
                    completed=a.completed,
                    created_at=a.created_at
                )
                for a in items
            ]
        finally:
            session.close()

    def add_appointment(self, a: Appointment) -> None:
        session = self.SessionLocal()
        try:
            db_a = DBAppointment(
                id=a.id,
                care_recipient_id=a.care_recipient_id,
                provider=a.provider,
                at=a.at,
                location=a.location,
                purpose=a.purpose,
                completed=a.completed,
                created_at=a.created_at
            )
            session.add(db_a)
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def complete_appointment(self, appt_id: UUID) -> None:
        session = self.SessionLocal()
        try:
            db_a = session.query(DBAppointment).filter(DBAppointment.id == appt_id).first()
            if db_a:
                db_a.completed = True
                session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def update_appointment(self, appt_id: UUID, **kwargs) -> None:
        session = self.SessionLocal()
        try:
            db_a = session.query(DBAppointment).filter(DBAppointment.id == str(appt_id)).first()
            if db_a:
                for k, v in kwargs.items():
                    if hasattr(db_a, k):
                        setattr(db_a, k, v)
                session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def delete_appointment(self, appt_id: UUID) -> None:
        session = self.SessionLocal()
        try:
            db_a = session.query(DBAppointment).filter(DBAppointment.id == str(appt_id)).first()
            if db_a:
                session.delete(db_a)
                session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    # Handoffs
    def list_handoffs(self) -> list[HandoffLog]:
        session = self.SessionLocal()
        try:
            items = session.query(DBHandoffLog).all()
            result = []
            for h in items:
                # Build Incidents list
                incidents = [
                    Incident(
                        kind=i.kind,  # type: ignore[arg-type]
                        at=i.at,
                        description=i.description,
                        severity=i.severity  # type: ignore[arg-type]
                    )
                    for i in h.incidents
                ]
                
                # Convert medication UUIDs back
                med_ids = [UUID(m) for m in h.medications_given]

                result.append(
                    HandoffLog(
                        id=h.id,
                        care_recipient_id=h.care_recipient_id,
                        shift_start=h.shift_start,
                        shift_end=h.shift_end,
                        caregiver=h.caregiver,
                        vitals=h.vitals,
                        mood=h.mood,
                        meals=h.meals,
                        medications_given=med_ids,
                        incidents=incidents,
                        notes=h.notes
                    )
                )
            return result
        finally:
            session.close()

    def add_handoff(self, h: HandoffLog) -> None:
        session = self.SessionLocal()
        try:
            db_h = DBHandoffLog(
                id=h.id,
                care_recipient_id=h.care_recipient_id,
                shift_start=h.shift_start,
                shift_end=h.shift_end,
                caregiver=h.caregiver,
                vitals=h.vitals,
                mood=h.mood,
                meals=h.meals,
                medications_given=[str(m) for m in h.medications_given],
                notes=h.notes
            )
            session.add(db_h)

            for i in h.incidents:
                db_i = DBIncident(
                    id=uuid4(),
                    handoff_log_id=h.id,
                    kind=i.kind,
                    at=i.at,
                    description=i.description,
                    severity=i.severity
                )
                session.add(db_i)
                
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    # CarePlan
    def list_careplan_versions(self) -> list[CarePlan]:
        session = self.SessionLocal()
        try:
            items = session.query(DBCarePlan).order_by(DBCarePlan.version.asc()).all()
            return [
                CarePlan(
                    id=p.id,
                    care_recipient_id=p.care_recipient_id,
                    version=p.version,
                    markdown=p.markdown,
                    updated_at=p.updated_at,
                    updated_by=p.updated_by
                )
                for p in items
            ]
        finally:
            session.close()

    def add_careplan(self, p: CarePlan) -> None:
        session = self.SessionLocal()
        try:
            db_p = DBCarePlan(
                id=p.id,
                care_recipient_id=p.care_recipient_id,
                version=p.version,
                markdown=p.markdown,
                updated_at=p.updated_at,
                updated_by=p.updated_by
            )
            session.add(db_p)
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    # Settings
    def get_setting(self, key: str, default: str | None = None) -> str | None:
        session = self.SessionLocal()
        try:
            s = session.query(DBSetting).filter(DBSetting.key == key).first()
            return s.value if s else default
        finally:
            session.close()

    def set_setting(self, key: str, value: str | None) -> None:
        session = self.SessionLocal()
        try:
            s = session.query(DBSetting).filter(DBSetting.key == key).first()
            if s:
                if value is None:
                    session.delete(s)
                else:
                    s.value = value
            elif value is not None:
                s = DBSetting(key=key, value=value)
                session.add(s)
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    # Profiles (Caregivers)
    def list_profiles(self) -> list[dict[str, Any]]:
        session = self.SessionLocal()
        try:
            items = session.query(DBProfile).all()
            return [
                {
                    "id": str(p.id),
                    "name": p.name,
                    "role": p.role,
                    "language": p.language,
                    "pin": p.pin,
                    "active": p.active
                }
                for p in items
            ]
        finally:
            session.close()

    def add_profile(self, name: str, role: str = "caregiver", language: str = "en", pin: str | None = None) -> dict[str, Any]:
        session = self.SessionLocal()
        try:
            p = DBProfile(id=uuid4(), name=name, role=role, language=language, pin=pin, active=True)
            session.add(p)
            session.commit()
            return {
                "id": str(p.id),
                "name": p.name,
                "role": p.role,
                "language": p.language,
                "pin": p.pin,
                "active": p.active
            }
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def update_profile(self, profile_id: UUID, **kwargs) -> None:
        session = self.SessionLocal()
        try:
            p = session.query(DBProfile).filter(DBProfile.id == profile_id).first()
            if p:
                for k, v in kwargs.items():
                    if hasattr(p, k):
                        setattr(p, k, v)
                session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    # Pending Approvals (Consent Gate)
    def list_pending_approvals(self) -> list[dict[str, Any]]:
        session = self.SessionLocal()
        try:
            items = session.query(DBPendingApproval).filter(DBPendingApproval.status == "pending").all()
            return [
                {
                    "id": str(a.id),
                    "tool_name": a.tool_name,
                    "arguments": json.loads(a.arguments),
                    "status": a.status,
                    "created_at": a.created_at.isoformat() if a.created_at else ""
                }
                for a in items
            ]
        finally:
            session.close()

    def add_pending_approval(self, tool_name: str, arguments: dict[str, Any]) -> UUID:
        session = self.SessionLocal()
        try:
            a_id = uuid4()
            a = DBPendingApproval(
                id=a_id,
                tool_name=tool_name,
                arguments=json.dumps(arguments),
                status="pending"
            )
            session.add(a)
            session.commit()
            return a_id
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def get_approval(self, approval_id: UUID) -> dict[str, Any] | None:
        session = self.SessionLocal()
        try:
            a = session.query(DBPendingApproval).filter(DBPendingApproval.id == approval_id).first()
            if not a:
                return None
            return {
                "id": str(a.id),
                "tool_name": a.tool_name,
                "arguments": json.loads(a.arguments),
                "status": a.status,
                "created_at": a.created_at.isoformat() if a.created_at else ""
            }
        finally:
            session.close()

    def set_approval_status(self, approval_id: UUID, status: str) -> None:
        session = self.SessionLocal()
        try:
            a = session.query(DBPendingApproval).filter(DBPendingApproval.id == approval_id).first()
            if a:
                a.status = status
                session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def update_handoff(self, h: HandoffLog) -> None:
        session = self.SessionLocal()
        try:
            db_h = session.query(DBHandoffLog).filter(DBHandoffLog.id == str(h.id)).first()
            if db_h:
                db_h.shift_end = h.shift_end
                db_h.caregiver = h.caregiver
                db_h.vitals = h.vitals
                db_h.mood = h.mood
                db_h.meals = h.meals
                db_h.medications_given = [str(m) for m in h.medications_given]
                db_h.notes = h.notes

                session.query(DBIncident).filter(DBIncident.handoff_log_id == str(h.id)).delete()
                for i in h.incidents:
                    db_i = DBIncident(
                        id=uuid4(),
                        handoff_log_id=str(h.id),
                        kind=i.kind,
                        at=i.at,
                        description=i.description,
                        severity=i.severity
                    )
                    session.add(db_i)
                session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
