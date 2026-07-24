"""
Revenue analytics — reads from the aggregations table.

Returns per-minute revenue data for time-series charts.
"""

import os
from datetime import datetime, timezone

import boto3

AGG_TABLE = os.environ.get("AGGREGATIONS_TABLE_NAME", "heycloud-dev-aggregations")
dynamodb = boto3.client("dynamodb")


def get_revenue(date: str = None) -> dict:
    """Get revenue time-series for a given date.

    Args:
        date: Date string YYYY-MM-DD (defaults to today).

    Returns:
        {"date": str, "total_revenue": float, "timeline": [{"time": str, "revenue": float}]}
    """
    if not date:
        date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    pk = f"revenue#{date}"

    try:
        response = dynamodb.query(
            TableName=AGG_TABLE,
            KeyConditionExpression="PK = :pk",
            ExpressionAttributeValues={":pk": {"S": pk}},
        )
    except Exception:
        return {"date": date, "total_revenue": 0, "timeline": []}

    timeline = []
    total = 0.0

    for item in response.get("Items", []):
        sk = item.get("SK", {}).get("S", "")
        rev = float(item.get("total_revenue", {}).get("N", "0"))
        total += rev

        time_str = sk.replace("minute#", "")
        timeline.append({"time": time_str, "revenue": round(rev, 2)})

    timeline.sort(key=lambda x: x["time"])

    return {
        "date": date,
        "total_revenue": round(total, 2),
        "timeline": timeline,
    }
