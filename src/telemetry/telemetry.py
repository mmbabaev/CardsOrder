"""Monium telemetry: OTel metrics for the Telegram bot.

Set MONIUM_API_KEY and MONIUM_PROJECT env vars to enable.
If not set, all calls are silent no-ops.
"""

import os
import logging

logger = logging.getLogger(__name__)

# Instruments are None until init_telemetry() succeeds
_commands_counter = None
_requests_counter = None
_processing_duration = None
_order_cards = None
_order_price = None


def init_telemetry() -> bool:
    """Initialize OTel metrics exporter to Monium.

    Required env vars:
      MONIUM_API_KEY   — Yandex Cloud API key with monium.telemetry.writer role
      MONIUM_PROJECT   — Monium project name, e.g. folder__b1g86q4m5vej...

    Optional:
      OTEL_SERVICE_NAME  (default: cards-order-bot)

    Returns True if initialized, False if disabled or setup failed.
    """
    global _commands_counter, _requests_counter
    global _processing_duration, _order_cards, _order_price

    api_key = os.getenv('MONIUM_API_KEY')
    if not api_key:
        logger.info("MONIUM_API_KEY not set — metrics disabled")
        return False

    try:
        from opentelemetry import metrics
        from opentelemetry.sdk.metrics import MeterProvider
        from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
        from opentelemetry.sdk.resources import Resource, SERVICE_NAME
        from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
        from grpc import Compression

        project = os.getenv('MONIUM_PROJECT', '')
        service_name = os.getenv('OTEL_SERVICE_NAME', 'cards-order-bot')

        exporter = OTLPMetricExporter(
            endpoint='ingest.monium.yandex.cloud:443',
            headers=(
                ('authorization', f'Api-Key {api_key}'),
                ('x-monium-project', project),
            ),
            compression=Compression.Gzip,
        )

        reader = PeriodicExportingMetricReader(exporter, export_interval_millis=60_000)
        provider = MeterProvider(
            resource=Resource(attributes={SERVICE_NAME: service_name}),
            metric_readers=[reader],
        )
        metrics.set_meter_provider(provider)

        meter = metrics.get_meter('cards-order-bot')

        _commands_counter = meter.create_counter(
            'bot_commands_total',
            description='Bot commands received (/start, /help)',
        )
        _requests_counter = meter.create_counter(
            'bot_requests_total',
            description='Parse requests by type and outcome',
        )
        _processing_duration = meter.create_histogram(
            'bot_processing_duration_seconds',
            unit='s',
            description='End-to-end processing time (download → parse → excel)',
        )
        _order_cards = meter.create_histogram(
            'bot_order_unique_cards',
            description='Unique card count per successful order',
        )
        _order_price = meter.create_histogram(
            'bot_order_price_usd',
            unit='USD',
            description='Total order price per successful parse',
        )

        logger.info(f"Monium telemetry enabled (project={project!r}, service={service_name!r})")
        return True

    except ImportError as e:
        logger.warning(f"OpenTelemetry packages not installed — metrics disabled: {e}")
        return False
    except Exception as e:
        logger.error(f"Failed to initialize Monium telemetry: {e}")
        return False


def record_command(command: str) -> None:
    """Increment the command counter. command: 'start' | 'help'."""
    if _commands_counter is not None:
        _commands_counter.add(1, {'command': command})


def record_request(input_type: str, status: str, site: str = '') -> None:
    """Increment the request counter.

    Args:
        input_type: 'document' | 'text'
        status:     'success' | 'error_invalid_type' | 'error_too_large' |
                    'error_unsupported_site' | 'error_empty_cart' |
                    'error_parse' | 'error_os' | 'error_unknown'
        site:       detected site slug, e.g. 'card_kingdom' (empty on error)
    """
    if _requests_counter is not None:
        attrs: dict = {'input_type': input_type, 'status': status}
        if site:
            attrs['site'] = site.lower().replace(' ', '_')
        _requests_counter.add(1, attrs)


def record_processing(duration: float, site: str, total_cards: int, total_price: float) -> None:
    """Record timing and order-size metrics for a successful parse."""
    attrs = {'site': site.lower().replace(' ', '_')}
    if _processing_duration is not None:
        _processing_duration.record(duration, attrs)
    if _order_cards is not None:
        _order_cards.record(total_cards, attrs)
    if _order_price is not None:
        _order_price.record(total_price, attrs)
