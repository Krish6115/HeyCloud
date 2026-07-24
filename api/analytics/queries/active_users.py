"""
Active users analytics — reads from the aggregations table.

Returns per-minute active user counts for dashboard widgets.
"""

import os
from datetime import datetime, timezone

import boto3

AGG_TABLE = os.environ.get("AGGREGATIONS_TABLE_NAME", "heycloud-dev-aggregations")
dynamodb = boto3.client("dynamodb")


def get_active_users(date: str = None) -> dict:
    """Get active user counts over time for a given date.

    Args:
        date: Date string YYYY-MM-DD (defaults to today).

    Returns:
        {"date": str, "peak_users": int, "timeline": [{"time": str, "count": int}]}
    """
    if not date:
        date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    pk = f"active_users#{date}"

    try:
        response = dynamodb.query(
            TableName=AGG_TABLE,
            KeyConditionExpression="PK = :pk",
            ExpressionAttributeValues={":pk": {"S": pk}},
        )
    except Exception:
        return {"date": date, "peak_users": 0, "timeline": []}

    timeline = []
    peak = 0

    for item in response.get("Items", []):
        sk = item.get("SK", {}).get("S", "")
        count = int(item.get("count", {}).get("N", "0"))
        peak = max(peak, count)

        time_str = sk.replace("minute#", "")
        timeline.append({"time": time_str, "count": count})

    timeline.sort(key=lambda x: x["time"])

    return {
        "date": date,
        "peak_users": peak,
        "timeline": timeline,
    }
