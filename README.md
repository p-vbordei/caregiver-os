# caregiver-os

> An open-source coordination OS for caregivers of an aging parent, a disabled family member, or anyone needing distributed care.

## Problem

The ACL (US Administration for Community Living) **Caregiver Artificial Intelligence Prize Challenge** ([acl.gov](https://acl.gov/caregiver-ai-competition)) exists because the gap is real. Family caregivers manage:

- Medication schedules across multiple drugs, dosages, frequencies
- Doctor/therapy appointments with cross-referenced symptoms
- Multi-person shift handoff (night care → day care → spouse)
- EHR portal access (manual, fragmented, hostile UX)
- Insurance / billing reconciliation
- Family-channel updates ("Mom ate breakfast", "Dad fell at 2am")

The closed commercial space is dominated by enterprise home-care SaaS (AlayaCare, AxisCare, Alora). There is **no usable open-source family-scale coordinator** as of mid-2026. The privacy-first variant is especially missing.

## Why doesn't this already exist

- HIPAA / health-data complexity makes open-source contributors nervous.
- The product is unsexy compared to the AI-coding-agent wave.
- The user pool (family caregivers) under-represented in OSS communities.
- Vertical SaaS captures the willingness-to-pay first.

## What this is

A Python + FastAPI service plus a CLI that runs locally (or on a home server / Raspberry Pi):

1. **Medication tracker** — schedules, doses, reminders, missed-dose alerts, refill window.
2. **Appointment manager** — read iCal feeds; consolidate; remind.
3. **Shift handoff log** — append-only daily log with structured "vital signs", "mood", "meals", "incidents".
4. **Family announcement bus** — pluggable channel adapters (Telegram, Signal, WhatsApp, email) for sending updates.
5. **Care plan documents** — Markdown-stored care plan with versions.
6. **Agent endpoint** — exposes the above as an MCP server so a personal AI assistant (Claude Desktop, Cursor, or any MCP client) can read/write on the caregiver's behalf with proper consent gates.

## Quick start

```bash
uv venv
uv pip install -e .

# initialise local store at ~/.caregiver-os
caregiver-os init --care-recipient "Mom (Maria, 78)"

# add a medication
caregiver-os meds add --name "Atorvastatin 20mg" --dose 1 --times 09:00 --refill-at 7

# log a handoff
caregiver-os handoff log \
  --date today \
  --vitals "BP 132/84, pulse 76" \
  --mood "alert" \
  --meals "breakfast yes, lunch half" \
  --notes "asked about Dad twice"

# show today
caregiver-os today

# start the local server (FastAPI + MCP)
caregiver-os serve --port 7878
```

## MVP scope

- [x] Local SQLite store at `~/.caregiver-os/store.sqlite`
- [x] Pydantic models for medications, appointments, handoff logs, care plans
- [x] CLI for the above
- [x] FastAPI HTTP service with read/write endpoints
- [x] MCP-style stdio tools wrapper (alpha)
- [x] Unit tests on the core models
- [ ] Channel adapters (Telegram, Signal, WhatsApp) for announcements
- [ ] iCal subscription for appointments
- [ ] EHR portal scraper (per-provider plugin model)
- [ ] Web UI for non-CLI caregivers
- [ ] Multi-caregiver auth + role separation
- [ ] Consent gates so the AI agent must ask before writes

## Why caregiver-shaped vs. patient-shaped

This product is built for *the caregiver*, not the patient. The patient is often unable to use software directly. The caregiver is the user, the data subject is the patient, and consent flows respect that distinction.

## Privacy

- **Local-first**: data lives on the caregiver's machine by default. Cloud sync is opt-in and per-collection (e.g., medication list can sync; handoff notes might not).
- **Per-caregiver auth** when multiple people share the install — viewer / writer / admin roles.
- **Audit log** of every read/write via [agent-attestation](../agent-attestation/) receipts when used as an agent endpoint.
- **HIPAA stance**: this is a personal-use tool, not a covered-entity HIS — but we document a hardening path for those who need it.

## Roadmap

| Milestone | What |
|---|---|
| v0.1 | Core models, CLI, FastAPI service, MCP stdio wrapper |
| v0.2 | Telegram + Signal announcement adapters |
| v0.3 | iCal appointment subscription + EHR scraper framework |
| v0.4 | Multi-caregiver auth + Web UI |
| v0.5 | LLM-summary "explain since last shift" via [explain-since](../explain-since/) |

## References

- Research paper §8.2, §10.2 #20
- [ACL Caregiver AI Prize Challenge](https://acl.gov/caregiver-ai-competition)
- [How AI Can Become a Caregivers New Ally — AARP](https://www.aarp.org/caregiving/basics/how-ai-can-help-caregivers/)

## License

Apache-2.0 © Vlad Bordei
