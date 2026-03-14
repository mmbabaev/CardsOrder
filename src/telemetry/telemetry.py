"""Monium telemetry: OTel logs for the Telegram bot.

Architecture: SDK → OTel Collector (localhost:4318) → Monium gRPC.

Set MONIUM_API_KEY to enable (used as a feature flag — actual auth is in otel-collector.yaml).
If not set, all calls are silent no-ops.
"""

import os
import time
import logging

logger = logging.getLogger(__name__)

_otel_logger = None


def init_telemetry() -> bool:
    """Initialize OTel log exporter to Monium.

    Required env vars:
      MONIUM_API_KEY   — used as feature flag (auth is handled by OTel Collector)

    Optional:
      OTEL_SERVICE_NAME           (default: cards-order-bot)
      OTEL_EXPORTER_OTLP_ENDPOINT (default: http://localhost:4318)

    Returns True if initialized, False if disabled or setup failed.
    """
    global _otel_logger

    api_key = os.getenv('MONIUM_API_KEY')
    if not api_key:
        logger.info("MONIUM_API_KEY not set — logs disabled")
        return False

    try:
        from opentelemetry._logs import set_logger_provider
        from opentelemetry.sdk._logs import LoggerProvider
        from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
        from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter
        from opentelemetry.sdk.resources import Resource, SERVICE_NAME

        service_name = os.getenv('OTEL_SERVICE_NAME', 'cards-order-bot')
        # SDK отправляет на локальный OTel Collector; он сам передаёт в Monium с auth
        collector_endpoint = os.getenv('OTEL_EXPORTER_OTLP_ENDPOINT', 'http://localhost:4318')

        exporter = OTLPLogExporter(endpoint=collector_endpoint)

        provider = LoggerProvider(
            resource=Resource(attributes={SERVICE_NAME: service_name}),
        )
        provider.add_log_record_processor(BatchLogRecordProcessor(exporter))
        set_logger_provider(provider)

        _otel_logger = provider.get_logger('cards-order-bot')

        logger.info(f"Monium telemetry enabled (collector={collector_endpoint!r}, service={service_name!r})")
        return True

    except ImportError as e:
        logger.warning(f"OpenTelemetry packages not installed — logs disabled: {e}")
        return False
    except Exception as e:
        logger.error(f"Failed to initialize Monium telemetry: {e}")
        return False


def _emit(body: str, attributes: dict) -> None:
    if _otel_logger is None:
        return
    from opentelemetry.sdk._logs._internal import LogRecord
    from opentelemetry._logs import SeverityNumber

    _otel_logger.emit(LogRecord(
        timestamp=time.time_ns(),
        severity_number=SeverityNumber.INFO,
        severity_text='INFO',
        body=body,
        attributes=attributes,
    ))


def record_command(command: str) -> None:
    """Log a bot command (/start, /help)."""
    _emit('bot_command', {'event': 'command', 'command': command})


def record_request(input_type: str, status: str, site: str = '') -> None:
    """Log a parse request outcome.

    Args:
        input_type: 'document' | 'text'
        status:     'success' | 'error_invalid_type' | 'error_too_large' |
                    'error_unsupported_site' | 'error_empty_cart' |
                    'error_parse' | 'error_os' | 'error_unknown'
        site:       detected site slug, e.g. 'card_kingdom' (empty on error)
    """
    attrs: dict = {'event': 'request', 'input_type': input_type, 'status': status}
    if site:
        attrs['site'] = site.lower().replace(' ', '_')
    _emit('bot_request', attrs)


def record_processing(duration: float, site: str, total_cards: int, total_price: float) -> None:
    """Log timing and order-size data for a successful parse."""
    _emit('bot_processing', {
        'event': 'processing',
        'site': site.lower().replace(' ', '_'),
        'duration_seconds': round(duration, 2),
        'total_cards': total_cards,
        'total_price_usd': round(total_price, 2),
    })
