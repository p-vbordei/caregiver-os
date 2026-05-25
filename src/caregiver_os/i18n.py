"""Internationalization / Translation helper for caregiver-os."""

from __future__ import annotations

import os

TRANSLATIONS = {
    "en": {
        "no_recipient": "No care recipient configured. Run: caregiver-os init --care-recipient '<name>'",
        "initialized": "Initialized: {name} ({id})",
        "med_added": "Added: {name} ({id})",
        "med_deactivated": "Deactivated {id}",
        "appt_added": "Added: {provider} @ {at} ({id})",
        "handoff_started": "Started handoff: {id}",
        "no_open_handoff": "No open handoff. Run: caregiver-os handoff start --caregiver <name>",
        "logged": "Logged.",
        "handoff_closed": "Closed handoff.",
        "today_recipient": "Recipient: {name}",
        "today_meds": "Medications due today: {count}",
        "today_appts": "Upcoming appointments (48h): {count}",
        "today_open_handoff": "Open handoff: {status}",
        "today_incidents": "Recent incidents: {count}",
        "yes": "yes",
        "no": "no",
        "incident_invalid": "Incident must be 'kind:severity:description'",
        "summary_title": "Shift Summary for {recipient}",
        "summary_since": "Since {since}",
        "summary_no_active": "No active shift handoff found.",
        "summary_meds_taken": "Medications Taken",
        "summary_meds_taken_none": "No medications logged as taken during this shift.",
        "summary_vitals": "Vitals Logged",
        "summary_vitals_none": "No vitals recorded.",
        "summary_mood": "Mood",
        "summary_meals": "Meals",
        "summary_meals_none": "No meal logs recorded.",
        "summary_incidents": "Incidents Logged ({count})",
        "summary_incidents_none": "No incidents reported during this shift.",
        "summary_notes": "General Notes",
        "summary_notes_none": "No additional notes.",
        "approval_required": "AI write operation requires consent. Approval ID: {id}",
        "approval_approved": "Approval {id} approved.",
        "approval_denied": "Approval {id} denied.",
        "approval_not_found": "Approval {id} not found.",
        "sync_completed": "Calendar sync completed. Imported {count} appointments.",
    },
    "ro": {
        "no_recipient": "Niciun beneficiar de îngrijire configurat. Rulați: caregiver-os init --care-recipient '<nume>'",
        "initialized": "Inițializat: {name} ({id})",
        "med_added": "Adăugat: {name} ({id})",
        "med_deactivated": "Dezactivat {id}",
        "appt_added": "Adăugat: {provider} @ {at} ({id})",
        "handoff_started": "S-a început schimbul: {id}",
        "no_open_handoff": "Nu există niciun schimb deschis. Rulați: caregiver-os handoff start --caregiver <nume>",
        "logged": "Înregistrat.",
        "handoff_closed": "Schimb închis.",
        "today_recipient": "Beneficiar: {name}",
        "today_meds": "Medicamente programate azi: {count}",
        "today_appts": "Următoarele programări (48h): {count}",
        "today_open_handoff": "Schimb deschis: {status}",
        "today_incidents": "Incidente recente: {count}",
        "yes": "da",
        "no": "nu",
        "incident_invalid": "Incidentul trebuie să fie în formatul 'tip:severitate:descriere'",
        "summary_title": "Sumarul schimbului pentru {recipient}",
        "summary_since": "De la {since}",
        "summary_no_active": "Nu s-a găsit niciun schimb activ.",
        "summary_meds_taken": "Medicamente administrate",
        "summary_meds_taken_none": "Nu s-au înregistrat medicamente administrate în acest schimb.",
        "summary_vitals": "Funcții vitale înregistrate",
        "summary_vitals_none": "Nu s-au înregistrat funcții vitale.",
        "summary_mood": "Stare de spirit",
        "summary_meals": "Mese",
        "summary_meals_none": "Nu s-au înregistrat detalii despre mese.",
        "summary_incidents": "Incidente înregistrate ({count})",
        "summary_incidents_none": "Nu s-au raportat incidente în acest schimb.",
        "summary_notes": "Note generale",
        "summary_notes_none": "Nu există note suplimentare.",
        "approval_required": "Operațiunea de scriere AI necesită consimțământ. ID Aprobare: {id}",
        "approval_approved": "Aprobarea {id} a fost acceptată.",
        "approval_denied": "Aprobarea {id} a fost respinsă.",
        "approval_not_found": "Aprobarea {id} nu a fost găsită.",
        "sync_completed": "Sincronizarea calendarului a fost finalizată. S-au importat {count} programări.",
    }
}


def get_lang() -> str:
    """Detect language preference from environment variable, defaulting to 'en'."""
    lang = os.environ.get("CAREGIVER_LANG", "en").lower()
    return lang if lang in TRANSLATIONS else "en"


def t(key: str, lang: str | None = None, **kwargs) -> str:
    """Translate a key into the target language, formatting with kwargs."""
    if not lang:
        lang = get_lang()
    lang_dict = TRANSLATIONS.get(lang, TRANSLATIONS["en"])
    template = lang_dict.get(key, TRANSLATIONS["en"].get(key, key))
    return template.format(**kwargs)
