"""
Trends analytics — reads event counts from the aggregations table.

Returns per-type event count time-series for trend visualization.
"""

import os
from collections import defaultdict
from datetime import datetime, timezone

import boto3

AGG_TABLE = os.environ.get("AGGREGATIONS_TABLE_NAME", "heycloud-dev-aggregations")
dynamodb = boto3.client("dynamodb")

EVENT_TYPES = ["PRODUCT_VIEW", "ADD_TO_CART", "PURCHASE", "PAYMENT", "USER_LOGIN", "SEARCH"]


def get_trends(date: str = None) -> dict:
    """Get event count trends by type for a given date.

    Args:
        date: Date string YYYY-MM-DD (defaults to today).

    Returns:
        {"date": str, "totals": {type: count}, "timeline": {type: [{time, count}]}}
    """
    if not date:
        date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    pk = f"event_count#{date}"

    try:
        response = dynamodb.query(
            TableName=AGG_TABLE,
            KeyConditionExpression="PK = :pk",
            ExpressionAttributeValues={":pk": {"S": pk}},
        )
    except Exception:
        return {"date": date, "totals": {}, "timeline": {}}

    totals: dict[str, int] = defaultdict(int)
    timeline: dict[str, list] = defaultdict(list)

    for item in response.get("Items", []):
        sk = item.get("SK", {}).get("S", "")
        time_str = sk.replace("minute#", "")

        for event_type in EVENT_TYPES:
            count = int(item.get(event_type, {}).get("N", "0"))
            if count > 0:
                totals[event_type] += count
                timeline[event_type].append({"time": time_str, "count": count})

    # Sort timelines
    for et in timeline:
        timeline[et].sort(key=lambda x: x["time"])

    return {
        "date": date,
        "totals": dict(totals),
        "timeline": dict(timeline),
    }
