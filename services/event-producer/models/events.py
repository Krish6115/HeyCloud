"""
Pydantic event models matching the DynamoDB schema exactly.

These models enforce the event envelope contract used across the entire pipeline:
  Producer → API Gateway → Kinesis → Lambda → DynamoDB/S3

Every event has a common envelope (event_id, event_type, timestamp, metadata, user)
with a type-specific payload. This guarantees schema consistency and enables
validation at both producer and consumer boundaries.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from uuid import uuid4

from pydantic import BaseModel, Field


# =============================================================================
# Enums
# =============================================================================

class EventType(str, Enum):
    PRODUCT_VIEW = "PRODUCT_VIEW"
    ADD_TO_CART = "ADD_TO_CART"
    PURCHASE = "PURCHASE"
    PAYMENT = "PAYMENT"
    USER_LOGIN = "USER_LOGIN"
    SEARCH = "SEARCH"


class Platform(str, Enum):
    WEB = "web"
    MOBILE = "mobile"
    TABLET = "tablet"


class Membership(str, Enum):
    FREE = "free"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"


class PaymentStatus(str, Enum):
    SUCCESS = "success"
    FAILED = "failed"
    PENDING = "pending"


# =============================================================================
# Nested Models
# =============================================================================

class EventMetadata(BaseModel):
    """Contextual metadata attached to every event."""
    region: str
    platform: Platform
    session_id: str = Field(default_factory=lambda: str(uuid4()))
    user_agent: str = "HeyCloud-Producer/1.0"


class UserInfo(BaseModel):
    """Anonymized user information."""
    user_id: str
    age_group: str
    membership: Membership


# =============================================================================
# Payload Models (event-type-specific)
# =============================================================================

class ProductViewPayload(BaseModel):
    product_id: str
    category: str
    price: float
    brand: str
    view_duration_sec: int


class AddToCartPayload(BaseModel):
    product_id: str
    category: str
    price: float
    quantity: int


class PurchaseItem(BaseModel):
    product_id: str
    category: str
    price: float
    quantity: int


class PurchasePayload(BaseModel):
    order_id: str
    products: list[PurchaseItem]
    total_amount: float
    currency: str = "USD"
    payment_method: str


class PaymentPayload(BaseModel):
    order_id: str
    payment_id: str
    status: PaymentStatus
    amount: float
    gateway: str


class UserLoginPayload(BaseModel):
    login_method: str
    success: bool
    ip_address: str


class SearchPayload(BaseModel):
    query: str
    results_count: int
    category_filter: Optional[str] = None
    sort_by: str = "relevance"


# =============================================================================
# Event Envelope
# =============================================================================

class StreamEvent(BaseModel):
    """
    Root event envelope sent to the API Gateway.

    This is the single schema contract between all services. The partition key
    for Kinesis is derived from event_type, ensuring all events of the same
    type land on the same shard for ordered processing.
    """
    event_id: str = Field(default_factory=lambda: str(uuid4()))
    event_type: EventType
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    source: str = "event-producer-v1"
    version: str = "1.0"
    metadata: EventMetadata
    user: UserInfo
    payload: dict  # Type-specific payload serialized as dict

    def to_json_dict(self) -> dict:
        """Serialize to a JSON-compatible dict for HTTP transmission."""
        return self.model_dump(mode="json")
