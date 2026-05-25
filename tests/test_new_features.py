"""Unit and integration tests for new Caregiver OS features."""

from __future__ import annotations

import os
from datetime import datetime, time
from pathlib import Path
from uuid import UUID, uuid4

import pytest

from caregiver_os.ai import explain_shift
from caregiver_os.i18n import t
from caregiver_os.ical import parse_ical_datetime, parse_ical_text, sync_ical_feed
from caregiver_os.models import HandoffLog, Incident, Medication
from caregiver_os.store import Store


@pytest.fixture
def store(tmp_path: Path) -> Store:
    return Store(root=tmp_path)


# --- 1. Localization Tests ---

def test_localization_translation() -> None:
    # Test English translation
    msg_en = t("initialized", lang="en", name="Maria", id="123")
    assert "Initialized: Maria (123)" in msg_en

    # Test Romanian translation
    msg_ro = t("initialized", lang="ro", name="Maria", id="123")
    assert "Inițializat: Maria (123)" in msg_ro


def test_localization_fallback() -> None:
    # Key that exists in EN but not explicitly separated from RO
    assert t("yes", lang="ro") == "da"
    assert t("yes", lang="en") == "yes"
    
    # Fallback to key itself if not found
    assert t("non_existent_key", lang="en") == "non_existent_key"


# --- 2. iCal Parser Tests ---

def test_parse_ical_datetime() -> None:
    # UTC format
    dt1 = parse_ical_datetime("20260525T100000Z")
    assert dt1.year == 2026 and dt1.month == 5 and dt1.day == 25 and dt1.hour == 10

    # Local format
    dt2 = parse_ical_datetime("20260525T143000")
    assert dt2.year == 2026 and dt2.month == 5 and dt2.day == 25 and dt2.hour == 14 and dt2.minute == 30

    # Date only format
    dt3 = parse_ical_datetime("20260525")
    assert dt3.year == 2026 and dt3.month == 5 and dt3.day == 25 and dt3.hour == 0


def test_parse_ical_text() -> None:
    assert parse_ical_text("Dr. Smith\\, Cardiologist") == "Dr. Smith, Cardiologist"
    assert parse_ical_text("Line 1\\nLine 2") == "Line 1\nLine 2"


# --- 3. Consent Gate approvals ---

def test_consent_gate_workflow(store: Store) -> None:
    # Recipient configuration
    from caregiver_os.models import CareRecipient
    store.set_recipient(store.get_recipient() or CareRecipient(name="Mom", age=78))
    
    # 1. Queue pending approval
    args = {"name": "Aspirin", "dose": "81mg", "times": "08:00"}
    app_id = store.add_pending_approval("add_medication", args)
    
    # 2. Check pending approvals list
    pending = store.list_pending_approvals()
    assert len(pending) == 1
    assert pending[0]["id"] == str(app_id)
    assert pending[0]["tool_name"] == "add_medication"
    assert pending[0]["arguments"]["name"] == "Aspirin"
    
    # 3. Deny approval
    store.set_approval_status(app_id, "denied")
    assert len(store.list_pending_approvals()) == 0
    
    # Verify status in DB
    appr = store.get_approval(app_id)
    assert appr is not None
    assert appr["status"] == "denied"


# --- 4. Shift Explainer ---

def test_explain_shift_local_fallback(store: Store) -> None:
    # Ensure recipient exists
    from caregiver_os.services import init_recipient
    r = init_recipient(store, "Maria", 78)
    
    # Add medication for name mapping
    med = Medication(care_recipient_id=r.id, name="Aspirin", dose="81mg", times=[time(8, 0)])
    store.add_med(med)
    
    # Create handoff log
    h = HandoffLog(
        care_recipient_id=r.id,
        shift_start=datetime(2026, 5, 25, 8, 0),
        shift_end=datetime(2026, 5, 25, 16, 0),
        caregiver="Alice",
        vitals="BP 120/80",
        mood="calm",
        meals="Breakfast full",
        medications_given=[med.id],
        incidents=[Incident(kind="other", description="refused afternoon tea", severity="info")],
        notes="All good"
    )
    store.add_handoff(h)
    
    # Test EN summary
    summary_en = explain_shift(h, store, lang="en")
    assert "Shift Summary for Maria" in summary_en
    assert "Aspirin (81mg)" in summary_en
    assert "Alice" in summary_en
    assert "refused afternoon tea" in summary_en
    
    # Test RO summary
    summary_ro = explain_shift(h, store, lang="ro")
    assert "Sumarul schimbului pentru Maria" in summary_ro
    assert "Aspirin (81mg)" in summary_ro
    assert "Îngrijitor" in summary_ro
