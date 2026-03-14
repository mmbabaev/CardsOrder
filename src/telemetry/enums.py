"""Telemetry label enums — use these instead of raw strings."""

from enum import StrEnum


class BotCommand(StrEnum):
    START = 'start'
    HELP = 'help'


class InputType(StrEnum):
    DOCUMENT = 'document'
    TEXT = 'text'


class RequestStatus(StrEnum):
    SUCCESS = 'success'
    ERROR_INVALID_TYPE = 'error_invalid_type'
    ERROR_TOO_LARGE = 'error_too_large'
    ERROR_UNSUPPORTED_SITE = 'error_unsupported_site'
    ERROR_EMPTY_CART = 'error_empty_cart'
    ERROR_PARSE = 'error_parse'
    ERROR_OS = 'error_os'
    ERROR_UNKNOWN = 'error_unknown'
