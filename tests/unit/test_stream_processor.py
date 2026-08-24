"""
Unit tests for the Stream Processor — transform logic and event models.

Tests decoding, validation, and DynamoDB key construction
WITHOUT hitting real AWS services.

NOTE: The stream-processor has its own models.events module that conflicts
with the event-producer's models.events. We use importlib to isolate imports.
"""

import base64
import json
import importlib
import importlib.util
import sys
import os


def _import_from_path(module_name, file_path):
    """Import a module from an absolute file path, bypassing sys.path cache."""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# Resolve paths
_sp_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "services", "stream-processor"))

# Import stream-processor modules explicitly by file path
_events_mod = _import_from_path(
    "sp_models_events",
    os.path.join(_sp_root, "models", "events.py"),
)
ProcessedEvent = _events_mod.ProcessedEvent

# For transform, we need the stream-processor on sys.path temporarily
_saved_path = sys.path.copy()
# Remove any event-producer paths
sys.path = [p for p in sys.path if "event-producer" not in p]
sys.path.insert(0, _sp_root)

# Clear any cached models module
if "models" in sys.modules:
    del sys.modules["models"]
if "models.events" in sys.modules:
    del sys.modules["models.events"]

from processors.transform import transform_record, validate_event  # noqa: E402

# Restore sys.path
sys.path = _saved_path


def _make_kinesis_record(event_data: dict) -> dict:
    """Helper: encode event data as a mock Kinesis record."""
    encoded = base64.b64encode(json.dumps(event_data).encode()).decode()
    return {
        "kinesis": {
            "data": encoded,
            "sequenceNumber": "seq-001",
            "partitionKey": "test",
        }
    }


class TestValidateEvent:
    def test_valid_event_passes(self):
        event = {
            "event_id": "e-001",
            "event_type": "PRODUCT_VIEW",
            "timestamp": "2026-05-20T12:00:00Z",
        }
        assert validate_event(event) is True

    def test_missing_event_id_fails(self):
        event = {"event_type": "PRODUCT_VIEW", "timestamp": "2026-05-20T12:00:00Z"}
        assert validate_event(event) is False

    def test_invalid_event_type_fails(self):
        event = {
            "event_id": "e-001",
            "event_type": "INVALID_TYPE",
            "timestamp": "2026-05-20T12:00:00Z",
        }
        assert validate_event(event) is False


class TestTransformRecord:
    def test_valid_record_returns_processed_event(self):
        event_data = {
            "event_id": "e-001",
            "event_type": "PRODUCT_VIEW",
            "timestamp": "2026-05-20T12:00:00+00:00",
            "source": "test",
            "version": "1.0",
            "metadata": {"region": "us-east-1", "platform": "web"},
            "user": {"user_id": "usr_123", "age_group": "26-35", "membership": "free"},
            "payload": {"product_id": "prod_101", "category": "Electronics", "price": 99.99},
        }

        record = _make_kinesis_record(event_data)
        result = transform_record(record)

        assert result is not None
        assert result.event_id == "e-001"
        assert result.event_type == "PRODUCT_VIEW"

    def test_invalid_json_returns_none(self):
        encoded = base64.b64encode(b"not-json").decode()
        record = {"kinesis": {"data": encoded}}
        assert transform_record(record) is None

    def test_missing_required_fields_returns_none(self):
        event_data = {"event_type": "PURCHASE"}  # missing event_id, timestamp
        record = _make_kinesis_record(event_data)
        assert transform_record(record) is None


class TestProcessedEvent:
    def test_pk_construction(self):
        event = ProcessedEvent({
            "event_id": "e-001",
            "event_type": "PURCHASE",
            "timestamp": "2026-05-20T12:00:00+00:00",
            "user": {"user_id": "usr_123"},
            "payload": {"product_id": "prod_101"},
        })
        assert event.pk == "PURCHASE#2026-05-20"
        assert event.sk == "2026-05-20T12:00:00+00:00#e-001"

    def test_dynamodb_item_has_required_keys(self):
        event = ProcessedEvent({
            "event_id": "e-001",
            "event_type": "PRODUCT_VIEW",
            "timestamp": "2026-05-20T12:00:00+00:00",
            "metadata": {"region": "us-east-1", "platform": "web"},
            "user": {"user_id": "usr_123", "age_group": "26-35", "membership": "free"},
            "payload": {"product_id": "prod_101"},
        })
        item = event.to_dynamodb_item()
        assert "PK" in item
        assert "SK" in item
        assert "user_id" in item
        assert "product_id" in item
        assert "ttl" in item

    def test_s3_key_format(self):
        event = ProcessedEvent({
            "event_id": "e-001",
            "event_type": "PURCHASE",
            "timestamp": "2026-05-20T12:00:00+00:00",
        })
        assert event.s3_key == "raw/2026/05/20/PURCHASE/e-001.json"
