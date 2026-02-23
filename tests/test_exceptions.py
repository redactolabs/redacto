import pytest

from redacto.events.exceptions import ConfigurationError, UnsupportedEventTypeError


class TestExceptions:
    def test_configuration_error(self):
        with pytest.raises(ConfigurationError, match="missing url"):
            raise ConfigurationError("missing url")

    def test_unsupported_event_type_error(self):
        with pytest.raises(UnsupportedEventTypeError, match="bad.event"):
            raise UnsupportedEventTypeError("bad.event")

    def test_configuration_error_is_exception(self):
        assert issubclass(ConfigurationError, Exception)

    def test_unsupported_event_type_error_is_exception(self):
        assert issubclass(UnsupportedEventTypeError, Exception)
