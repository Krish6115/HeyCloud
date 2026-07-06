"""
DynamoDB writer — writes individual events to the hot storage table.

Uses BatchWriteItem for throughput (up to 25 items per batch).
Handles unprocessed items with automatic retry.
"""

import os

import boto3
from botocore.exceptions import ClientError

from models.events import ProcessedEvent
from utils.logger import get_logger
from utils.retry import retry_with_backoff

logger = get_logger(__name__)

dynamodb = boto3.client("dynamodb")
TABLE_NAME = os.environ.get("EVENTS_TABLE_NAME", "heycloud-dev-events")


@retry_with_backoff(max_retries=3, retryable_exceptions=(ClientError,))
def _batch_write(items: list[dict]) -> int:
    """Write a batch of items to DynamoDB (max 25 per API call).

    Returns:
        Number of successfully written items.
    """
    request_items = {
        TABLE_NAME: [{"PutRequest": {"Item": item}} for item in items]
    }

    response = dynamodb.batch_write_item(RequestItems=request_items)

    # Handle unprocessed items (throttling)
    unprocessed = response.get("UnprocessedItems", {})
    if unprocessed.get(TABLE_NAME):
        unprocessed_count = len(unprocessed[TABLE_NAME])
        logger.warning(
            f"{unprocessed_count} items were not processed (throttled)",
            extra={"table_name": TABLE_NAME},
        )
        return len(items) - unprocessed_count

    return len(items)


def write_events(events: list[ProcessedEvent]) -> dict:
    """Write a list of ProcessedEvents to DynamoDB in batches of 25.

    Returns:
        Dict with write stats: {"written": N, "failed": N}
    """
    total_written = 0
    total_failed = 0

    # DynamoDB BatchWriteItem limit is 25 items
    batch_size = 25

    for i in range(0, len(events), batch_size):
        batch = events[i:i + batch_size]
        items = [event.to_dynamodb_item() for event in batch]

        try:
            written = _batch_write(items)
            total_written += written
            total_failed += len(batch) - written
        except ClientError as e:
            logger.error(
                f"DynamoDB batch write failed: {e}",
                extra={"table_name": TABLE_NAME, "error": str(e)},
            )
            total_failed += len(batch)

    logger.info(
        f"DynamoDB write complete: {total_written} written, {total_failed} failed",
        extra={"table_name": TABLE_NAME, "record_count": total_written},
    )

    return {"written": total_written, "failed": total_failed}
