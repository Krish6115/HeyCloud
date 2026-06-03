"""
Base event generator with shared logic for all event types.

Uses Faker for realistic data and provides common methods for
generating user info, metadata, product IDs, etc.
"""

import random
from abc import ABC, abstractmethod

from faker import Faker

from models.events import (
    EventMetadata, EventType, Membership, Platform, StreamEvent, UserInfo,
)
from config import config

fake = Faker()
Faker.seed(42)  # Reproducible in tests, overridden in production


class BaseGenerator(ABC):
    """Abstract base for all event generators."""

    event_type: EventType

    def _random_user(self) -> UserInfo:
        """Generate a realistic user profile."""
        return UserInfo(
            user_id=f"usr_{random.randint(1000, 9999)}",
            age_group=random.choice(["18-25", "26-35", "36-50", "50+"]),
            membership=random.choice(list(Membership)),
        )

    def _random_metadata(self) -> EventMetadata:
        """Generate contextual metadata."""
        return EventMetadata(
            region=random.choice(config.REGIONS),
            platform=random.choice(list(Platform)),
        )

    def _random_product_id(self) -> str:
        return f"prod_{random.randint(100, 999)}"

    def _random_category(self) -> str:
        return random.choice(config.CATEGORIES)

    def _random_brand(self) -> str:
        return random.choice(config.BRANDS)

    def _random_price(self, min_val: float = 5.0, max_val: float = 500.0) -> float:
        return round(random.uniform(min_val, max_val), 2)

    def _build_event(self, payload: dict) -> StreamEvent:
        """Wrap a payload in the standard event envelope."""
        return StreamEvent(
            event_type=self.event_type,
            metadata=self._random_metadata(),
            user=self._random_user(),
            payload=payload,
        )

    @abstractmethod
    def generate(self) -> StreamEvent:
        """Generate a single event. Implemented by subclasses."""
        ...
