import structlog
from typing import Any


def configure_logging() -> None:
    """Configure structlog with appropriate processors and settings."""
    structlog.configure(
        processors=[
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S"),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


def get_logger(name: str = None) -> structlog.BoundLogger:
    """
    Get a configured structured logger instance.

    Args:
        name: Optional name for the logger, typically the module name

    Returns:
        A configured structlog logger instance
    """
    # Initialize logging configuration if not already done
    try:
        return structlog.get_logger(name)
    except Exception as e:
        configure_logging()
        logger = structlog.get_logger(name)
        logger.warning("Had to configure logging on the fly", error=str(e))
        return logger

