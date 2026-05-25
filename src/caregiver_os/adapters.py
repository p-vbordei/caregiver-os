"""Channel notification adapters for caregiver-os."""

from __future__ import annotations

import smtplib
import subprocess
import urllib.request
import urllib.parse
from email.mime.text import MIMEText
from typing import Protocol

from .store import Store


class ChannelAdapter(Protocol):
    """Protocol defining a notification channel adapter."""

    name: str

    def announce(self, text: str, store: Store) -> str:
        """Send a notification message. Returns a message ID or status string."""
        ...


class StdoutAdapter:
    name = "stdout"

    def announce(self, text: str, store: Store) -> str:
        print(f"[ANNOUNCEMENT] {text}")
        return "stdout_printed"


class TelegramAdapter:
    name = "telegram"

    def announce(self, text: str, store: Store) -> str:
        token = store.get_setting("telegram_bot_token")
        chat_id = store.get_setting("telegram_chat_id")
        if not token or not chat_id:
            return "telegram_not_configured"

        url = f"https://api.telegram.org/bot{token}/sendMessage"
        data = urllib.parse.urlencode({"chat_id": chat_id, "text": text, "parse_mode": "HTML"}).encode("utf-8")
        
        try:
            req = urllib.request.Request(url, data=data, method="POST")
            with urllib.request.urlopen(req, timeout=5) as response:
                res = response.read().decode("utf-8")
                # Parse to verify success if needed
                return f"telegram_sent_ok: {res[:50]}"
        except Exception as e:
            return f"telegram_failed: {e}"


class EmailAdapter:
    name = "email"

    def announce(self, text: str, store: Store) -> str:
        smtp_host = store.get_setting("email_smtp_host")
        smtp_port_str = store.get_setting("email_smtp_port", "587")
        smtp_user = store.get_setting("email_smtp_user")
        smtp_pass = store.get_setting("email_smtp_pass")
        email_from = store.get_setting("email_from")
        email_to = store.get_setting("email_to")

        if not smtp_host or not email_from or not email_to:
            return "email_not_configured"

        msg = MIMEText(text)
        msg["Subject"] = "Caregiver OS Alert"
        msg["From"] = email_from
        msg["To"] = email_to

        try:
            smtp_port = int(smtp_port_str)
            # Use SSL/TLS appropriately
            if smtp_port == 465:
                server = smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=5)
            else:
                server = smtplib.SMTP(smtp_host, smtp_port, timeout=5)
                server.starttls()

            if smtp_user and smtp_pass:
                server.login(smtp_user, smtp_pass)

            server.send_message(msg)
            server.quit()
            return "email_sent_ok"
        except Exception as e:
            return f"email_failed: {e}"


class SignalAdapter:
    name = "signal"

    def announce(self, text: str, store: Store) -> str:
        recipient = store.get_setting("signal_recipient")
        if not recipient:
            return "signal_not_configured"

        # Signal adapter spawns signal-cli subcommand if available
        # e.g., signal-cli -u +YOURNUMBER send -m "Message" +RECIPIENTNUMBER
        sender = store.get_setting("signal_sender")
        if not sender:
            return "signal_sender_missing"

        try:
            # Safe call executing signal-cli
            subprocess.run(
                ["signal-cli", "-u", sender, "send", "-m", text, recipient],
                check=True,
                capture_output=True,
                text=True,
                timeout=10,
            )
            return "signal_sent_ok"
        except Exception as e:
            return f"signal_failed: {e}"


class NotificationManager:
    """Orchestrates announcements across active adapters."""

    def __init__(self, store: Store | None = None) -> None:
        self.store = store or Store()
        self.adapters: list[ChannelAdapter] = [
            StdoutAdapter(),
            TelegramAdapter(),
            EmailAdapter(),
            SignalAdapter(),
        ]

    def send_announcement(self, text: str, channels: list[str] | None = None) -> dict[str, str]:
        """Announce to selected channels (or all active channels configured in settings)."""
        results = {}
        for adapter in self.adapters:
            # If channels specified, check membership
            if channels is not None:
                if adapter.name in channels:
                    results[adapter.name] = adapter.announce(text, self.store)
            else:
                # Default is stdout + any configured adapter
                if adapter.name == "stdout":
                    results[adapter.name] = adapter.announce(text, self.store)
                elif adapter.name == "telegram" and self.store.get_setting("telegram_bot_token"):
                    results[adapter.name] = adapter.announce(text, self.store)
                elif adapter.name == "email" and self.store.get_setting("email_smtp_host"):
                    results[adapter.name] = adapter.announce(text, self.store)
                elif adapter.name == "signal" and self.store.get_setting("signal_recipient"):
                    results[adapter.name] = adapter.announce(text, self.store)
        return results

    def notify_incident(self, incident_kind: str, severity: str, desc: str, lang: str = "en") -> dict[str, str]:
        """Send urgent notification on new incidents."""
        msg = f"⚠️ <b>[Caregiver OS] {severity.upper()} Incident</b>\nKind: {incident_kind}\nDescription: {desc}"
        if lang == "ro":
            msg = f"⚠️ <b>[Caregiver OS] Incident {severity.upper()}</b>\nTip: {incident_kind}\nDescriere: {desc}"
        return self.send_announcement(msg)

    def notify_handoff(self, caregiver: str, action: str, lang: str = "en") -> dict[str, str]:
        """Notify careteam that a handoff shift started or ended."""
        if action == "start":
            msg = f"🔄 <b>[Caregiver OS] Shift started</b> by {caregiver}."
            if lang == "ro":
                msg = f"🔄 <b>[Caregiver OS] Schimb început</b> de {caregiver}."
        else:
            msg = f"🏁 <b>[Caregiver OS] Shift closed</b> by {caregiver}."
            if lang == "ro":
                msg = f"🏁 <b>[Caregiver OS] Schimb încheiat</b> de {caregiver}."
        return self.send_announcement(msg)
