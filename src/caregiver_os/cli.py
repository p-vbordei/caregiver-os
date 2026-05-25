"""Typer-based CLI for caregiver-os with EN/RO bilingual support and new subcommands."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

import typer

from .i18n import t
from .models import Appointment, Incident, Medication
from .services import (
    init_recipient,
    parse_times,
    require_recipient,
    start_handoff,
    today_summary,
)
from .store import Store

app = typer.Typer(no_args_is_help=True, add_completion=False)
meds_app = typer.Typer(no_args_is_help=True)
appts_app = typer.Typer(no_args_is_help=True)
handoff_app = typer.Typer(no_args_is_help=True)
approvals_app = typer.Typer(no_args_is_help=True)

app.add_typer(meds_app, name="meds")
app.add_typer(appts_app, name="appointments")
app.add_typer(handoff_app, name="handoff")
app.add_typer(approvals_app, name="approvals")


def _store() -> Store:
    return Store()


def _get_lang(store: Store) -> str:
    """Helper to detect language setting in DB or fallback to environment/default."""
    return store.get_setting("default_language", "en")


@app.command()
def init(care_recipient: str = typer.Option(..., "--care-recipient")) -> None:
    """Initialize the local store with a care recipient."""
    store = _store()
    lang = _get_lang(store)
    r = init_recipient(store, care_recipient)
    typer.echo(t("initialized", lang, name=r.name, id=str(r.id)))


@app.command()
def today() -> None:
    """One-screen summary of today's care state."""
    store = _store()
    lang = _get_lang(store)
    
    try:
        s = today_summary(store)
    except RuntimeError:
        typer.echo(t("no_recipient", lang))
        raise typer.Exit(code=1)
        
    typer.echo(t("today_recipient", lang, name=s.recipient.name))
    typer.echo(t("today_meds", lang, count=len(s.medications_due)))
    for m in s.medications_due:
        typer.echo(f"  - {m.name} ({m.dose}) @ {','.join(str(t_val) for t_val in m.times)}")
        
    typer.echo(t("today_appts", lang, count=len(s.upcoming_appointments)))
    for a in s.upcoming_appointments:
        typer.echo(f"  - {a.at:%Y-%m-%d %H:%M} {a.provider} — {a.purpose or ''}")
        
    status_str = t("yes", lang) if s.open_handoff else t("no", lang)
    typer.echo(t("today_open_handoff", lang, status=status_str))
    
    typer.echo(t("today_incidents", lang, count=len(s.recent_incidents)))
    for inc in s.recent_incidents:
        typer.echo(f"  - [{inc.severity}] {inc.kind} @ {inc.at:%H:%M}: {inc.description}")


# Medications

@meds_app.command("add")
def meds_add(
    name: str = typer.Option(..., "--name"),
    dose: str = typer.Option(..., "--dose"),
    times: str = typer.Option("", "--times", help="comma-separated HH:MM e.g. 09:00,21:00"),
    instructions: str | None = typer.Option(None, "--instructions"),
    refill_at: int = typer.Option(7, "--refill-at"),
) -> None:
    """Add a medication."""
    store = _store()
    lang = _get_lang(store)
    r = require_recipient(store)
    m = Medication(
        care_recipient_id=r.id,
        name=name,
        dose=dose,
        times=parse_times(times) if times else [],
        instructions=instructions,
        refill_at_days_left=refill_at,
    )
    store.add_med(m)
    typer.echo(t("med_added", lang, name=m.name, id=str(m.id)))


@meds_app.command("list")
def meds_list() -> None:
    for m in _store().list_meds():
        marker = "" if m.active else " (inactive)"
        typer.echo(f"{m.id} {m.name} {m.dose} {','.join(str(t_val) for t_val in m.times)}{marker}")


@meds_app.command("done")
def meds_done(med_id: UUID = typer.Argument(...)) -> None:
    store = _store()
    lang = _get_lang(store)
    store.deactivate_med(med_id)
    typer.echo(t("med_deactivated", lang, id=str(med_id)))


# Appointments

