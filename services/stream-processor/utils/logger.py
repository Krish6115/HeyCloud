"""
Structured logger for Lambda functions.

Uses the same JSON format as the event producer for consistency
across the entire pipeline. CloudWatch Logs Insights can query
all services using the same query syntax.
"""

import json
import logging
import os
import sys
from datetime import datetime, timezone


class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "service": os.environ.get("POWERTOOLS_SERVICE_NAME", "unknown"),
            "message": record.getMessage(),
            "logger": record.name,
        }

        # Attach any extra fields
        for key in ("event_id", "event_type", "batch_size", "duration_ms",
                     "error", "record_count", "table_name", "bucket"):
            if hasattr(record, key):
                log_entry[key] = getattr(record, key)

        if record.exc_info and record.exc_info[1]:
            log_entry["exception"] = str(record.exc_info[1])
            log_entry["exception_type"] = type(record.exc_info[1]).__name__

        return json.dumps(log_entry)


def get_logger(name: str) -> logging.Logger:
    level = os.environ.get("LOG_LEVEL", "INFO").upper()
    logger = logging.getLogger(name)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JSONFormatter())
        logger.addHandler(handler)

    logger.setLevel(getattr(logging, level, logging.INFO))
    return logger
