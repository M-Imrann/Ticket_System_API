import os
import logging
import smtplib
from email.mime.text import MIMEText
from celery import Celery

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery("worker", broker=REDIS_URL, backend=REDIS_URL)

logging.basicConfig(
    filename="replies.log",
    level=logging.INFO,
    format="%(asctime)s %(message)s"
)


@celery_app.task
def send_email_notification(
    email: str,
    message: str,
    subject: str = "Notification"
):
    """
    Send an email notification for testing purposes.
    Falls back to logging if sending fails.

    Args:
        email: Recipient email address.
        message: Email message content.
        subject: Email subject (default: 'Notification').
    """
    # Default test values for local SMTP server (e.g., MailHog)
    mail_host = os.getenv("MAIL_HOST", "localhost")
    mail_port = int(os.getenv("MAIL_PORT", 1025))
    mail_username = os.getenv("MAIL_USERNAME", "")
    mail_password = os.getenv("MAIL_PASSWORD", "")
    mail_from = os.getenv("MAIL_FROM", "test@example.com")
    use_tls = os.getenv("MAIL_USE_TLS", "false").lower() == "true"
    use_ssl = os.getenv("MAIL_USE_SSL", "false").lower() == "true"

    msg = MIMEText(message)
    msg["Subject"] = subject
    msg["From"] = mail_from
    msg["To"] = email

    try:
        if use_ssl:
            server = smtplib.SMTP_SSL(mail_host, mail_port)
        else:
            server = smtplib.SMTP(mail_host, mail_port)

        if use_tls and not use_ssl:
            server.starttls()

        if mail_username and mail_password:
            server.login(mail_username, mail_password)

        server.sendmail(mail_from, [email], msg.as_string())
        server.quit()
        logging.info(f"[EMAIL -> {email}] {subject}: {message}")
    except Exception as e:
        logging.error(f"Failed to send email to {email}: {e}")


@celery_app.task
def log_reply(ticket_id: int, message: str, agent_email: str):
    """
    Log a reply event to the log file.

    Args:
        ticket_id: ID of the ticket being replied to.
        message: Reply message content.
        agent_email: Email of the agent replying.
    """
    logging.info(f"[REPLY] ticket={ticket_id} by={agent_email} :: {message}")
