"""
Top Products query — reads from DynamoDB ProductIndex GSI.

Returns the most viewed/purchased products for a given date.
"""

import os
from collections import Counter
from datetime import datetime, timezone

import boto3

EVENTS_TABLE = os.environ.get("EVENTS_TABLE_NAME", "heycloud-dev-events")
dynamodb = boto3.client("dynamodb")


def get_top_products(date: str = None, limit: int = 10) -> list[dict]:
    """Get top products by event count for a given date.

    Queries the events table filtering by PRODUCT_VIEW and PURCHASE events,
    then aggregates by product_id.

    Args:
        date: Date string YYYY-MM-DD (defaults to today).
        limit: Number of top products to return.

    Returns:
        List of {"product_id": str, "views": int, "purchases": int} dicts.
    """
    if not date:
        date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    product_counts: Counter = Counter()
    purchase_counts: Counter = Counter()

    # Query product views for the date
    for event_type, counter in [("PRODUCT_VIEW", product_counts), ("PURCHASE", purchase_counts)]:
        pk = f"{event_type}#{date}"

        try:
            response = dynamodb.query(
                TableName=EVENTS_TABLE,
                KeyConditionExpression="PK = :pk",
                ExpressionAttributeValues={":pk": {"S": pk}},
                ProjectionExpression="product_id",
                Limit=1000,  # Cap for cost control
            )

            for item in response.get("Items", []):
                pid = item.get("product_id", {}).get("S", "unknown")
                if pid != "none":
                    counter[pid] += 1

        except Exception:
            pass  # Gracefully degrade if query fails

    # Combine views and purchases, sort by total activity
    all_products = set(product_counts.keys()) | set(purchase_counts.keys())
    results = []

    for pid in all_products:
        results.append({
            "product_id": pid,
            "views": product_counts.get(pid, 0),
            "purchases": purchase_counts.get(pid, 0),
            "score": product_counts.get(pid, 0) + purchase_counts.get(pid, 0) * 5,
        })

    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:limit]
