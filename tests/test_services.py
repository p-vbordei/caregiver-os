from datetime import datetime, time
from pathlib import Path

import pytest

from caregiver_os.models import Appointment, Medication
from caregiver_os.services import (
    init_recipient,
    medications_due_today,
    today_summary,
    upcoming_appointments,
)
from caregiver_os.store import Store


@pytest.fixture
def store(tmp_path: Path) -> Store:
    return Store(root=tmp_path)


def test_init_and_today(store: Store) -> None:
    init_recipient(store, "Mom (Maria, 78)", age=78)
    s = today_summary(store)
    assert s.recipient.name.startswith("Mom")
    assert s.medications_due == []


def test_meds_due(store: Store) -> None:
    r = init_recipient(store, "Mom")
    store.add_med(Medication(
        care_recipient_id=r.id,
        name="Atorvastatin",
        dose="20mg",
        times=[time(9, 0), time(21, 0)],
    ))
    store.add_med(Medication(
        care_recipient_id=r.id,
        name="Inactive med",
        dose="10mg",
        times=[time(8, 0)],
        active=False,
    ))
    due = medications_due_today(store.list_meds())
    assert len(due) == 1
    assert due[0].name == "Atorvastatin"


def test_upcoming(store: Store) -> None:
    r = init_recipient(store, "Mom")
    now = datetime(2026, 5, 24, 10, 0)
    store.add_appointment(Appointment(
        care_recipient_id=r.id,
        provider="Dr Smith",
        at=datetime(2026, 5, 25, 9, 0),
    ))
    store.add_appointment(Appointment(
        care_recipient_id=r.id,
        provider="Dr Future",
        at=datetime(2026, 6, 1, 9, 0),
    ))
    up = upcoming_appointments(store.list_appointments(), now=now)
    assert len(up) == 1
    assert up[0].provider == "Dr Smith"
