"""
Unit tests for the Event Producer generators.

Tests that each generator produces valid events matching the expected schema.
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "services", "event-producer"))

from models.events import EventType, StreamEvent
from generators.product_view import ProductViewGenerator
from generators.cart_event import CartEventGenerator
from generators.purchase import PurchaseGenerator
from generators.payment import PaymentGenerator
from generators.user_login import UserLoginGenerator
from generators.search_query import SearchQueryGenerator


class TestProductViewGenerator:
    def test_generates_valid_event(self):
        gen = ProductViewGenerator()
        event = gen.generate()
        assert isinstance(event, StreamEvent)
        assert event.event_type == EventType.PRODUCT_VIEW

    def test_payload_has_required_fields(self):
        gen = ProductViewGenerator()
        event = gen.generate()
        payload = event.payload
        assert "product_id" in payload
        assert "category" in payload
        assert "price" in payload
        assert "brand" in payload
        assert "view_duration_sec" in payload

    def test_price_is_positive(self):
        gen = ProductViewGenerator()
        for _ in range(20):
            event = gen.generate()
            assert event.payload["price"] > 0


class TestCartEventGenerator:
    def test_generates_valid_event(self):
        gen = CartEventGenerator()
        event = gen.generate()
        assert event.event_type == EventType.ADD_TO_CART
        assert "quantity" in event.payload
        assert event.payload["quantity"] >= 1


class TestPurchaseGenerator:
    def test_generates_valid_event(self):
        gen = PurchaseGenerator()
        event = gen.generate()
        assert event.event_type == EventType.PURCHASE
        assert "order_id" in event.payload
        assert "products" in event.payload
        assert "total_amount" in event.payload
        assert len(event.payload["products"]) >= 1

    def test_total_amount_is_positive(self):
        gen = PurchaseGenerator()
        for _ in range(20):
            event = gen.generate()
            assert event.payload["total_amount"] > 0


class TestPaymentGenerator:
    def test_generates_valid_event(self):
        gen = PaymentGenerator()
        event = gen.generate()
        assert event.event_type == EventType.PAYMENT
        assert "payment_id" in event.payload
        assert event.payload["status"] in ("success", "failed", "pending")


class TestUserLoginGenerator:
    def test_generates_valid_event(self):
        gen = UserLoginGenerator()
        event = gen.generate()
        assert event.event_type == EventType.USER_LOGIN
        assert "login_method" in event.payload
        assert isinstance(event.payload["success"], bool)


class TestSearchQueryGenerator:
    def test_generates_valid_event(self):
        gen = SearchQueryGenerator()
        event = gen.generate()
        assert event.event_type == EventType.SEARCH
        assert "query" in event.payload
        assert "results_count" in event.payload


class TestStreamEventEnvelope:
    def test_to_json_dict(self):
        gen = ProductViewGenerator()
        event = gen.generate()
        d = event.to_json_dict()
        assert isinstance(d, dict)
        assert "event_id" in d
        assert "event_type" in d
        assert "timestamp" in d
        assert "metadata" in d
        assert "user" in d
        assert "payload" in d

    def test_event_id_is_uuid(self):
        gen = ProductViewGenerator()
        event = gen.generate()
        assert len(event.event_id) == 36  # UUID format