@appts_app.command("add")
def appts_add(
    provider: str = typer.Option(..., "--provider"),
    at: str = typer.Option(..., "--at", help="ISO 8601 datetime"),
    purpose: str | None = typer.Option(None, "--purpose"),
    location: str | None = typer.Option(None, "--location"),
) -> None:
    store = _store()
    lang = _get_lang(store)
    r = require_recipient(store)
    a = Appointment(
        care_recipient_id=r.id,
        provider=provider,
        at=datetime.fromisoformat(at),
        purpose=purpose,
        location=location,
    )
    store.add_appointment(a)
    typer.echo(t("appt_added", lang, provider=a.provider, at=f"{a.at:%Y-%m-%d %H:%M}", id=str(a.id)))


@appts_app.command("list")
def appts_list() -> None:
    for a in _store().list_appointments():
        done = " (done)" if a.completed else ""
        typer.echo(f"{a.id} {a.at:%Y-%m-%d %H:%M} {a.provider}{done}")


@appts_app.command("sync")
def appts_sync(url: str | None = typer.Option(None, "--url", help="iCal Feed URL override")) -> None:
    """Synchronize clinical appointments from configured iCal feed."""
    store = _store()
    lang = _get_lang(store)
    feed_url = url or store.get_setting("ical_urls")
    if not feed_url:
        typer.echo("Error: No iCal URLs configured. Set in Web UI or pass --url parameter.")
        raise typer.Exit(code=1)
        
    urls = [u.strip() for u in feed_url.split(",") if u.strip()]
    total_imported = 0
    from .ical import sync_ical_feed
    for u in urls:
        total_imported += sync_ical_feed(u, store)
        
    typer.echo(t("sync_completed", lang, count=total_imported))


# Handoff

@handoff_app.command("start")
def handoff_start(caregiver: str = typer.Option(..., "--caregiver")) -> None:
    store = _store()
    lang = _get_lang(store)
    h = start_handoff(store, caregiver)
    
    # Notify team
    from .adapters import NotificationManager
    NotificationManager(store).notify_handoff(caregiver, "start", lang=lang)
    
    typer.echo(t("handoff_started", lang, id=str(h.id)))


@handoff_app.command("log")
def handoff_log(
    vitals: str | None = typer.Option(None, "--vitals"),
    mood: str | None = typer.Option(None, "--mood"),
    meals: str | None = typer.Option(None, "--meals"),
    notes: str | None = typer.Option(None, "--notes"),
    incident: str | None = typer.Option(None, "--incident", help='Format: "kind:severity:description"'),
) -> None:
    """Update the open handoff with a quick log entry."""
    store = _store()
    lang = _get_lang(store)
    handoffs = sorted(store.list_handoffs(), key=lambda h: h.shift_start, reverse=True)
    open_h = next((h for h in handoffs if h.shift_end is None), None)
    if not open_h:
        typer.echo(t("no_open_handoff", lang))
        raise typer.Exit(code=1)
        
    if vitals:
        open_h.vitals = vitals
    if mood:
        open_h.mood = mood
    if meals:
        open_h.meals = meals
    if notes:
        open_h.notes = (open_h.notes or "") + "\n" + notes if open_h.notes else notes
    if incident:
        parts = incident.split(":", 2)
        if len(parts) != 3:
            typer.echo(t("incident_invalid", lang))
            raise typer.Exit(code=1)
        kind, severity, desc = parts
        open_h.incidents.append(Incident(kind=kind, severity=severity, description=desc))  # type: ignore[arg-type]
        
        # Trigger notifications
        from .adapters import NotificationManager
        NotificationManager(store).notify_incident(kind, severity, desc, lang=lang)
        
    store.update_handoff(open_h)
    typer.echo(t("logged", lang))


@handoff_app.command("end")
def handoff_end() -> None:
    store = _store()
    lang = _get_lang(store)
    handoffs = sorted(store.list_handoffs(), key=lambda h: h.shift_start, reverse=True)
    open_h = next((h for h in handoffs if h.shift_end is None), None)
    if not open_h:
        typer.echo("No open handoff.")
        raise typer.Exit(code=1)
        
    open_h.shift_end = datetime.now(timezone.utc)
    store.update_handoff(open_h)
    
    # Notify team
    from .adapters import NotificationManager
    NotificationManager(store).notify_handoff(open_h.caregiver, "end", lang=lang)
    
    typer.echo(t("handoff_closed", lang))


