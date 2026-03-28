import os
import smtplib
import logging
from email.mime.text import MIMEText
from typing import Dict, Any

from utils import env_bool

logger = logging.getLogger("alert_service")


class AlertService:
    def __init__(self):
        self.mode = os.getenv("ALERT_MODE", "console").lower()  # console|smtp|twilio
        self.smtp_enabled = self.mode == "smtp"
        self.twilio_enabled = self.mode == "twilio"

    def send_alert(self, incident: Dict[str, Any]):
        if not incident.get("fire_detected"):
            return

        message = (
            f"🔥 Fire detected! Severity: {incident.get('severity', 'Unknown')} | "
            f"Location: {incident.get('location', {})} | "
            f"Confidence: {incident.get('confidence', 0)} | Take immediate action."
        )

        if self.mode == "smtp":
            self._send_email(message)
        elif self.mode == "twilio":
            self._send_twilio(message)
        else:
            logger.warning(f"[ALERT-CONSOLE] {message}")

    def _send_email(self, message: str):
        host = os.getenv("SMTP_HOST")
        port = int(os.getenv("SMTP_PORT", "587"))
        user = os.getenv("SMTP_USER")
        pwd = os.getenv("SMTP_PASS")
        to_email = os.getenv("ALERT_TO_EMAIL")
        from_email = os.getenv("ALERT_FROM_EMAIL", user)

        if not all([host, user, pwd, to_email]):
            logger.error("SMTP config missing. Falling back to console.")
            logger.warning(f"[ALERT-CONSOLE] {message}")
            return

        msg = MIMEText(message)
        msg["Subject"] = "Wildfire Alert"
        msg["From"] = from_email
        msg["To"] = to_email

        with smtplib.SMTP(host, port) as server:
            server.starttls()
            server.login(user, pwd)
            server.sendmail(from_email, [to_email], msg.as_string())

        logger.info("SMTP alert sent.")

    def _send_twilio(self, message: str):
        try:
            from twilio.rest import Client
        except Exception:
            logger.error("Twilio package not installed. pip install twilio")
            logger.warning(f"[ALERT-CONSOLE] {message}")
            return

        sid = os.getenv("TWILIO_ACCOUNT_SID")
        token = os.getenv("TWILIO_AUTH_TOKEN")
        from_num = os.getenv("TWILIO_FROM")
        to_num = os.getenv("TWILIO_TO")

        if not all([sid, token, from_num, to_num]):
            logger.error("Twilio config missing. Falling back to console.")
            logger.warning(f"[ALERT-CONSOLE] {message}")
            return

        client = Client(sid, token)
        client.messages.create(body=message, from_=from_num, to=to_num)
        logger.info("Twilio SMS alert sent.")