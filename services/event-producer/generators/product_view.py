"""PRODUCT_VIEW event generator — the highest-frequency event type."""

import random
from models.events import EventType, ProductViewPayload
from .base import BaseGenerator


class ProductViewGenerator(BaseGenerator):
    event_type = EventType.PRODUCT_VIEW

    def generate(self):
        payload = ProductViewPayload(
            product_id=self._random_product_id(),
            category=self._random_category(),
            price=self._random_price(),
            brand=self._random_brand(),
            view_duration_sec=random.randint(3, 300),
        )
        return self._build_event(payload.model_dump())
