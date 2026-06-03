"""PAYMENT event generator — success/failure/pending outcomes."""

import random
from uuid import uuid4

from models.events import EventType, PaymentPayload, PaymentStatus
from config import config
from .base import BaseGenerator


class PaymentGenerator(BaseGenerator):
    event_type = EventType.PAYMENT

    def generate(self):
        # 85% success, 10% failed, 5% pending — realistic distribution
        status = random.choices(
            list(PaymentStatus),
            weights=[0.85, 0.10, 0.05],
            k=1,
        )[0]

        payload = PaymentPayload(
            order_id=f"ord_{uuid4().hex[:12]}",
            payment_id=f"pay_{uuid4().hex[:12]}",
            status=status,
            amount=self._random_price(20.0, 1000.0),
            gateway=random.choice(config.PAYMENT_GATEWAYS),
        )
        return self._build_event(payload.model_dump())
