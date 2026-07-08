"""
S3 writer — archives raw events to the data lake.

Writes each event as an individual JSON object keyed by:
  raw/YYYY/MM/DD/EVENT_TYPE/event_id.json

This partitioning scheme enables efficient Athena queries:
  - Partition by date for time-range scans
  - Partition by event type for type-specific analysis
"""

import json
import os

import boto3
from botocore.exceptions import ClientError

from models.events import ProcessedEvent
from utils.logger import get_logger
from utils.retry import retry_with_backoff

logger = get_logger(__name__)

s3 = boto3.client("s3")
BUCKET_NAME = os.environ.get("DATA_LAKE_BUCKET", "heycloud-dev-data-lake")


@retry_with_backoff(max_retries=3, retryable_exceptions=(ClientError,))
def _put_object(key: str, body: str) -> bool:
    """Write a single object to S3."""
    s3.put_object(
        Bucket=BUCKET_NAME,
        Key=key,
        Body=body.encode("utf-8"),
        ContentType="application/json",
        ServerSideEncryption="AES256",
    )
    return True


def archive_events(events: list[ProcessedEvent]) -> dict:
    """Archive a list of events to S3.

    Returns:
        Dict with archive stats: {"archived": N, "failed": N}
    """
    archived = 0
    failed = 0

    for event in events:
        try:
            key = event.s3_key
            body = json.dumps(event.to_s3_record())
            _put_object(key, body)
            archived += 1
        except Exception as e:
            logger.error(
                f"S3 archive failed for event {event.event_id}: {e}",
                extra={"bucket": BUCKET_NAME, "error": str(e)},
            )
            failed += 1

    logger.info(
        f"S3 archive complete: {archived} archived, {failed} failed",
        extra={"bucket": BUCKET_NAME, "record_count": archived},
    )

    return {"archived": archived, "failed": failed}
