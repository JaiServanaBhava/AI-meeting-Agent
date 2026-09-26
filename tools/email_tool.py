"""CrewAI Tool: Follow-up Email Dispatcher via SMTP."""

import os
import smtplib
from email.mime.text import MIMEText
from typing import Type
try:
    from pydantic import BaseModel, Field
except ImportError:
    class BaseModel:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)
    def Field(*args, **kwargs):
        return kwargs.get("default", None)

import config

try:
    from crewai.tools import BaseTool
except ImportError:
    class BaseTool:
        def __init__(self, **kwargs):
            pass



class EmailToolSchema(BaseModel):
    recipient_email: str = Field(..., description="Target email address of the participant.")
    subject: str = Field(..., description="Email subject line.")
    body: str = Field(..., description="Personalized email message body.")


class MailerTool(BaseTool):
    name: str = "mailer_tool"
    description: str = "Sends formatted follow-up emails to meeting participants using SMTP."
    args_schema: Type[BaseModel] = EmailToolSchema

    def _run(self, recipient_email: str, subject: str, body: str) -> str:
        sender = config.SMTP_EMAIL or os.getenv("SMTP_EMAIL", "")
        password = config.SMTP_PASSWORD or os.getenv("SMTP_PASSWORD", "")

        if not sender or not password:
            return (
                f"[Simulated Dispatch] Email to '{recipient_email}' successfully generated and queued. "
                f"(To deliver live emails, configure SMTP_EMAIL and SMTP_PASSWORD in .env)"
            )

        try:
            msg = MIMEText(body, "plain")
            msg["From"] = sender
            msg["To"] = recipient_email
            msg["Subject"] = subject

            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                server.login(sender, password)
                server.sendmail(sender, recipient_email, msg.as_string())
            return f"Email successfully delivered to {recipient_email}."
        except Exception as e:
            return f"SMTP delivery encountered an error: {str(e)}"
