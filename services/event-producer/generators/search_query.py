"""SEARCH event generator."""

import random
from models.events import EventType, SearchPayload
from config import config
from .base import BaseGenerator


class SearchQueryGenerator(BaseGenerator):
    event_type = EventType.SEARCH

    # Realistic e-commerce search queries
    SEARCH_QUERIES = [
        "wireless headphones", "running shoes", "laptop stand",
        "protein powder", "yoga mat", "mechanical keyboard",
        "smart watch", "air purifier", "gaming mouse",
        "backpack", "water bottle", "desk lamp",
        "phone case", "bluetooth speaker", "office chair",
        "face wash", "sunscreen", "power bank",
        "usb hub", "monitor arm", "webcam hd",
    ]

    def generate(self):
        payload = SearchPayload(
            query=random.choice(self.SEARCH_QUERIES),
            results_count=random.randint(0, 500),
            category_filter=random.choice([None] + config.CATEGORIES),
            sort_by=random.choice(["relevance", "price_low", "price_high", "rating", "newest"]),
        )
        return self._build_event(payload.model_dump())
