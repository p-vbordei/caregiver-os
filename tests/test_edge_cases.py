"""Edge-case coverage for services, store round-trips, and models."""

from __future__ import annotations

from datetime import datetime, time, timedelta
from pathlib import Path

import pytest

from caregiver_os.models import (
    Appointment,
    HandoffLog,
    Incident,
    IncidentKind,
    IncidentSeverity,
    Medication,
)
from caregiver_os.services import (
    init_recipient,
    medications_due_today,
    parse_times,
    start_handoff,
    today_summary,
    upcoming_appointments,
)
from caregiver_os.store import Store


# --- fixtures ---------------------------------------------------------------


@pytest.fixture
def store(tmp_path: Path) -> Store:
    return Store(root=tmp_path)


def _make_med(rid, **kwargs) -> Medication:
    base = dict(care_recipient_id=rid, name="X", dose="1mg", times=[time(9, 0)])
    base.update(kwargs)
    return Medication(**base)


# --- medications_due_today -------------------------------------------------


def test_meds_due_empty_list() -> None:
    assert medications_due_today([]) == []


def test_meds_due_all_inactive(store: Store) -> None:
    r = init_recipient(store, "Mom")
    inactive_meds = [
        _make_med(r.id, name="A", active=False),
        _make_med(r.id, name="B", active=False),
    ]
    assert medications_due_today(inactive_meds) == []


def test_meds_due_multiple_with_times(store: Store) -> None:
    r = init_recipient(store, "Mom")
    meds = [
        _make_med(r.id, name="A", times=[time(8, 0)]),
        _make_med(r.id, name="B", times=[time(12, 0), time(20, 0)]),
        _make_med(r.id, name="C", times=[time(7, 30)]),
    ]
    due = medications_due_today(meds)
    assert {m.name for m in due} == {"A", "B", "C"}


def test_meds_due_empty_times_not_due(store: Store) -> None:
    r = init_recipient(store, "Mom")
    meds = [_make_med(r.id, name="NoTimes", times=[])]
    assert medications_due_today(meds) == []


# --- upcoming_appointments -------------------------------------------------


def test_upcoming_excludes_completed(store: Store) -> None:
    r = init_recipient(store, "Mom")
    now = datetime(2026, 5, 24, 10, 0)
    appts = [
        Appointment(
            care_recipient_id=r.id,
            provider="Done Doc",
            at=now + timedelta(hours=2),
            completed=True,
        ),
        Appointment(
            care_recipient_id=r.id,
            provider="Open Doc",
            at=now + timedelta(hours=3),
        ),
    ]
    up = upcoming_appointments(appts, now=now)
    assert [a.provider for a in up] == ["Open Doc"]


def test_upcoming_excludes_past(store: Store) -> None:
    r = init_recipient(store, "Mom")
    now = datetime(2026, 5, 24, 10, 0)
    appts = [
        Appointment(care_recipient_id=r.id, provider="Past", at=now - timedelta(hours=1)),
        Appointment(care_recipient_id=r.id, provider="Future", at=now + timedelta(hours=1)),
    ]
    up = upcoming_appointments(appts, now=now)
    assert [a.provider for a in up] == ["Future"]


def test_upcoming_excludes_far_future(store: Store) -> None:
    r = init_recipient(store, "Mom")
    now = datetime(2026, 5, 24, 10, 0)
    appts = [
        Appointment(care_recipient_id=r.id, provider="Soon", at=now + timedelta(hours=1)),
        Appointment(
            care_recipient_id=r.id,
            provider="Beyond",
            at=now + timedelta(hours=49),  # default within_hours=48
        ),
    ]
    up = upcoming_appointments(appts, now=now, within_hours=48)
    assert [a.provider for a in up] == ["Soon"]


def test_upcoming_sorted_ascending(store: Store) -> None:
    r = init_recipient(store, "Mom")
    now = datetime(2026, 5, 24, 10, 0)
    appts = [
        Appointment(care_recipient_id=r.id, provider="Late", at=now + timedelta(hours=20)),
        Appointment(care_recipient_id=r.id, provider="Early", at=now + timedelta(hours=2)),
        Appointment(care_recipient_id=r.id, provider="Mid", at=now + timedelta(hours=8)),
    ]
    up = upcoming_appointments(appts, now=now)
    assert [a.provider for a in up] == ["Early", "Mid", "Late"]


