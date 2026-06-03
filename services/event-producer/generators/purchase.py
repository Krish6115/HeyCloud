"""PURCHASE event generator — creates orders with multiple products."""

import random
from uuid import uuid4

from models.events import EventType, PurchaseItem, PurchasePayload
from config import config
from .base import BaseGenerator


class PurchaseGenerator(BaseGenerator):
    event_type = EventType.PURCHASE

    def generate(self):
        num_items = random.randint(1, 5)
        products = []
        total = 0.0

        for _ in range(num_items):
            price = self._random_price(10.0, 300.0)
            qty = random.randint(1, 3)
            products.append(PurchaseItem(
                product_id=self._random_product_id(),
                category=self._random_category(),
                price=price,
                quantity=qty,
            ))
            total += price * qty

        payload = PurchasePayload(
            order_id=f"ord_{uuid4().hex[:12]}",
            products=products,
            total_amount=round(total, 2),
            currency=random.choice(["USD", "EUR", "INR"]),
            payment_method=random.choice(config.PAYMENT_METHODS),
        )
        return self._build_event(payload.model_dump())
