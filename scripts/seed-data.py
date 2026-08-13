"""
Seed script — generates sample events and writes them directly to DynamoDB/S3
for testing the analytics API and dashboard without requiring the full pipeline.

Usage: python scripts/seed-data.py [--count 100] [--date 2026-05-20]
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
import boto3
import decimal

# Add event producer to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "services", "event-producer"))

from generators import (
    ProductViewGenerator, CartEventGenerator, PurchaseGenerator,
    PaymentGenerator, UserLoginGenerator, SearchQueryGenerator,
)
from config import config

GENERATORS = {
    "PRODUCT_VIEW": ProductViewGenerator(),
    "SEARCH": SearchQueryGenerator(),
    "ADD_TO_CART": CartEventGenerator(),
    "USER_LOGIN": UserLoginGenerator(),
    "PURCHASE": PurchaseGenerator(),
    "PAYMENT": PaymentGenerator(),
}


def generate_sample_events(count: int) -> list[dict]:
    """Generate a batch of sample events."""
    import random

    events = []
    types = list(config.EVENT_WEIGHTS.keys())
    weights = list(config.EVENT_WEIGHTS.values())

    for _ in range(count):
        event_type = random.choices(types, weights=weights, k=1)[0]
        gen = GENERATORS[event_type]
        event = gen.generate()
        events.append(event.to_json_dict())

    return events


def main():
    parser = argparse.ArgumentParser(description="Seed sample events")
    parser.add_argument("--count", type=int, default=100, help="Number of events to generate")
    parser.add_argument("--output", type=str, default="sample_events.jsonl", help="Output file")
    parser.add_argument("--table", type=str, default="heycloud-dev-events", help="DynamoDB events table name")
    parser.add_argument("--agg-table", type=str, default="heycloud-dev-aggregations", help="DynamoDB aggregations table name")
    args = parser.parse_args()

    print(f"Generating {args.count} sample events...")
    events = generate_sample_events(args.count)

    with open(args.output, "w") as f:
        for event in events:
            f.write(json.dumps(event) + "\n")

    print(f"Written {len(events)} events to {args.output}")

    if args.table:
        print(f"Writing {len(events)} events to DynamoDB table {args.table}...")
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        table = dynamodb.Table(args.table)
        
        with table.batch_writer() as batch:
            for event in events:
                # Construct PK and SK for the events table
                dt = datetime.fromisoformat(event['timestamp'].replace('Z', '+00:00'))
                date_str = dt.strftime('%Y-%m-%d')
                event['PK'] = f"{event['event_type']}#{date_str}"
                event['SK'] = f"{event['timestamp']}#{event['event_id']}"
                
                # Extract attributes for GSI and queries
                if 'user' in event and 'user_id' in event['user']:
                    event['user_id'] = event['user']['user_id']
                if 'payload' in event and 'product_id' in event['payload']:
                    event['product_id'] = event['payload']['product_id']
                elif 'payload' in event and 'products' in event['payload'] and len(event['payload']['products']) > 0:
                    event['product_id'] = event['payload']['products'][0]['product_id']
                
                # Convert floats to Decimal for DynamoDB
                item = json.loads(json.dumps(event), parse_float=decimal.Decimal)
                batch.put_item(Item=item)
        print("Successfully written to Events DynamoDB.")

    if args.agg_table:
        print(f"Writing sample aggregations to DynamoDB table {args.agg_table}...")
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        agg_table = dynamodb.Table(args.agg_table)
        
        date_str = datetime.now(timezone.utc).strftime('%Y-%m-%d')
        
        with agg_table.batch_writer() as batch:
            for i in range(10, 20):
                # Sample revenue
                batch.put_item(Item={
                    'PK': f"revenue#{date_str}",
                    'SK': f"minute#14:{i}",
                    'total_revenue': decimal.Decimal(str(round(50.5 + i * 2, 2)))
                })
                # Sample active users
                batch.put_item(Item={
                    'PK': f"active_users#{date_str}",
                    'SK': f"minute#14:{i}",
                    'active_users': decimal.Decimal(str(10 + i))
                })
        print("Successfully written to Aggregations DynamoDB.")

    # Print type distribution
    type_counts = {}
    for e in events:
        t = e["event_type"]
        type_counts[t] = type_counts.get(t, 0) + 1

    print("\nEvent distribution:")
    for t, c in sorted(type_counts.items(), key=lambda x: -x[1]):
        print(f"  {t}: {c} ({c/len(events)*100:.0f}%)")


if __name__ == "__main__":
    main()
