"""Email service module supporting production SMTP delivery and test mail sinks."""
import os
import smtplib
from datetime import datetime, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any, Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

# In-memory test mail sink for automated tests
_TEST_MAIL_SINK: List[Dict[str, Any]] = []
_TEST_MAIL_SINK_ENABLED: bool = False

def enable_test_mail_sink(enabled: bool = True) -> None:
    """Enables or disables the isolated test mail sink."""
    global _TEST_MAIL_SINK_ENABLED
    _TEST_MAIL_SINK_ENABLED = enabled

def is_test_mail_sink_enabled() -> bool:
    return _TEST_MAIL_SINK_ENABLED

def get_test_mail_sink() -> List[Dict[str, Any]]:
    """Returns all captured messages from the test mail sink."""
    return list(_TEST_MAIL_SINK)

def clear_test_mail_sink() -> None:
    """Empties the test mail sink."""
    _TEST_MAIL_SINK.clear()

def is_email_configured() -> bool:
    """
    Checks if email delivery is configured in the current environment.
    Returns True if either test mail sink is active or valid SMTP configuration exists.
    """
    if _TEST_MAIL_SINK_ENABLED:
        return True
    
    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = os.getenv("SMTP_PORT")
    return bool(smtp_host and smtp_port)

def send_password_reset_email(
    to_email: str,
    reset_token: str,
    user_name: Optional[str] = None
) -> bool:
    """
    Dispatches a password reset email containing the secret single-use reset token.
    If test mail sink is enabled, delivers message to the sink.
    If SMTP is configured, delivers via SMTP.
    If unconfigured, records delivery failure safely without logging the token.
    """
    subject = "FinRegTech ShipYard - Password Recovery Request"
    body_text = (
        f"Hello {user_name or 'User'},\n\n"
        f"A password reset was requested for your FinRegTech ShipYard account.\n"
        f"Your single-use password recovery token is:\n\n"
        f"{reset_token}\n\n"
        f"This token is valid for 15 minutes and can only be used once.\n"
        f"If you did not request this reset, please ignore this message.\n\n"
        f"— FinRegTech ShipYard Security Team"
    )

    if _TEST_MAIL_SINK_ENABLED:
        _TEST_MAIL_SINK.append({
            "to": to_email,
            "subject": subject,
            "body": body_text,
            "token": reset_token,
            "sent_at": datetime.now(timezone.utc).isoformat()
        })
        return True

    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = os.getenv("SMTP_PORT")
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")

    if not smtp_host or not smtp_port:
        # Unconfigured delivery channel
        return False

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = os.getenv("SMTP_FROM", "no-reply@finregtech.io")
        msg["To"] = to_email
        msg.attach(MIMEText(body_text, "plain"))

        port = int(smtp_port)
        if port == 465:
            server = smtplib.SMTP_SSL(smtp_host, port, timeout=10)
        else:
            server = smtplib.SMTP(smtp_host, port, timeout=10)
            server.starttls()

        if smtp_user and smtp_password:
            server.login(smtp_user, smtp_password)

        server.sendmail(msg["From"], [to_email], msg.as_string())
        server.quit()
        return True
    except Exception as exc:
        logger.warning("SMTP dispatch failed: %s", exc)
        return False
