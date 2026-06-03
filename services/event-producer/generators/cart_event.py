"""ADD_TO_CART event generator."""

import random
from models.events import AddToCartPayload, EventType
from .base import BaseGenerator


class CartEventGenerator(BaseGenerator):
    event_type = EventType.ADD_TO_CART

    def generate(self):
        payload = AddToCartPayload(
            product_id=self._random_product_id(),
            category=self._random_category(),
            price=self._random_price(),
            quantity=random.randint(1, 5),
        )
        return self._build_event(payload.model_dump())
