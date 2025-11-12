"""Custom exceptions for the Redacto Events SDK."""


class ConfigurationError(Exception):
    """Raised when required configuration parameters are missing or invalid."""

    pass


class UnsupportedEventTypeError(Exception):
    """Raised when an unsupported event type is used."""

    pass
