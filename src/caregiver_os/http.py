"""FastAPI service exposing caregiver-os over local HTTP."""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, HTTPException

from .models import Appointment, HandoffLog, Medication
from .services import require_recipient, today_summary
from .store import Store


def create_app() -> FastAPI:
    api = FastAPI(title="caregiver-os", version="2026.5.24")

    @api.get("/v1/today")
    def get_today() -> dict[str, Any]:
        try:
            s = today_summary(Store())
        except RuntimeError as e:
            raise HTTPException(status_code=400, detail=str(e))
        return s.model_dump(mode="json")

    @api.get("/v1/recipient")
    def get_recipient() -> dict[str, Any]:
        r = Store().get_recipient()
        if not r:
            raise HTTPException(status_code=404, detail="No recipient configured")
        return r.model_dump(mode="json")

    @api.get("/v1/meds")
    def list_meds() -> list[dict[str, Any]]:
        return [m.model_dump(mode="json") for m in Store().list_meds()]

    @api.post("/v1/meds")
    def add_med(med: Medication) -> dict[str, Any]:
        Store().add_med(med)
        return med.model_dump(mode="json")

    @api.get("/v1/appointments")
    def list_appts() -> list[dict[str, Any]]:
        return [a.model_dump(mode="json") for a in Store().list_appointments()]

    @api.post("/v1/appointments")
    def add_appt(appt: Appointment) -> dict[str, Any]:
        Store().add_appointment(appt)
        return appt.model_dump(mode="json")

    @api.get("/v1/handoffs")
    def list_handoffs() -> list[dict[str, Any]]:
        return [h.model_dump(mode="json") for h in Store().list_handoffs()]

    @api.post("/v1/handoffs")
    def add_handoff(h: HandoffLog) -> dict[str, Any]:
        Store().add_handoff(h)
        return h.model_dump(mode="json")

    return api


def run(host: str = "127.0.0.1", port: int = 7878) -> None:
    import uvicorn

    uvicorn.run(create_app, host=host, port=port, factory=True)
