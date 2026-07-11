"""
Aggregation processor — computes real-time metrics.

Updates the DynamoDB aggregations table with per-minute metrics:
  - event_count: Total events per type per minute
  - revenue: Sum of purchase amounts per minute
  - active_users: Unique user count approximation

Uses DynamoDB atomic counters (UpdateItem with ADD) for
concurrent-safe aggregation without read-before-write.
"""

import os
from datetime import datetime, timezone
from collections import defaultdict

import boto3
from botocore.exceptions import ClientError

from models.events import ProcessedEvent
from utils.logger import get_logger
from utils.retry import retry_with_backoff

logger = get_logger(__name__)

dynamodb = boto3.client("dynamodb")
TABLE_NAME = os.environ.get("AGGREGATIONS_TABLE_NAME", "heycloud-dev-aggregations")


def _get_time_window(timestamp_str: str) -> str:
    """Extract minute-level time window from ISO timestamp."""
    try:
        dt = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
        return f"minute#{dt.strftime('%H:%M')}"
    except (ValueError, AttributeError):
        now = datetime.now(timezone.utc)
        return f"minute#{now.strftime('%H:%M')}"


@retry_with_backoff(max_retries=3, retryable_exceptions=(ClientError,))
def _increment_counter(pk: str, sk: str, field: str, value: float = 1) -> None:
    """Atomically increment a counter in the aggregations table."""
    from datetime import timedelta
    ttl = int((datetime.now(timezone.utc) + timedelta(days=7)).timestamp())

    dynamodb.update_item(
        TableName=TABLE_NAME,
        Key={
            "PK": {"S": pk},
            "SK": {"S": sk},
        },
        UpdateExpression="ADD #field :val SET #ttl = if_not_exists(#ttl, :ttl)",
        ExpressionAttributeNames={
            "#field": field,
            "#ttl": "ttl",
        },
        ExpressionAttributeValues={
            ":val": {"N": str(value)},
            ":ttl": {"N": str(ttl)},
        },
    )


def aggregate_events(events: list[ProcessedEvent]) -> dict:
    """Compute and store aggregations for a batch of events.

    Returns:
        Dict with aggregation stats for logging.
    """
    type_counts: dict[str, int] = defaultdict(int)
    total_revenue = 0.0
    users_seen: set[str] = set()

    for event in events:
        date_str = event.date_str
        time_window = _get_time_window(event.timestamp)
        type_counts[event.event_type] += 1
        users_seen.add(event.user_id)

        # Per-type event count
        pk = f"event_count#{date_str}"
        _increment_counter(pk, time_window, event.event_type)

        # Revenue tracking for purchases
        if event.event_type == "PURCHASE":
            amount = event.payload.get("total_amount", 0)
            total_revenue += amount
            rev_pk = f"revenue#{date_str}"
            _increment_counter(rev_pk, time_window, "total_revenue", amount)

        # Payment success/failure tracking
        if event.event_type == "PAYMENT":
            status = event.payload.get("status", "unknown")
            pay_pk = f"payment_status#{date_str}"
            _increment_counter(pay_pk, time_window, status)

    # Active users (approximate — stored per minute window)
    if users_seen:
        now = datetime.now(timezone.utc)
        date_str = now.strftime("%Y-%m-%d")
        time_window = f"minute#{now.strftime('%H:%M')}"
        active_pk = f"active_users#{date_str}"
        _increment_counter(active_pk, time_window, "count", len(users_seen))

    return {
        "event_type_counts": dict(type_counts),
        "revenue": round(total_revenue, 2),
        "unique_users": len(users_seen),
    }
