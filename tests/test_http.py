"""HTTP-layer tests using FastAPI's TestClient.

Routes construct `Store()` inline, which defaults to `~/.caregiver-os`.
We monkeypatch `store.DEFAULT_DIR` to redirect at construction time so
tests are isolated to `tmp_path`.
"""

from __future__ import annotations

from datetime import datetime, time
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from caregiver_os import http as http_module
from caregiver_os.models import CareRecipient
from caregiver_os.store import Store as _RealStore


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    # Routes call `Store()` with no args. `Store.__init__`'s default
    # `root=DEFAULT_DIR` is bound at function-definition time, so patching
    # the module attribute does NOT redirect. Instead, swap the `Store`
    # symbol that http.py looked up at import time with a factory that
    # uses tmp_path.
    def _make() -> _RealStore:
        return _RealStore(root=tmp_path)

    monkeypatch.setattr(http_module, "Store", _make)
    return TestClient(http_module.create_app())


def test_get_today_no_recipient_returns_400(client: TestClient) -> None:
    resp = client.get("/v1/today")
    assert resp.status_code == 400
    assert "No care recipient" in resp.json()["detail"]


def test_put_recipient_then_get(client: TestClient, tmp_path: Path) -> None:
    # No PUT endpoint exists; seed via Store directly to match the API surface.
    _RealStore(root=tmp_path).set_recipient(CareRecipient(name="Maria", age=78))
    resp = client.get("/v1/recipient")
    assert resp.status_code == 200
    body = resp.json()
    assert body["name"] == "Maria"
    assert body["age"] == 78


def test_post_meds_then_get_includes_it(client: TestClient, tmp_path: Path) -> None:
    _RealStore(root=tmp_path).set_recipient(CareRecipient(name="Maria"))
    rid = _RealStore(root=tmp_path).get_recipient().id  # type: ignore[union-attr]
    payload = {
        "care_recipient_id": str(rid),
        "name": "Atorvastatin",
        "dose": "20mg",
        "times": [time(9, 0).isoformat()],
    }
    resp = client.post("/v1/meds", json=payload)
    assert resp.status_code == 200, resp.text

    listed = client.get("/v1/meds")
    assert listed.status_code == 200
    names = [m["name"] for m in listed.json()]
    assert "Atorvastatin" in names


def test_post_appointments_then_get_includes_it(client: TestClient, tmp_path: Path) -> None:
    _RealStore(root=tmp_path).set_recipient(CareRecipient(name="Maria"))
    rid = _RealStore(root=tmp_path).get_recipient().id  # type: ignore[union-attr]
    payload = {
        "care_recipient_id": str(rid),
        "provider": "Dr Smith",
        "at": datetime(2026, 6, 1, 9, 0).isoformat(),
        "purpose": "checkup",
    }
    resp = client.post("/v1/appointments", json=payload)
    assert resp.status_code == 200, resp.text

    listed = client.get("/v1/appointments")
    assert listed.status_code == 200
    providers = [a["provider"] for a in listed.json()]
    assert "Dr Smith" in providers


def test_recipient_404_when_missing(client: TestClient) -> None:
    resp = client.get("/v1/recipient")
    assert resp.status_code == 404
