"""
Structured JSON logger for the Event Producer service.

Why structured logging:
  - Machine-parseable (CloudWatch Logs Insights, ELK, Datadog)
  - Consistent format across all services
  - Correlation IDs enable request tracing
  - Severity levels enable log filtering in production
"""

import logging
import json
import sys
from datetime import datetime, timezone


class JSONFormatter(logging.Formatter):
    """Format log records as JSON for structured log ingestion."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "service": "event-producer",
            "message": record.getMessage(),
            "logger": record.name,
        }

        # Attach extra fields if present
        if hasattr(record, "event_type"):
            log_entry["event_type"] = record.event_type
        if hasattr(record, "batch_size"):
            log_entry["batch_size"] = record.batch_size
        if hasattr(record, "status_code"):
            log_entry["status_code"] = record.status_code
        if hasattr(record, "duration_ms"):
            log_entry["duration_ms"] = record.duration_ms
        if hasattr(record, "error"):
            log_entry["error"] = record.error

        if record.exc_info and record.exc_info[1]:
            log_entry["exception"] = str(record.exc_info[1])
            log_entry["exception_type"] = type(record.exc_info[1]).__name__

        return json.dumps(log_entry)


def get_logger(name: str, level: str = "INFO") -> logging.Logger:
    """Create a structured JSON logger.

    Args:
        name: Logger name (typically module __name__).
        level: Logging level string (DEBUG, INFO, WARNING, ERROR).

    Returns:
        Configured logger instance.
    """
    logger = logging.getLogger(name)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JSONFormatter())
        logger.addHandler(handler)

    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    return logger
