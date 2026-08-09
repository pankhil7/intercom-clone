"""
Central logging setup using structlog.

- Development (DEBUG=true): colored, human-readable console output
- Production (DEBUG=false): JSON lines — one JSON object per log entry,
  works with Railway / Datadog / CloudWatch log aggregators out of the box

Usage in any module:
    from app.logging_config import get_logger
    logger = get_logger(__name__)
    logger.info("conversation_created", conversation_id=str(conv.id), org_id=str(org_id))

NEVER log: passwords, tokens (JWT/API/widget), cookie values, full email bodies.
"""

import logging
import sys

import structlog
from app.config import settings


def setup_logging() -> None:
    """Call once at app startup (from main.py lifespan)."""

    shared_processors = [
        structlog.contextvars.merge_contextvars,          # attach request-scoped fields
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
    ]

    if settings.DEBUG:
        # Pretty colored output for local development
        processors = shared_processors + [
            structlog.dev.ConsoleRenderer(colors=True),
        ]
    else:
        # JSON lines for production log aggregators
        processors = shared_processors + [
            structlog.processors.dict_tracebacks,
            structlog.processors.JSONRenderer(),
        ]

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(
            logging.DEBUG if settings.DEBUG else logging.INFO
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(sys.stdout),
        cache_logger_on_first_use=True,
    )

    # Route standard library logging (uvicorn, sqlalchemy, apscheduler) through structlog
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=logging.DEBUG if settings.DEBUG else logging.INFO,
    )
    # Silence noisy loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)  # we log requests ourselves
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("apscheduler").setLevel(logging.INFO)


def get_logger(name: str) -> structlog.BoundLogger:
    return structlog.get_logger(name)
