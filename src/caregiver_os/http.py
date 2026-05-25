"""FastAPI service exposing caregiver-os over HTTP with Static Web UI serving."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import UUID

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .adapters import NotificationManager
from .ai import explain_shift
from .ical import sync_ical_feed
from .models import Appointment, CarePlan, CareRecipient, HandoffLog, Incident, Medication
from .services import today_summary
from .store import Store

# Request/Response schemas helper
class SettingUpdate(BaseModel):
    key: str
    value: str | None

class ProfileCreate(BaseModel):
    name: str
    role: str = "caregiver"
    language: str = "en"
    pin: str | None = None

class ApprovalAction(BaseModel):
    action: str  # approve or deny

class SyncRequest(BaseModel):
    url: str | None = None

class HandoffLogRequest(BaseModel):
    vitals: str | None = None
    mood: str | None = None
    meals: str | None = None
    notes: str | None = None
    incident: str | None = None  # "kind:severity:description"

class CareRecipientCreate(BaseModel):
    name: str
    age: int | None = None
    notes: str | None = None


def create_app() -> FastAPI:
    api = FastAPI(title="caregiver-os", version="2026.5.24")

    # Enable CORS for local network and home automation integrations
    api.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

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

    @api.post("/v1/recipient")
    def post_recipient(req: CareRecipientCreate) -> dict[str, Any]:
        store = Store()
        r = CareRecipient(name=req.name, age=req.age, notes=req.notes)
        store.set_recipient(r)
        return r.model_dump(mode="json")

    # --- Medications ---
    @api.get("/v1/meds")
    def list_meds() -> list[dict[str, Any]]:
        return [m.model_dump(mode="json") for m in Store().list_meds()]

    @api.post("/v1/meds")
    def add_med(med: Medication) -> dict[str, Any]:
        Store().add_med(med)
        return med.model_dump(mode="json")

    @api.post("/v1/meds/{med_id}/deactivate")
    def deactivate_med(med_id: UUID) -> dict[str, str]:
        Store().deactivate_med(med_id)
        return {"status": "deactivated"}

    # --- Appointments ---
    @api.get("/v1/appointments")
    def list_appts() -> list[dict[str, Any]]:
        return [a.model_dump(mode="json") for a in Store().list_appointments()]

    @api.post("/v1/appointments")
    def add_appt(appt: Appointment) -> dict[str, Any]:
        Store().add_appointment(appt)
        return appt.model_dump(mode="json")

    @api.post("/v1/appointments/{appt_id}/complete")
    def complete_appt(appt_id: UUID) -> dict[str, str]:
        Store().complete_appointment(appt_id)
        return {"status": "completed"}

    # --- Handoffs ---
    @api.get("/v1/handoffs")
    def list_handoffs() -> list[dict[str, Any]]:
        return [h.model_dump(mode="json") for h in Store().list_handoffs()]

    @api.post("/v1/handoffs")
    def start_handoff_api(handoff: HandoffLog) -> dict[str, Any]:
        store = Store()
        store.add_handoff(handoff)
        
        # Trigger Telegram/Email notifications
        notifier = NotificationManager(store)
        lang = store.get_setting("default_language", "en")
        notifier.notify_handoff(handoff.caregiver, "start", lang=lang)
        
        return handoff.model_dump(mode="json")

    @api.post("/v1/handoffs/{handoff_id}/end")
    def end_handoff_api(handoff_id: UUID) -> dict[str, str]:
        store = Store()
        handoffs = store.list_handoffs()
        h = next((x for x in handoffs if x.id == handoff_id), None)
        if not h:
            raise HTTPException(status_code=404, detail="Handoff log not found")
        
        h.shift_end = datetime.now(timezone.utc)
        
        store.update_handoff(h)
        
        # Trigger notifications
        notifier = NotificationManager(store)
        lang = store.get_setting("default_language", "en")
        notifier.notify_handoff(h.caregiver, "end", lang=lang)
        
        return {"status": "closed"}

    @api.post("/v1/handoffs/log")
    def log_handoff_api(req: HandoffLogRequest) -> dict[str, str]:
        store = Store()
        handoffs = sorted(store.list_handoffs(), key=lambda x: x.shift_start, reverse=True)
        open_h = next((x for x in handoffs if x.shift_end is None), None)
        if not open_h:
            raise HTTPException(status_code=400, detail="No open handoff shift active")

        if req.vitals:
            open_h.vitals = req.vitals
        if req.mood:
            open_h.mood = req.mood
        if req.meals:
            open_h.meals = req.meals
        if req.notes:
            open_h.notes = (open_h.notes or "") + "\n" + req.notes if open_h.notes else req.notes
        
        if req.incident:
            parts = req.incident.split(":", 2)
            if len(parts) == 3:
                kind, severity, desc = parts
                open_h.incidents.append(Incident(kind=kind, severity=severity, description=desc))  # type: ignore[arg-type]
                
                # Notify careteam about critical incident immediately
                notifier = NotificationManager(store)
                lang = store.get_setting("default_language", "en")
                notifier.notify_incident(kind, severity, desc, lang=lang)

        store.update_handoff(open_h)
        
        return {"status": "logged"}

    # --- Care Plan ---
    @api.get("/v1/careplan")
    def list_careplans() -> list[dict[str, Any]]:
        return [cp.model_dump(mode="json") for cp in Store().list_careplan_versions()]

    @api.post("/v1/careplan")
    def add_careplan(cp: CarePlan) -> dict[str, Any]:
        Store().add_careplan(cp)
        return cp.model_dump(mode="json")

    # --- Settings ---
    @api.get("/v1/settings")
    def get_settings() -> dict[str, str | None]:
        store = Store()
        keys = [
            "telegram_bot_token", "telegram_chat_id", 
            "email_smtp_host", "email_smtp_port", "email_smtp_user", "email_smtp_pass", 
            "email_from", "email_to", "signal_recipient", "signal_sender",
            "ical_urls", "default_language"
        ]
        return {k: store.get_setting(k) for k in keys}

    @api.post("/v1/settings")
    def update_settings(req: SettingUpdate) -> dict[str, str]:
        Store().set_setting(req.key, req.value)
        return {"status": "updated"}

    # --- Caregiver Profiles ---
    @api.get("/v1/profiles")
    def list_profiles() -> list[dict[str, Any]]:
        return Store().list_profiles()

    @api.post("/v1/profiles")
    def add_profile(req: ProfileCreate) -> dict[str, Any]:
        return Store().add_profile(req.name, req.role, req.language, req.pin)

    # --- iCal Calendar Sync ---
    @api.post("/v1/appointments/sync")
    def sync_appointments(req: SyncRequest) -> dict[str, Any]:
        store = Store()
        url = req.url or store.get_setting("ical_urls")
        if not url:
            raise HTTPException(status_code=400, detail="No iCal URL configured or provided")
        
        # Support multiple comma-separated URLs
        urls = [u.strip() for u in url.split(",") if u.strip()]
        total_imported = 0
        for u in urls:
            total_imported += sync_ical_feed(u, store)
            
        return {"status": "success", "imported": total_imported}

    # --- Shift Summarizer ---
    @api.get("/v1/handoffs/{handoff_id}/explain")
    def get_shift_explanation(handoff_id: UUID, lang: str = Query("en")) -> dict[str, str]:
        store = Store()
        handoffs = store.list_handoffs()
        h = next((x for x in handoffs if x.id == handoff_id), None)
        if not h:
            raise HTTPException(status_code=404, detail="Handoff log not found")
        
        summary_md = explain_shift(h, store, lang=lang)
        return {"summary": summary_md}

    # --- Consent Gate approvals ---
    @api.get("/v1/approvals")
    def list_approvals() -> list[dict[str, Any]]:
        return Store().list_pending_approvals()

    @api.post("/v1/approvals/{approval_id}/action")
    def action_approval(approval_id: UUID, req: ApprovalAction) -> dict[str, str]:
        store = Store()
        appr = store.get_approval(approval_id)
        if not appr:
            raise HTTPException(status_code=404, detail="Approval request not found")

        if req.action.lower() == "approve":
            store.set_approval_status(approval_id, "approved")
            
            # Execute the delayed tool action
            tool_name = appr["tool_name"]
            args = appr["arguments"]
            
            # Dynamically perform write
            recipient = store.get_recipient()
            if not recipient:
                raise HTTPException(status_code=400, detail="Recipient not configured")
                
            if tool_name == "add_medication":
                from .models import Medication
                from .services import parse_times
                med = Medication(
                    care_recipient_id=recipient.id,
                    name=args["name"],
                    dose=args["dose"],
                    times=parse_times(args.get("times", "")),
                    instructions=args.get("instructions"),
                    refill_at_days_left=args.get("refill_at", 7)
                )
                store.add_med(med)
            elif tool_name == "deactivate_medication":
                store.deactivate_med(UUID(args["med_id"]))
            elif tool_name == "add_appointment":
                appt = Appointment(
                    care_recipient_id=recipient.id,
                    provider=args["provider"],
                    at=datetime.fromisoformat(args["at"]),
                    purpose=args.get("purpose"),
                    location=args.get("location")
                )
                store.add_appointment(appt)
            elif tool_name == "complete_appointment":
                store.complete_appointment(UUID(args["appt_id"]))
            elif tool_name == "log_incident":
                # Find open handoff
                handoffs = sorted(store.list_handoffs(), key=lambda x: x.shift_start, reverse=True)
                open_h = next((x for x in handoffs if x.shift_end is None), None)
                if open_h:
                    open_h.incidents.append(Incident(
                        kind=args["kind"],
                        severity=args.get("severity", "info"),
                        description=args["description"]
                    ))
                    store.update_handoff(open_h)
                    
                    # Send alert
                    notifier = NotificationManager(store)
                    lang = store.get_setting("default_language", "en")
                    notifier.notify_incident(args["kind"], args.get("severity", "info"), args["description"], lang=lang)
            
            return {"status": "approved"}
        else:
            store.set_approval_status(approval_id, "denied")
            return {"status": "denied"}

    # Mount UI static folder served under the root URL
    static_dir = Path(__file__).parent / "static"
    static_dir.mkdir(parents=True, exist_ok=True)
    api.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")

    return api


def run(host: str = "127.0.0.1", port: int = 7878) -> None:
    import uvicorn
    uvicorn.run(create_app, host=host, port=port, factory=True)
