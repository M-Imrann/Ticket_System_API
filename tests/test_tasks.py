import pytest
from app import tasks
import logging
import builtins


@pytest.mark.asyncio
def test_log_reply_logs_info(monkeypatch):
    """
    Testcase that log_reply writes correct log message
    """
    logged = []

    def fake_info(msg):
        logged.append(msg)

    monkeypatch.setattr(logging, "info", fake_info)
    tasks.log_reply(ticket_id=1, message="Hello", agent_email="agent@test.com")

    assert logged[0] == "[REPLY] ticket=1 by=agent@test.com :: Hello"


@pytest.mark.asyncio
def test_send_email_notification_logs(monkeypatch):
    """
    Test send_email_notification logs the email instead of sending
    """
    logged = []

    class DummySMTP:
        def __init__(self, host, port): pass
        def starttls(self): pass
        def login(self, username, password): pass
        def sendmail(self, from_addr, to_addrs, msg): pass
        def quit(self): pass

    monkeypatch.setattr(tasks, "smtplib", builtins.__import__("smtplib"))
    monkeypatch.setattr(tasks.smtplib, "SMTP", DummySMTP)
    monkeypatch.setattr(tasks.smtplib, "SMTP_SSL", DummySMTP)

    monkeypatch.setattr(tasks.logging, "info", lambda msg: logged.append(msg))

    tasks.send_email_notification(
        email="user@test.com",
        message="Hello Test",
        subject="Test Subject")
    assert any("user@test.com" in log for log in logged)
