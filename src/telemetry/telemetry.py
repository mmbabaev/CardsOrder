"""Bot analytics + error alerting, backed by the botstat library.

Events go to a local SQLite DB (BOTSTAT_DB, default 'analytics.db' in the
working directory). Errors are additionally pushed to the admin over Telegram
when ADMIN_CHAT_ID is set and configure_alerts() has been called with the app.

Debug mode: BOT_ENV=debug or DEBUG_MODE=1.
"""

import os
import asyncio
import logging
from typing import Optional

from botstat import Analytics, SQLiteBackend, CallbackAlerter

logger = logging.getLogger(__name__)

_analytics: Optional[Analytics] = None

# Late-bound Telegram alert target — set after the Application is built.
_alert_app = None
_alert_chat_id: Optional[int] = None


def is_debug_mode() -> bool:
    """Returns True when running in debug mode (BOT_ENV=debug or DEBUG_MODE=1)."""
    return (
        os.getenv('BOT_ENV', '').lower() == 'debug'
        or os.getenv('DEBUG_MODE', '').lower() in ('1', 'true')
    )


def _deliver_alert(text: str) -> None:
    """Schedule a Telegram DM to the admin. Runs on the bot's event loop."""
    app, chat_id = _alert_app, _alert_chat_id
    if app is None or chat_id is None:
        return
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        return
    loop.create_task(app.bot.send_message(chat_id=chat_id, text=text))


def init_telemetry() -> bool:
    """Initialize analytics. Always on — local SQLite, no external service."""
    global _analytics
    db_path = os.getenv('BOTSTAT_DB', 'analytics.db')
    try:
        _analytics = Analytics(
            SQLiteBackend(db_path),
            alerter=CallbackAlerter(_deliver_alert),
        )
        logger.info(f"Analytics enabled (db={db_path!r})")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize analytics: {e}")
        _analytics = None
        return False


def configure_alerts(application, admin_chat_id: Optional[int]) -> None:
    """Wire error alerts to a Telegram chat. Call after building the Application."""
    global _alert_app, _alert_chat_id
    _alert_app = application
    _alert_chat_id = admin_chat_id
    if admin_chat_id:
        logger.info(f"Error alerts will be sent to chat {admin_chat_id}")
    else:
        logger.info("ADMIN_CHAT_ID not set — error alerts disabled (still recorded)")


def record_command(command: str, user_id: Optional[int] = None) -> None:
    if _analytics is not None:
        _analytics.record_command(str(command), user_id=user_id)


def record_request(
    input_type: str, status: str, site: str = '', user_id: Optional[int] = None
) -> None:
    if _analytics is None:
        return
    attrs = {'input_type': str(input_type)}
    if site:
        attrs['site'] = site.lower().replace(' ', '_')
    _analytics.record_request(str(status), user_id=user_id, **attrs)


def record_order(
    site: str,
    total_cards: int,
    total_quantity: int,
    total_price: float,
    foil_count: int,
    input_type: str = '',
    duration: Optional[float] = None,
    user_id: Optional[int] = None,
) -> None:
    """Persist one completed order as an 'order' event (full history record)."""
    if _analytics is None:
        return
    attrs = {
        'input_type': str(input_type),
        'total_cards': int(total_cards),
        'total_quantity': int(total_quantity),
        'total_price': round(float(total_price), 2),
        'foil_count': int(foil_count),
    }
    if duration is not None:
        attrs['duration_seconds'] = round(duration, 2)
    _analytics.record_event(
        'order', site.lower().replace(' ', '_'), user_id=user_id, **attrs
    )


def record_error(error_type: str, message: str = '', **attrs) -> None:
    if _analytics is None:
        return
    user_id = attrs.pop('user_id', None)
    clean = {k: str(v) for k, v in attrs.items() if v is not None}
    _analytics.record_error(str(error_type), message, user_id=user_id, **clean)


def get_summary() -> Optional[dict]:
    return _analytics.summary() if _analytics is not None else None


def format_summary(s: dict) -> str:
    """Render a summary dict (from botstat) into a Telegram message."""
    lines = [
        "📊 Статистика бота",
        "",
        "👤 Уникальные пользователи:",
        f"  • всего: {s['users_total']}",
        f"  • за 24ч: {s['users_24h']}",
        f"  • за 30д: {s['users_30d']}",
        "",
        f"📥 Запросов: {s['requests_total']} (24ч: {s['requests_24h']})",
        f"❌ Ошибок: {s['errors_total']} (24ч: {s['errors_24h']})",
    ]
    if s.get('top_sites'):
        lines.append("")
        lines.append("🌐 Топ сайтов:")
        lines += [f"  • {site}: {n}" for site, n in s['top_sites'].items()]
    if s.get('by_status'):
        lines.append("")
        lines.append("📈 По статусам:")
        lines += [f"  • {st}: {n}" for st, n in s['by_status'].items()]
    return "\n".join(lines)


ORDERS_PER_PAGE = 10


def get_orders_count() -> int:
    return _analytics.count(event_type='order') if _analytics is not None else 0


def get_orders_page(page: int, per_page: int = ORDERS_PER_PAGE):
    if _analytics is None:
        return []
    return _analytics.recent(
        event_type='order', limit=per_page, offset=max(0, page) * per_page
    )


def get_monthly_orders():
    if _analytics is None:
        return []
    return _analytics.timeseries('total_price', event_type='order', bucket='month')


def format_orders(monthly, orders, page: int, total: int, per_page: int = ORDERS_PER_PAGE) -> str:
    import datetime

    lines = ["📦 Заказы по месяцам:"]
    if monthly:
        for r in reversed(monthly[-12:]):
            lines.append(f"  • {r['period']}: {r['count']} заказов на ${r['sum']:.2f}")
    else:
        lines.append("  (пока нет заказов)")

    pages = max(1, (total + per_page - 1) // per_page)
    lines.append("")
    lines.append(f"🕘 История (стр. {page + 1}/{pages}, всего {total}):")
    for e in orders:
        when = datetime.datetime.fromtimestamp(
            e.ts_ns / 1e9, datetime.timezone.utc
        ).strftime('%d.%m %H:%M')
        a = e.attributes
        price = a.get('total_price', 0)
        line = f"  • {when} — {e.name}, {a.get('total_cards', '?')} карт, ${price:.2f}"
        if e.user_id:
            line += f" (id {e.user_id})"
        lines.append(line)
    return "\n".join(lines)
