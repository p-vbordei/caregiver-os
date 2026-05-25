"""LLM-based Caregiver Shift Explainer utilizing Google Gemini API."""

from __future__ import annotations

import json
import os
import urllib.request

from .i18n import t
from .models import HandoffLog
from .store import Store


def generate_gemini_summary(prompt: str, api_key: str) -> str | None:
    """Send a direct HTTP request to the Google Gemini API to generate content."""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}
    body = {
        "contents": [
            {
                "parts": [
                    {"text": prompt}
                ]
            }
        ]
    }

    try:
        data = json.dumps(body).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=15) as response:
            res_json = json.loads(response.read().decode("utf-8"))
            # Extract text content from candidate response
            candidates = res_json.get("candidates", [])
            if candidates:
                parts = candidates[0].get("content", {}).get("parts", [])
                if parts:
                    return parts[0].get("text")
    except Exception as e:
        print(f"Gemini API request failed: {e}")
    return None


def explain_shift(handoff: HandoffLog, store: Store, lang: str = "en") -> str:
    """Generate a clean, structured shift summary in English or Romanian."""
    recipient = store.get_recipient()
    recipient_name = recipient.name if recipient else "Care Recipient"

    # Gather medications details
    meds_dict = {m.id: m for m in store.list_meds()}
    meds_given_names = []
    for m_id in handoff.medications_given:
        if m_id in meds_dict:
            m = meds_dict[m_id]
            meds_given_names.append(f"{m.name} ({m.dose})")
        else:
            meds_given_names.append(str(m_id))

    # Construct clean text representation of the handoff data
    start_str = handoff.shift_start.strftime("%Y-%m-%d %H:%M")
    end_str = handoff.shift_end.strftime("%Y-%m-%d %H:%M") if handoff.shift_end else t("yes", lang).upper()

    vitals = handoff.vitals or t("summary_vitals_none", lang)
    mood = handoff.mood or t("no", lang)
    meals = handoff.meals or t("summary_meals_none", lang)
    notes = handoff.notes or t("summary_notes_none", lang)

    meds_str = ", ".join(meds_given_names) if meds_given_names else t("summary_meds_taken_none", lang)

    incidents_list = []
    for inc in handoff.incidents:
        inc_time = inc.at.strftime("%H:%M")
        inc_str = f"- [{inc.severity.upper()}] {inc.kind} @ {inc_time}: {inc.description}"
        incidents_list.append(inc_str)
    incidents_str = "\n".join(incidents_list) if incidents_list else t("summary_incidents_none", lang)

    # Check for Gemini API key
    api_key = os.environ.get("GEMINI_API_KEY")
    if api_key:
        # Prompt definition
        prompt_en = f"""
You are an expert caregiver coordination AI. Summarize the following shift handoff log for the care recipient "{recipient_name}".
Provide a warm, reassuring, and highly professional summary in English.
Highlight any critical incidents, vitals, mood, meals, and medication adherence. Use Markdown formatting.

Shift Details:
- Caregiver: {handoff.caregiver}
- Started: {start_str}
- Ended: {end_str}
- Vitals: {vitals}
- Mood: {mood}
- Meals: {meals}
- Medications Given: {meds_str}
- Incidents:
{incidents_str}
- Caregiver Notes: {notes}
"""

        prompt_ro = f"""
Ești un asistent AI expert în coordonarea îngrijirii. Rezumă următorul jurnal de schimb de tură pentru beneficiarul "{recipient_name}".
Oferă un rezumat călduros, liniștitor și foarte profesionist în Limba Română.
Evidențiază incidentele critice, funcțiile vitale, starea de spirit, mesele și aderența la medicamente. Utilizează formatarea Markdown.

Detalii schimb:
- Îngrijitor: {handoff.caregiver}
- Început: {start_str}
- Sfârșit: {end_str}
- Funcții vitale: {vitals}
- Stare de spirit: {mood}
- Mese: {meals}
- Medicamente administrate: {meds_str}
- Incidente:
{incidents_str}
- Note îngrijitor: {notes}
"""
        prompt = prompt_ro if lang == "ro" else prompt_en
        summary = generate_gemini_summary(prompt, api_key)
        if summary:
            return summary.strip()

    # Fallback to local structured summary (English or Romanian)
    if lang == "ro":
        summary_lines = [
            f"# {t('summary_title', lang, recipient=recipient_name)}",
            f"**Îngrijitor:** {handoff.caregiver}",
            f"**Interval:** {start_str} ➔ {end_str}",
            "",
            f"### 💊 {t('summary_meds_taken', lang)}",
            f"{meds_str}",
            "",
            f"### 💓 {t('summary_vitals', lang)}",
            f"{vitals}",
            "",
            f"### 😊 {t('summary_mood', lang)}",
            f"{mood}",
            "",
            f"### 🍎 {t('summary_meals', lang)}",
            f"{meals}",
            "",
            f"### ⚠️ {t('summary_incidents', lang, count=len(handoff.incidents))}",
            f"{incidents_str}",
            "",
            f"### 📝 {t('summary_notes', lang)}",
            f"{notes}",
        ]
    else:
        summary_lines = [
            f"# {t('summary_title', lang, recipient=recipient_name)}",
            f"**Caregiver:** {handoff.caregiver}",
            f"**Interval:** {start_str} ➔ {end_str}",
            "",
            f"### 💊 {t('summary_meds_taken', lang)}",
            f"{meds_str}",
            "",
            f"### 💓 {t('summary_vitals', lang)}",
            f"{vitals}",
            "",
            f"### 😊 {t('summary_mood', lang)}",
            f"{mood}",
            "",
            f"### 🍎 {t('summary_meals', lang)}",
            f"{meals}",
            "",
            f"### ⚠️ {t('summary_incidents', lang, count=len(handoff.incidents))}",
            f"{incidents_str}",
            "",
            f"### 📝 {t('summary_notes', lang)}",
            f"{notes}",
        ]
        
    return "\n".join(summary_lines)
