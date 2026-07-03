"""
Event transformation and validation processor.

Receives raw base64-decoded Kinesis records, validates the schema,
enriches with processing metadata, and returns ProcessedEvent objects.
"""

import json
from typing import Optional

from models.events import ProcessedEvent
from utils.logger import get_logger

logger = get_logger(__name__)

# Required fields in every event
REQUIRED_FIELDS = {"event_id", "event_type", "timestamp"}
VALID_EVENT_TYPES = {
    "PRODUCT_VIEW", "ADD_TO_CART", "PURCHASE",
    "PAYMENT", "USER_LOGIN", "SEARCH",
}


def validate_event(raw_data: dict) -> bool:
    """Validate that a raw event has all required fields and valid type."""
    missing = REQUIRED_FIELDS - set(raw_data.keys())
    if missing:
        logger.warning(
            f"Event missing required fields: {missing}",
            extra={"event_id": raw_data.get("event_id", "unknown")},
        )
        return False

    if raw_data.get("event_type") not in VALID_EVENT_TYPES:
        logger.warning(
            f"Invalid event_type: {raw_data.get('event_type')}",
            extra={"event_id": raw_data.get("event_id", "unknown")},
        )
        return False

    return True


def transform_kinesis_record(kinesis_record: dict) -> Optional[ProcessedEvent]:
    """Decode a Kinesis record and transform into a ProcessedEvent.

    Kinesis records arrive as:
      {"kinesis": {"data": "<base64-encoded-json>"}, ...}

    The data is base64-decoded by the Lambda runtime, so we receive
    the raw bytes which we decode as UTF-8 JSON.

    Args:
        kinesis_record: A single record from the Kinesis event batch.

    Returns:
        ProcessedEvent if valid, None if validation fails.
    """
    import base64

    try:
        # Lambda provides base64-encoded data
        encoded_data = kinesis_record["kinesis"]["data"]
        decoded_bytes = base64.b64decode(encoded_data)
        raw_data = json.loads(decoded_bytes.decode("utf-8"))
    except (KeyError, json.JSONDecodeError, UnicodeDecodeError) as e:
        logger.error(
            f"Failed to decode Kinesis record: {e}",
            extra={"error": str(e)},
        )
        return None

    # Validate schema
    if not validate_event(raw_data):
        return None

    return ProcessedEvent(raw_data)


def transform_sqs_record(sqs_record: dict) -> Optional[ProcessedEvent]:
    """Decode an SQS record and transform into a ProcessedEvent.

    SQS records arrive as:
      {"body": "<json-string>"}, ...}

    Args:
        sqs_record: A single record from the SQS event batch.

    Returns:
        ProcessedEvent if valid, None if validation fails.
    """
    try:
        raw_data = json.loads(sqs_record["body"])
    except (KeyError, json.JSONDecodeError) as e:
        logger.error(
            f"Failed to decode SQS record: {e}",
            extra={"error": str(e)},
        )
        return None

    # Validate schema
    if not validate_event(raw_data):
        return None

    return ProcessedEvent(raw_data)


def transform_record(record: dict) -> Optional[ProcessedEvent]:
    """Decode a Kinesis or SQS record and transform into a ProcessedEvent.

    Args:
        record: A Kinesis or SQS record dictionary.

    Returns:
        ProcessedEvent if valid, None otherwise.
    """
    if "kinesis" in record:
        return transform_kinesis_record(record)
    elif "body" in record:
        return transform_sqs_record(record)
    return None
