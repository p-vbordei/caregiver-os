"""In-process JSON store. Replace with SQLAlchemy + SQLite in v0.2."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from uuid import UUID

from .models import (
    Appointment,
    CarePlan,
    CareRecipient,
    HandoffLog,
    Medication,
)

DEFAULT_DIR = Path.home() / ".caregiver-os"


class Store:
    """Single-recipient JSON-file store. One file per collection.

    The MVP intentionally avoids SQLAlchemy for ease of inspection; the
    schema is small enough that a JSON tree is reasonable. v0.2 swaps in
    SQLite + Alembic-managed migrations.
    """

    def __init__(self, root: Path = DEFAULT_DIR) -> None:
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, name: str) -> Path:
        return self.root / f"{name}.json"

    def _read(self, name: str) -> list[dict[str, Any]]:
        path = self._path(name)
        if not path.exists():
            return []
        return json.loads(path.read_text())

    def _write(self, name: str, items: list[dict[str, Any]]) -> None:
        self._path(name).write_text(json.dumps(items, indent=2, default=str))

    # Recipient
    def get_recipient(self) -> CareRecipient | None:
        items = self._read("recipient")
        return CareRecipient(**items[0]) if items else None

    def set_recipient(self, r: CareRecipient) -> None:
        self._write("recipient", [r.model_dump(mode="json")])

    # Medications
    def list_meds(self) -> list[Medication]:
        return [Medication(**m) for m in self._read("medications")]

    def add_med(self, m: Medication) -> None:
        items = self._read("medications")
        items.append(m.model_dump(mode="json"))
        self._write("medications", items)

    def deactivate_med(self, med_id: UUID) -> None:
        items = self._read("medications")
        for it in items:
            if it["id"] == str(med_id):
                it["active"] = False
        self._write("medications", items)

    # Appointments
    def list_appointments(self) -> list[Appointment]:
        return [Appointment(**a) for a in self._read("appointments")]

    def add_appointment(self, a: Appointment) -> None:
        items = self._read("appointments")
        items.append(a.model_dump(mode="json"))
        self._write("appointments", items)

    def complete_appointment(self, appt_id: UUID) -> None:
        items = self._read("appointments")
        for it in items:
            if it["id"] == str(appt_id):
                it["completed"] = True
        self._write("appointments", items)

    # Handoffs
    def list_handoffs(self) -> list[HandoffLog]:
        return [HandoffLog(**h) for h in self._read("handoffs")]

    def add_handoff(self, h: HandoffLog) -> None:
        items = self._read("handoffs")
        items.append(h.model_dump(mode="json"))
        self._write("handoffs", items)

    # CarePlan
    def list_careplan_versions(self) -> list[CarePlan]:
        return [CarePlan(**p) for p in self._read("careplan")]

    def add_careplan(self, p: CarePlan) -> None:
        items = self._read("careplan")
        items.append(p.model_dump(mode="json"))
        self._write("careplan", items)
