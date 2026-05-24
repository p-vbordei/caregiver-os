"""Typer-based CLI for caregiver-os."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

import typer

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
app.add_typer(meds_app, name="meds")
app.add_typer(appts_app, name="appointments")
app.add_typer(handoff_app, name="handoff")


def _store() -> Store:
    return Store()


@app.command()
def init(care_recipient: str = typer.Option(..., "--care-recipient")) -> None:
    """Initialize the local store with a care recipient."""
    r = init_recipient(_store(), care_recipient)
    typer.echo(f"Initialized: {r.name} ({r.id})")


@app.command()
def today() -> None:
    """One-screen summary of today's care state."""
    s = today_summary(_store())
    typer.echo(f"Recipient: {s.recipient.name}")
    typer.echo(f"Medications due today: {len(s.medications_due)}")
    for m in s.medications_due:
        typer.echo(f"  - {m.name} ({m.dose}) @ {','.join(str(t) for t in m.times)}")
    typer.echo(f"Upcoming appointments (48h): {len(s.upcoming_appointments)}")
    for a in s.upcoming_appointments:
        typer.echo(f"  - {a.at:%Y-%m-%d %H:%M} {a.provider} — {a.purpose or ''}")
    typer.echo(f"Open handoff: {'yes' if s.open_handoff else 'no'}")
    typer.echo(f"Recent incidents: {len(s.recent_incidents)}")
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
    typer.echo(f"Added: {m.name} ({m.id})")


@meds_app.command("list")
def meds_list() -> None:
    for m in _store().list_meds():
        marker = "" if m.active else " (inactive)"
        typer.echo(f"{m.id} {m.name} {m.dose} {','.join(str(t) for t in m.times)}{marker}")


@meds_app.command("done")
def meds_done(med_id: UUID = typer.Argument(...)) -> None:
    _store().deactivate_med(med_id)
    typer.echo(f"Deactivated {med_id}")


# Appointments

@appts_app.command("add")
def appts_add(
    provider: str = typer.Option(..., "--provider"),
    at: str = typer.Option(..., "--at", help="ISO 8601 datetime"),
    purpose: str | None = typer.Option(None, "--purpose"),
    location: str | None = typer.Option(None, "--location"),
) -> None:
    store = _store()
    r = require_recipient(store)
    a = Appointment(
        care_recipient_id=r.id,
        provider=provider,
        at=datetime.fromisoformat(at),
        purpose=purpose,
        location=location,
    )
    store.add_appointment(a)
    typer.echo(f"Added: {a.provider} @ {a.at:%Y-%m-%d %H:%M} ({a.id})")


@appts_app.command("list")
def appts_list() -> None:
    for a in _store().list_appointments():
        done = " (done)" if a.completed else ""
        typer.echo(f"{a.id} {a.at:%Y-%m-%d %H:%M} {a.provider}{done}")


# Handoff

@handoff_app.command("start")
def handoff_start(caregiver: str = typer.Option(..., "--caregiver")) -> None:
    h = start_handoff(_store(), caregiver)
    typer.echo(f"Started handoff: {h.id}")


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
    handoffs = sorted(store.list_handoffs(), key=lambda h: h.shift_start, reverse=True)
    open_h = next((h for h in handoffs if h.shift_end is None), None)
    if not open_h:
        typer.echo("No open handoff. Run: caregiver-os handoff start --caregiver <name>")
        raise typer.Exit(code=1)
    if vitals: open_h.vitals = vitals
    if mood: open_h.mood = mood
    if meals: open_h.meals = meals
    if notes: open_h.notes = (open_h.notes or "") + "\n" + notes if open_h.notes else notes
    if incident:
        parts = incident.split(":", 2)
        if len(parts) != 3:
            typer.echo('Incident must be "kind:severity:description"')
            raise typer.Exit(code=1)
        kind, severity, desc = parts
        open_h.incidents.append(Incident(kind=kind, severity=severity, description=desc))  # type: ignore[arg-type]
    # Re-write the handoffs list with the update
    all_h = store.list_handoffs()
    all_h = [open_h if h.id == open_h.id else h for h in all_h]
    store._write("handoffs", [h.model_dump(mode="json") for h in all_h])  # noqa: SLF001
    typer.echo("Logged.")


@handoff_app.command("end")
def handoff_end() -> None:
    store = _store()
    handoffs = sorted(store.list_handoffs(), key=lambda h: h.shift_start, reverse=True)
    open_h = next((h for h in handoffs if h.shift_end is None), None)
    if not open_h:
        typer.echo("No open handoff.")
        raise typer.Exit(code=1)
    open_h.shift_end = datetime.now()
    all_h = store.list_handoffs()
    all_h = [open_h if h.id == open_h.id else h for h in all_h]
    store._write("handoffs", [h.model_dump(mode="json") for h in all_h])  # noqa: SLF001
    typer.echo("Closed handoff.")


@app.command()
def serve(port: int = typer.Option(7878, "--port"), host: str = typer.Option("127.0.0.1", "--host")) -> None:
    """Start the FastAPI service (loads lazily to avoid import cost on every CLI call)."""
    from .http import run
    run(host=host, port=port)


if __name__ == "__main__":
    app()
