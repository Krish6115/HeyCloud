"""USER_LOGIN event generator."""

import random
from models.events import EventType, UserLoginPayload
from config import config
from .base import BaseGenerator, fake


class UserLoginGenerator(BaseGenerator):
    event_type = EventType.USER_LOGIN

    def generate(self):
        payload = UserLoginPayload(
            login_method=random.choice(config.LOGIN_METHODS),
            success=random.random() < 0.92,  # 92% success rate
            ip_address=fake.ipv4_public(),
        )
        return self._build_event(payload.model_dump())