@handoff_app.command("summarize")
def handoff_summarize(handoff_id: UUID = typer.Argument(...)) -> None:
    """Generate and print an AI/Local summary for a specific handoff shift."""
    store = _store()
    lang = _get_lang(store)
    handoffs = store.list_handoffs()
    h = next((x for x in handoffs if x.id == handoff_id), None)
    if not h:
        typer.echo(f"Error: Handoff {handoff_id} not found.")
        raise typer.Exit(code=1)
        
    from .ai import explain_shift
    summary = explain_shift(h, store, lang=lang)
    typer.echo(summary)


# AI Approvals (Consent Gate)

@approvals_app.command("list")
def approvals_list() -> None:
    """List pending AI agent write operations awaiting consent."""
    store = _store()
    pending = store.list_pending_approvals()
    if not pending:
        typer.echo("No pending approvals.")
        return
        
    for a in pending:
        typer.echo(f"ID: {a['id']}")
        typer.echo(f"  Tool: {a['tool_name']}")
        typer.echo(f"  Args: {a['arguments']}")
        typer.echo(f"  Time: {a['created_at']}")
        typer.echo("-" * 40)


@approvals_app.command("approve")
def approvals_approve(approval_id: UUID = typer.Argument(...)) -> None:
    """Authorize a pending AI write action."""
    store = _store()
    lang = _get_lang(store)
    
    # Fetch and check approval
    appr = store.get_approval(approval_id)
    if not appr:
        typer.echo(t("approval_not_found", lang, id=str(approval_id)))
        raise typer.Exit(code=1)
        
    # Execute action via http logic simulate
    try:
        # Direct call to the API function
        # Using dependency mock execution
        store.set_approval_status(approval_id, "approved")
        
        # Execute delayed logic
        tool_name = appr["tool_name"]
        args = appr["arguments"]
        recipient = store.get_recipient()
        if not recipient:
            typer.echo("Recipient not configured.")
            raise typer.Exit(code=1)
            
        if tool_name == "add_medication":
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
            handoffs = sorted(store.list_handoffs(), key=lambda x: x.shift_start, reverse=True)
            open_h = next((x for x in handoffs if x.shift_end is None), None)
            if open_h:
                open_h.incidents.append(Incident(
                    kind=args["kind"],
                    severity=args.get("severity", "info"),
                    description=args["description"]
                ))
                store.update_handoff(open_h)
                
                # Notify
                from .adapters import NotificationManager
                NotificationManager(store).notify_incident(args["kind"], args.get("severity", "info"), args["description"], lang=lang)
                
        typer.echo(t("approval_approved", lang, id=str(approval_id)))
    except Exception as e:
        typer.echo(f"Error executing approval: {e}")
        raise typer.Exit(code=1)


@approvals_app.command("deny")
def approvals_deny(approval_id: UUID = typer.Argument(...)) -> None:
    """Reject a pending AI write action."""
    store = _store()
    lang = _get_lang(store)
    appr = store.get_approval(approval_id)
    if not appr:
        typer.echo(t("approval_not_found", lang, id=str(approval_id)))
        raise typer.Exit(code=1)
        
    store.set_approval_status(approval_id, "denied")
    typer.echo(t("approval_denied", lang, id=str(approval_id)))


# Stdio MCP Server wrapper subcommand

@app.command()
def mcp() -> None:
    """Start the stdio-based MCP JSON-RPC Server Wrapper."""
    from .mcp import run_mcp_server
    run_mcp_server()


# Service Start

@app.command()
def serve(port: int = typer.Option(7878, "--port"), host: str = typer.Option("127.0.0.1", "--host")) -> None:
    """Start the FastAPI service side-by-side with the Web UI."""
    from .http import run
    run(host=host, port=port)


if __name__ == "__main__":
    app()
