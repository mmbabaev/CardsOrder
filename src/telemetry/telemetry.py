"""Monium telemetry: OTel logs + metrics for the Telegram bot.

Architecture: SDK → OTel Collector (localhost:4318) → Monium gRPC.

Set MONIUM_API_KEY to enable (used as a feature flag — actual auth is in otel-collector.yaml).
If not set, all calls are silent no-ops.

Debug mode: BOT_ENV=debug or DEBUG_MODE=1.
"""

import os
import time
import logging

logger = logging.getLogger(__name__)

_otel_logger = None
_cmd_counter = None
_req_counter = None


def is_debug_mode() -> bool:
    """Returns True when running in debug mode (BOT_ENV=debug or DEBUG_MODE=1)."""
    return (
        os.getenv('BOT_ENV', '').lower() == 'debug'
        or os.getenv('DEBUG_MODE', '').lower() in ('1', 'true')
    )


def init_telemetry() -> bool:
    """Initialize OTel logs + metrics exporters to Monium.

    Required env vars:
      MONIUM_API_KEY   — used as feature flag (auth is handled by OTel Collector)

    Optional:
      OTEL_SERVICE_NAME           (default: cards-order-bot)
      OTEL_EXPORTER_OTLP_ENDPOINT (default: http://localhost:4318)

    Returns True if initialized, False if disabled or setup failed.
    """
    global _otel_logger, _cmd_counter, _req_counter

    api_key = os.getenv('MONIUM_API_KEY')
    if not api_key:
        logger.info("MONIUM_API_KEY not set — telemetry disabled")
        return False

    try:
        from opentelemetry._logs import set_logger_provider
        from opentelemetry.sdk._logs import LoggerProvider
        from opentelemetry.sdk._logs.export import SimpleLogRecordProcessor
        from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter
        from opentelemetry.sdk.resources import Resource, SERVICE_NAME
        from opentelemetry import metrics as otel_metrics
        from opentelemetry.sdk.metrics import MeterProvider
        from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
        from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter

        service_name = os.getenv('OTEL_SERVICE_NAME', 'cards-order-bot')
        collector_base = os.getenv('OTEL_EXPORTER_OTLP_ENDPOINT', 'http://localhost:4318')
        resource = Resource(attributes={SERVICE_NAME: service_name})

        # — Logs —
        log_endpoint = collector_base.rstrip('/') + '/v1/logs'
        log_exporter = OTLPLogExporter(endpoint=log_endpoint)
        log_provider = LoggerProvider(resource=resource)
        log_provider.add_log_record_processor(SimpleLogRecordProcessor(log_exporter))
        set_logger_provider(log_provider)
        _otel_logger = log_provider.get_logger('cards-order-bot')

        # — Metrics (metrics channel) —
        metrics_endpoint = collector_base.rstrip('/') + '/v1/metrics'
        metric_exporter = OTLPMetricExporter(endpoint=metrics_endpoint)
        reader = PeriodicExportingMetricReader(metric_exporter, export_interval_millis=30_000)
        meter_provider = MeterProvider(resource=resource, metric_readers=[reader])
        otel_metrics.set_meter_provider(meter_provider)
        meter = meter_provider.get_meter('cards-order-bot')

        _cmd_counter = meter.create_counter(
            'bot_commands_total',
            description='Bot command invocations by command name',
        )
        _req_counter = meter.create_counter(
            'parse_requests_total',
            description='Parse request outcomes by input_type and status',
        )

        logger.info(
            f"Monium telemetry enabled (collector={collector_base!r}, service={service_name!r})"
        )
        return True

    except ImportError as e:
        logger.warning(f"OpenTelemetry packages not installed — telemetry disabled: {e}")
        return False
    except Exception as e:
        logger.error(f"Failed to initialize Monium telemetry: {e}")
        return False


def _emit_log(body: str, attributes: dict, severity_number=None, severity_text: str = 'INFO') -> None:
    if _otel_logger is None:
        return
    from opentelemetry.sdk._logs._internal import LogRecord
    from opentelemetry._logs import SeverityNumber

    _otel_logger.emit(LogRecord(
        timestamp=time.time_ns(),
        severity_number=severity_number or SeverityNumber.INFO,
        severity_text=severity_text,
        body=body,
        attributes=attributes,
    ))


def record_command(command: str) -> None:
    """Log a bot command and increment the bot_commands_total metric counter."""
    _emit_log('bot_command', {'event': 'command', 'command': command})
    if _cmd_counter is not None:
        _cmd_counter.add(1, {'command': command})


def record_request(input_type: str, status: str, site: str = '') -> None:
    """Log a parse request outcome and increment the parse_requests_total metric counter.

    Args:
        input_type: 'document' | 'text'
        status:     'success' | 'error_invalid_type' | 'error_too_large' |
                    'error_unsupported_site' | 'error_empty_cart' |
                    'error_parse' | 'error_os' | 'error_unknown'
        site:       detected site slug, e.g. 'card_kingdom' (empty on error)
    """
    log_attrs: dict = {'event': 'request', 'input_type': input_type, 'status': status}
    metric_attrs: dict = {'input_type': input_type, 'status': status}
    if site:
        slug = site.lower().replace(' ', '_')
        log_attrs['site'] = slug
        metric_attrs['site'] = slug
    _emit_log('bot_request', log_attrs)
    if _req_counter is not None:
        _req_counter.add(1, metric_attrs)


def record_processing(duration: float, site: str, total_cards: int, total_price: float) -> None:
    """Log timing and order-size data for a successful parse."""
    _emit_log('bot_processing', {
        'event': 'processing',
        'site': site.lower().replace(' ', '_'),
        'duration_seconds': round(duration, 2),
        'total_cards': total_cards,
        'total_price_usd': round(total_price, 2),
    })


def record_error(error_type: str, message: str, **attrs) -> None:
    """Emit an ERROR-level log to Monium telemetry.

    Also increments parse_requests_total metric when 'input_type' and 'status'
    are provided — so error handlers need only one call instead of two.

    Args:
        error_type: short slug, e.g. 'parse_error', 'os_error', 'easter_egg'
        message:    human-readable error description
        **attrs:    extra key-value attributes (input_type, status, site, user_id, …)
    """
    if _otel_logger is None:
        return
    from opentelemetry._logs import SeverityNumber
    error_attrs = {'event': 'error', 'error_type': error_type, **attrs}
    _emit_log(message, error_attrs, severity_number=SeverityNumber.ERROR, severity_text='ERROR')

    if _req_counter is not None and 'input_type' in attrs and 'status' in attrs:
        metric_attrs: dict = {'input_type': attrs['input_type'], 'status': attrs['status']}
        if 'site' in attrs:
            metric_attrs['site'] = attrs['site']
        _req_counter.add(1, metric_attrs)
