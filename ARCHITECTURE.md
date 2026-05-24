# Architecture — caregiver-os

## Layers

```
┌────────────────────────────────────────────────────────────┐
│ CLI (Typer)        Web UI (planned)        MCP stdio tools │
├────────────────────────────────────────────────────────────┤
│ FastAPI service                                             │
├────────────────────────────────────────────────────────────┤
│ Domain services: meds, appointments, handoff, careplan,     │
│ announcements, careteam                                     │
├────────────────────────────────────────────────────────────┤
│ Repositories (SQLAlchemy + SQLite)                          │
├────────────────────────────────────────────────────────────┤
│ Channel adapters (Telegram, Signal, WhatsApp, Email)        │
└────────────────────────────────────────────────────────────┘
```

## Core models (Pydantic)

```python
class CareRecipient(BaseModel):
    id: UUID
    name: str
    age: int | None
    notes: str | None
    created_at: datetime

class Medication(BaseModel):
    id: UUID
    care_recipient_id: UUID
    name: str
    dose: str                  # "1 tablet", "10 ml"
    times: list[time]          # e.g. [09:00, 21:00]
    instructions: str | None
    refill_at_days_left: int   # e.g. alert when 7 days left
    active: bool

class Appointment(BaseModel):
    id: UUID
    care_recipient_id: UUID
    provider: str              # "Dr. Smith — Cardiology"
    at: datetime
    location: str | None
    purpose: str | None
    completed: bool

class HandoffLog(BaseModel):
    id: UUID
    care_recipient_id: UUID
    shift_start: datetime
    shift_end: datetime | None
    caregiver: str             # name or email
    vitals: str | None
    mood: str | None
    meals: str | None
    medications_given: list[UUID]
    incidents: list[Incident]
    notes: str | None

class Incident(BaseModel):
    kind: Literal["fall", "confusion", "missed_meal", "medication_refusal", "other"]
    at: datetime
    description: str
    severity: Literal["info", "warning", "alert"]

class CarePlan(BaseModel):
    id: UUID
    care_recipient_id: UUID
    version: int
    markdown: str
    updated_at: datetime
    updated_by: str
```

## Storage

SQLite at `~/.caregiver-os/store.sqlite` via SQLAlchemy. One database per install. Schema versioned with Alembic (planned).

## CLI design

Typer-based, subcommand-per-domain:

```
caregiver-os meds add|list|done|skip
caregiver-os appointments add|list|done|upcoming
caregiver-os handoff start|end|log|today|history
caregiver-os careplan show|edit|history
caregiver-os announce --to telegram:family "Mom took morning meds"
caregiver-os today              # one-screen summary
caregiver-os explain-since 6h   # uses explain-since adapter
```

## FastAPI service

Endpoints under `/v1/`:

- `GET /recipient` / `PUT /recipient`
- `GET /meds` / `POST /meds` / `POST /meds/{id}/given`
- `GET /appointments` / `POST /appointments`
- `GET /handoffs` / `POST /handoffs`
- `GET /careplan` / `POST /careplan`
- `POST /announce` (with channel + message)
- `GET /today`

CORS off by default; binds to `127.0.0.1` only unless explicitly configured.

## MCP stdio wrapper

A small companion process exposes the above as MCP tools. Each tool:

- Declares its scope in the manifest ([mcp-provenance](../mcp-provenance/) compatible).
- Requires the operator's consent token for write operations.
- Emits an action receipt via [agent-attestation](../agent-attestation/).

## Channel adapters

```python
class ChannelAdapter(Protocol):
    name: str
    async def announce(self, to: str, text: str) -> str: ...   # returns message id
```

Adapters for Telegram (`grammy`-like), Signal (`signal-cli`), WhatsApp Business Cloud, Email (SMTP). The default install ships only a `stdout` adapter.

## Privacy & consent

- Local-first; nothing leaves the box without an opt-in adapter.
- Each adapter declares whom it tells what — `to: "telegram:family"` is an explicit choice, not a default.
- All writes from the MCP endpoint require a consent token from the caregiver (issued via CLI: `caregiver-os tokens issue`).
- Audit log via [agent-attestation](../agent-attestation/) preserves who/what/when.

## Non-goals

- Not an EHR replacement.
- Not a billing/insurance system.
- Not a clinical-decision tool.
- Not HIPAA-certified out of the box.
