"""Tests for the botstat-backed telemetry adapter."""

import asyncio

import pytest

import src.telemetry.telemetry as t


@pytest.fixture
def telemetry(tmp_path, monkeypatch):
    monkeypatch.setenv("BOTSTAT_DB", str(tmp_path / "a.db"))
    # reset late-bound alert target between tests
    t._alert_app = None
    t._alert_chat_id = None
    assert t.init_telemetry() is True
    yield t


def test_records_and_summary(telemetry):
    telemetry.record_command("start", user_id=1)
    telemetry.record_request("document", "success", "Card Kingdom", user_id=1)
    telemetry.record_request("text", "success", "SCG", user_id=2)
    telemetry.record_request("document", "error_parse", user_id=3)

    s = telemetry.get_summary()
    assert s["users_total"] == 3
    assert s["requests_total"] == 3
    assert s["top_sites"] == {"card_kingdom": 1, "scg": 1}
    assert s["by_status"]["success"] == 2


def test_format_summary_renders(telemetry):
    telemetry.record_command("start", user_id=1)
    msg = telemetry.format_summary(telemetry.get_summary())
    assert "Статистика" in msg
    assert "всего: 1" in msg


def test_record_error_without_loop_is_safe(telemetry):
    telemetry.record_error("parse_error", "boom", user_id=3, site="ck")
    assert telemetry.get_summary()["errors_total"] == 1


def test_functions_noop_before_init(monkeypatch):
    monkeypatch.setattr(t, "_analytics", None)
    t.record_command("start", user_id=1)  # must not raise
    t.record_request("text", "success", user_id=1)
    assert t.get_summary() is None


def test_alert_scheduled_on_error(telemetry):
    sent = []

    class FakeBot:
        async def send_message(self, chat_id, text):
            sent.append((chat_id, text))

    class FakeApp:
        bot = FakeBot()

    telemetry.configure_alerts(FakeApp(), 999)

    async def run():
        telemetry.record_error("parse_error", "boom", user_id=3)
        await asyncio.sleep(0)  # let the scheduled send run

    asyncio.run(run())
    assert sent and sent[0][0] == 999
    assert "parse_error" in sent[0][1]


def test_no_alert_without_admin(telemetry):
    sent = []

    class FakeBot:
        async def send_message(self, chat_id, text):
            sent.append((chat_id, text))

    class FakeApp:
        bot = FakeBot()

    telemetry.configure_alerts(FakeApp(), None)

    async def run():
        telemetry.record_error("parse_error", "boom", user_id=3)
        await asyncio.sleep(0)

    asyncio.run(run())
    assert sent == []
