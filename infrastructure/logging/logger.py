import logging
import sys
import structlog

def setup_logging(level: str = "INFO", environment: str = "development") -> None:
    """
    Configures structured logging for KAHNA.
    
    Args:
        level: The minimum logging level (e.g., "INFO", "DEBUG").
        environment: The running environment (e.g., "development", "production").
    """
    logging_level = getattr(logging, level.upper(), logging.INFO)
    
    structlog.configure(
        processors=[
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.dev.ConsoleRenderer() if environment == "development" else structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=logging_level,
    )

def get_logger(name: str) -> structlog.BoundLogger:
    """Returns a structured logger for the given module name."""
    return structlog.get_logger(name)
