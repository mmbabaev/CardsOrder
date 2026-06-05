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


def test_record_order_and_history(telemetry):
    telemetry.record_order("Card Kingdom", 10, 12, 145.0, 2, input_type="document", duration=1.2, user_id=1)
    telemetry.record_order("SCG", 5, 5, 50.0, 0, input_type="text", user_id=2)

    assert telemetry.get_orders_count() == 2
    page = telemetry.get_orders_page(0)
    assert [e.name for e in page] == ["scg", "card_kingdom"]  # newest first
    assert page[0].attributes["total_price"] == 50.0
    assert page[1].attributes["foil_count"] == 2

    monthly = telemetry.get_monthly_orders()
    assert monthly[-1]["count"] == 2
    assert monthly[-1]["sum"] == 195.0

    text = telemetry.format_orders(monthly, page, 0, 2)
    assert "Заказы по месяцам" in text
    assert "card_kingdom" in text


def test_orders_pagination(telemetry):
    for i in range(12):
        telemetry.record_order("ck", 1, 1, float(i), 0, user_id=1)
    assert telemetry.get_orders_count() == 12
    assert len(telemetry.get_orders_page(0)) == 10
    assert len(telemetry.get_orders_page(1)) == 2


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
