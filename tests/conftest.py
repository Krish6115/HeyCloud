"""
Test fixtures and shared configuration for all tests.
"""

import pytest


@pytest.fixture
def sample_kinesis_event():
    """A realistic Kinesis event as received by the Lambda handler."""
    import base64
    import json

    event_data = {
        "event_id": "test-event-001",
        "event_type": "PRODUCT_VIEW",
        "timestamp": "2026-05-20T12:00:00+00:00",
        "source": "event-producer-v1",
        "version": "1.0",
        "metadata": {
            "region": "us-east-1",
            "platform": "web",
            "session_id": "sess-001",
            "user_agent": "HeyCloud-Test/1.0",
        },
        "user": {
            "user_id": "usr_1234",
            "age_group": "26-35",
            "membership": "premium",
        },
        "payload": {
            "product_id": "prod_101",
            "category": "Electronics",
            "price": 299.99,
            "brand": "TechPro",
            "view_duration_sec": 45,
        },
    }

    encoded = base64.b64encode(json.dumps(event_data).encode()).decode()

    return {
        "Records": [
            {
                "kinesis": {
                    "data": encoded,
                    "sequenceNumber": "seq-001",
                    "partitionKey": "PRODUCT_VIEW",
                },
                "eventSource": "aws:kinesis",
                "eventSourceARN": "arn:aws:kinesis:us-east-1:123456789012:stream/test",
            }
        ]
    }


@pytest.fixture
def sample_api_event():
    """A realistic API Gateway proxy event."""
    return {
        "path": "/analytics/top-products",
        "httpMethod": "GET",
        "queryStringParameters": {"date": "2026-05-20", "limit": "5"},
        "headers": {"Content-Type": "application/json"},
        "requestContext": {"stage": "dev"},
    }