# --- today_summary ----------------------------------------------------------


def test_today_summary_no_recipient_raises(store: Store) -> None:
    with pytest.raises(RuntimeError, match="No care recipient"):
        today_summary(store)


# --- start_handoff ----------------------------------------------------------


def test_start_handoff_creates_open(store: Store) -> None:
    init_recipient(store, "Mom")
    h = start_handoff(store, caregiver="Alice")
    assert h.shift_end is None
    assert h.caregiver == "Alice"
    # Persisted as open
    persisted = store.list_handoffs()
    assert len(persisted) == 1
    assert persisted[0].shift_end is None


# --- parse_times ------------------------------------------------------------


def test_parse_times_empty() -> None:
    assert parse_times("") == []


def test_parse_times_single() -> None:
    assert parse_times("09:00") == [time(9, 0)]


def test_parse_times_multiple_with_spaces() -> None:
    assert parse_times("09:00, 12:30, 21:00") == [time(9, 0), time(12, 30), time(21, 0)]


def test_parse_times_invalid_raises() -> None:
    # Current behaviour: "abc" has no ':' -> ValueError from split unpacking.
    with pytest.raises(ValueError):
        parse_times("abc")


# --- Store round-trip -------------------------------------------------------


def test_store_recipient_roundtrip(tmp_path: Path) -> None:
    s1 = Store(root=tmp_path)
    init_recipient(s1, "Maria", age=78)
    s2 = Store(root=tmp_path)
    r = s2.get_recipient()
    assert r is not None
    assert r.name == "Maria"
    assert r.age == 78


def test_store_collections_roundtrip(tmp_path: Path) -> None:
    s1 = Store(root=tmp_path)
    r = init_recipient(s1, "Maria")
    s1.add_med(
        Medication(care_recipient_id=r.id, name="Atorvastatin", dose="20mg", times=[time(9, 0)])
    )
    s1.add_appointment(
        Appointment(care_recipient_id=r.id, provider="Dr Smith", at=datetime(2026, 6, 1, 9, 0))
    )
    s1.add_handoff(HandoffLog(care_recipient_id=r.id, caregiver="Alice"))

    s2 = Store(root=tmp_path)
    meds = s2.list_meds()
    appts = s2.list_appointments()
    handoffs = s2.list_handoffs()
    assert len(meds) == 1 and meds[0].name == "Atorvastatin"
    assert len(appts) == 1 and appts[0].provider == "Dr Smith"
    assert len(handoffs) == 1 and handoffs[0].caregiver == "Alice"


def test_store_fresh_instance_same_root(tmp_path: Path) -> None:
    Store(root=tmp_path)  # creates dir
    fresh = Store(root=tmp_path)  # re-opens cleanly
    assert fresh.get_recipient() is None
    assert fresh.list_meds() == []


# --- Pydantic model behaviour ----------------------------------------------


def test_medication_accepts_plausible_values(store: Store) -> None:
    r = init_recipient(store, "Mom")
    m = Medication(
        care_recipient_id=r.id,
        name="Vitamin D",
        dose="1000IU",
        times=[time(9, 0)],
        instructions="Take with food",
        refill_at_days_left=14,
        active=True,
    )
    assert m.refill_at_days_left == 14
    assert m.active is True


def test_medication_no_validation_on_negative_refill(store: Store) -> None:
    """Documents that there is no Pydantic constraint on refill_at_days_left.

    A negative value is currently accepted. If you want guardrails, add
    `Field(ge=0)` in models.py.
    """
    r = init_recipient(store, "Mom")
    m = Medication(care_recipient_id=r.id, name="X", dose="1mg", refill_at_days_left=-3)
    assert m.refill_at_days_left == -3  # no validation today


@pytest.mark.parametrize(
    "kind",
    ["fall", "confusion", "missed_meal", "medication_refusal", "other"],
)
@pytest.mark.parametrize("severity", ["info", "warning", "alert"])
def test_incident_kind_and_severity_roundtrip(
    kind: IncidentKind, severity: IncidentSeverity
) -> None:
    i = Incident(kind=kind, severity=severity, description="desc")
    dumped = i.model_dump(mode="json")
    restored = Incident(**dumped)
    assert restored.kind == kind
    assert restored.severity == severity
    assert restored.description == "desc"
