"""
Configuration management for the Event Producer service.

Loads settings from environment variables with sensible defaults.
All configuration is externalized — no hardcoded values.
"""

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Centralized configuration loaded from environment variables."""

    # API Gateway endpoint
    API_GATEWAY_URL: str = os.getenv("API_GATEWAY_URL", "https://khqqp05h57.execute-api.us-east-1.amazonaws.com/dev")
    API_KEY: str = os.getenv("API_KEY", "")

    # Producer tuning
    EVENTS_PER_SECOND: int = int(os.getenv("EVENTS_PER_SECOND", "10"))
    BATCH_SIZE: int = int(os.getenv("BATCH_SIZE", "25"))

    # Retry configuration
    MAX_RETRIES: int = int(os.getenv("MAX_RETRIES", "3"))
    RETRY_BACKOFF_FACTOR: float = float(os.getenv("RETRY_BACKOFF_FACTOR", "0.5"))
    REQUEST_TIMEOUT: int = int(os.getenv("REQUEST_TIMEOUT", "10"))

    # Logging
    LOG_LEVEL: str = os.getenv("PRODUCER_LOG_LEVEL", "INFO").upper()

    # Event generation weights (probability distribution)
    EVENT_WEIGHTS: dict = {
        "PRODUCT_VIEW": 0.35,
        "SEARCH": 0.20,
        "ADD_TO_CART": 0.18,
        "USER_LOGIN": 0.12,
        "PURCHASE": 0.10,
        "PAYMENT": 0.05,
    }

    # Simulation parameters
    REGIONS: list = ["us-east-1", "us-west-2", "eu-west-1", "ap-south-1", "ap-southeast-1"]
    PLATFORMS: list = ["web", "mobile", "tablet"]
    CATEGORIES: list = [
        "Electronics", "Fashion", "Home & Kitchen", "Books",
        "Sports", "Beauty", "Toys", "Grocery", "Automotive",
    ]
    BRANDS: list = [
        "TechPro", "StyleCraft", "HomeEssentials", "BookWorld",
        "FitGear", "GlowUp", "KidZone", "FreshMart", "AutoElite",
    ]
    PAYMENT_METHODS: list = ["credit_card", "debit_card", "upi", "net_banking", "wallet"]
    PAYMENT_GATEWAYS: list = ["stripe", "razorpay", "paypal", "adyen"]
    LOGIN_METHODS: list = ["email", "google", "github", "facebook"]


config = Config()
