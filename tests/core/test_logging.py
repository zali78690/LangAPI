"""Tests for logging configuration."""

import structlog

from lang_api.core.logging import configure_logging


class TestConfigureLogging:
    """Tests for configure_logging function."""

    def test_json_mode_configures_json_renderer(self) -> None:
        """Production mode configures structlog with JSONRenderer."""
        configure_logging(debug=False)
        config = structlog.get_config()
        renderer = config["processors"][-1]
        assert isinstance(renderer, structlog.processors.JSONRenderer)

    def test_debug_mode_configures_console_renderer(self) -> None:
        """Debug mode configures structlog with ConsoleRenderer."""
        configure_logging(debug=True)
        config = structlog.get_config()
        renderer = config["processors"][-1]
        assert isinstance(renderer, structlog.dev.ConsoleRenderer)

    def test_contextvars_processor_included(self) -> None:
        """Contextvars merger is in the processor chain for request-scoped logging."""
        configure_logging(debug=False)
        config = structlog.get_config()
        assert structlog.contextvars.merge_contextvars in config["processors"]

    def test_timestamper_included(self) -> None:
        """ISO UTC timestamps are added to log output."""
        configure_logging(debug=False)
        config = structlog.get_config()
        timestampers = [p for p in config["processors"] if isinstance(p, structlog.processors.TimeStamper)]
        assert len(timestampers) == 1
        assert timestampers[0].fmt == "iso"
