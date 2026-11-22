"""Local end-to-end check (no AWS account needed).

Generates real producer events, wraps them as an SQS batch (the shape
API Gateway /events -> SQS -> Lambda delivers), runs the stream processor,
then queries the analytics API — all against moto-mocked DynamoDB/S3.

    pip install "moto[dynamodb,s3,cloudwatch]"
    python scripts/local-e2e.py
"""

import importlib
import json
import os
import sys

os.environ.update({
    "AWS_DEFAULT_REGION": "us-east-1", "AWS_ACCESS_KEY_ID": "test",
    "AWS_SECRET_ACCESS_KEY": "test", "EVENTS_TABLE_NAME": "e2e-events",
    "AGGREGATIONS_TABLE_NAME": "e2e-aggregations", "DATA_LAKE_BUCKET": "e2e-lake",
    "LOG_LEVEL": "WARNING", "PRODUCER_LOG_LEVEL": "WARNING",
})

import boto3  # noqa: E402
from moto import mock_aws  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load(pkg_dir):
    """Import a service's top-level modules in isolation (they share names)."""
    for m in [m for m in sys.modules if m.split(".")[0] in
              ("handler", "config", "generators", "models", "utils",
               "processors", "storage", "queries")]:
        del sys.modules[m]
    sys.path.insert(0, os.path.join(ROOT, pkg_dir))


def make_table(ddb, name, gsis=False):
    kw = {}
    attrs = [{"AttributeName": "PK", "AttributeType": "S"},
             {"AttributeName": "SK", "AttributeType": "S"}]
    if gsis:
        attrs += [{"AttributeName": "user_id", "AttributeType": "S"},
                  {"AttributeName": "product_id", "AttributeType": "S"}]
        kw["GlobalSecondaryIndexes"] = [
            {"IndexName": n, "KeySchema": [{"AttributeName": h, "KeyType": "HASH"},
                                           {"AttributeName": "SK", "KeyType": "RANGE"}],
             "Projection": {"ProjectionType": "ALL"}}
            for n, h in (("UserIndex", "user_id"), ("ProductIndex", "product_id"))]
    ddb.create_table(TableName=name, BillingMode="PAY_PER_REQUEST",
                     KeySchema=[{"AttributeName": "PK", "KeyType": "HASH"},
                                {"AttributeName": "SK", "KeyType": "RANGE"}],
                     AttributeDefinitions=attrs, **kw)


@mock_aws
def main(n=200):
    ddb = boto3.client("dynamodb")
    make_table(ddb, "e2e-events", gsis=True)
    make_table(ddb, "e2e-aggregations")
    boto3.client("s3").create_bucket(Bucket="e2e-lake")

    # 1. Producer
    load("services/event-producer")
    producer = importlib.import_module("main")
    events = [producer.GENERATORS[producer._pick_event_type()].generate().to_json_dict()
              for _ in range(n)]
    print(f"[1] generated {len(events)} events")

    # 2. Stream processor (SQS batch of 100, like the event source mapping)
    sys.path.pop(0)
    load("services/stream-processor")
    sp = importlib.import_module("handler")
    processed = 0
    for i in range(0, n, 100):
        batch = {"Records": [{"messageId": str(j), "body": json.dumps(e), "eventSource": "aws:sqs"}
                             for j, e in enumerate(events[i:i + 100])]}
        r = sp.lambda_handler(batch, None)
        processed += r["processed"]
        assert r["invalid"] == 0, r
    print(f"[2] stream processor stored {processed} events, "
          f"s3 objects={boto3.client('s3').list_objects_v2(Bucket='e2e-lake').get('KeyCount', 0)}")
    assert processed == n

    # 3. Analytics API
    sys.path.pop(0)
    load("api/analytics")
    api = importlib.import_module("handler")
    for route in ("health", "summary", "top-products", "revenue", "active-users", "trends"):
        resp = api.lambda_handler({"path": f"/analytics/{route}", "httpMethod": "GET",
                                   "queryStringParameters": None}, None)
        body = json.loads(resp["body"])
        print(f"[3] /analytics/{route:<13} -> {resp['statusCode']} "
              f"{json.dumps(body)[:110]}")
        assert resp["statusCode"] == 200, body
    print("LOCAL END-TO-END PASSED")


if __name__ == "__main__":
    main()
