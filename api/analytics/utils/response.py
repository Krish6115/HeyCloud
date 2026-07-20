"""
Standard API response builder for the Analytics API.

Ensures consistent response format with CORS headers across all endpoints.
"""

import json
from typing import Any


def success_response(data: Any, status_code: int = 200) -> dict:
    """Build a successful API Gateway proxy response."""
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type,X-Api-Key",
            "Access-Control-Allow-Methods": "GET,OPTIONS",
        },
        "body": json.dumps(data, default=str),
    }


def error_response(message: str, status_code: int = 500) -> dict:
    """Build an error API Gateway proxy response."""
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
        "body": json.dumps({"error": message}),
    }
