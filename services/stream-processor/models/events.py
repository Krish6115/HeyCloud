"""
Event models for the stream processor (consumer side).

Mirrors the producer models but focused on deserialization and
DynamoDB key construction. The PK/SK patterns here MUST match
the DynamoDB table schema defined in Terraform.
"""

from datetime import datetime, timezone, timedelta


class ProcessedEvent:
    """Wraps a raw event dict with DynamoDB key construction logic."""

    def __init__(self, raw_event: dict):
        self.raw = raw_event
        self.event_id = raw_event.get("event_id", "unknown")
        self.event_type = raw_event.get("event_type", "UNKNOWN")
        self.timestamp = raw_event.get("timestamp", datetime.now(timezone.utc).isoformat())
        self.source = raw_event.get("source", "unknown")
        self.version = raw_event.get("version", "1.0")
        self.metadata = raw_event.get("metadata", {})
        self.user = raw_event.get("user", {})
        self.payload = raw_event.get("payload", {})

    @property
    def date_str(self) -> str:
        """Extract YYYY-MM-DD from the ISO timestamp."""
        try:
            dt = datetime.fromisoformat(self.timestamp.replace("Z", "+00:00"))
            return dt.strftime("%Y-%m-%d")
        except (ValueError, AttributeError):
            return datetime.now(timezone.utc).strftime("%Y-%m-%d")

    @property
    def pk(self) -> str:
        """DynamoDB PK: event_type#YYYY-MM-DD"""
        return f"{self.event_type}#{self.date_str}"

    @property
    def sk(self) -> str:
        """DynamoDB SK: timestamp#event_id"""
        return f"{self.timestamp}#{self.event_id}"

    @property
    def user_id(self) -> str:
        return self.user.get("user_id", "anonymous")

    @property
    def product_id(self) -> str:
        return self.payload.get("product_id", "none")

    @property
    def ttl_epoch(self) -> int:
        """TTL value: 7 days from now as epoch seconds."""
        return int((datetime.now(timezone.utc) + timedelta(days=7)).timestamp())

    def to_dynamodb_item(self) -> dict:
        """Convert to a DynamoDB item matching the table schema."""
        item = {
            "PK": {"S": self.pk},
            "SK": {"S": self.sk},
            "event_id": {"S": self.event_id},
            "event_type": {"S": self.event_type},
            "timestamp": {"S": self.timestamp},
            "source": {"S": self.source},
            "user_id": {"S": self.user_id},
            "product_id": {"S": self.product_id},
            "ttl": {"N": str(self.ttl_epoch)},
        }

        # Flatten user fields
        if self.user:
            item["age_group"] = {"S": self.user.get("age_group", "unknown")}
            item["membership"] = {"S": self.user.get("membership", "free")}

        # Flatten metadata
        if self.metadata:
            item["region"] = {"S": self.metadata.get("region", "unknown")}
            item["platform"] = {"S": self.metadata.get("platform", "unknown")}

        # Store full payload as JSON string
        import json
        item["payload"] = {"S": json.dumps(self.payload)}

        return item

    def to_s3_record(self) -> dict:
        """Return the full event dict for S3 archival (JSONL format)."""
        return self.raw

    @property
    def s3_key(self) -> str:
        """S3 object key: raw/YYYY/MM/DD/event_type/event_id.json"""
        try:
            dt = datetime.fromisoformat(self.timestamp.replace("Z", "+00:00"))
            return (
                f"raw/{dt.strftime('%Y/%m/%d')}/{self.event_type}/"
                f"{self.event_id}.json"
            )
        except (ValueError, AttributeError):
            now = datetime.now(timezone.utc)
            return f"raw/{now.strftime('%Y/%m/%d')}/{self.event_type}/{self.event_id}.json"
