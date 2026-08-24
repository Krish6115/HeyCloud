"""
Unit tests for the Analytics API handler routing.
"""

import json
import sys
import os

# Set environment before any imports
os.environ["EVENTS_TABLE_NAME"] = "test-events"
os.environ["AGGREGATIONS_TABLE_NAME"] = "test-aggregations"
os.environ["LOG_LEVEL"] = "WARNING"

_analytics_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "api", "analytics"))


def _load_handler():
    """Load the analytics handler module with correct path isolation."""
    # Ensure analytics path is first
    if _analytics_path in sys.path:
        sys.path.remove(_analytics_path)
    sys.path.insert(0, _analytics_path)

    # Clear any cached modules that collide
    for mod_name in list(sys.modules.keys()):
        if mod_name in ("handler", "utils", "utils.response", "queries",
                        "queries.top_products", "queries.revenue",
                        "queries.active_users", "queries.trends"):
            del sys.modules[mod_name]

    import handler
    return handler.lambda_handler


class TestAnalyticsHandler:
    def test_health_endpoint(self):
        handler = _load_handler()
        event = {
            "path": "/analytics/health",
            "httpMethod": "GET",
            "queryStringParameters": None,
        }
        response = handler(event, None)
        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert body["status"] == "healthy"

    def test_unknown_route_returns_404(self):
        handler = _load_handler()
        event = {
            "path": "/analytics/unknown-endpoint",
            "httpMethod": "GET",
            "queryStringParameters": None,
        }
        response = handler(event, None)
        assert response["statusCode"] == 404

    def test_cors_headers_present(self):
        handler = _load_handler()
        event = {
            "path": "/analytics/health",
            "httpMethod": "GET",
            "queryStringParameters": None,
        }
        response = handler(event, None)
        assert "Access-Control-Allow-Origin" in response["headers"]
        assert response["headers"]["Access-Control-Allow-Origin"] == "*"

    def test_top_products_route(self):
        # Load handler with correct path
        if _analytics_path in sys.path:
            sys.path.remove(_analytics_path)
        sys.path.insert(0, _analytics_path)

        for mod_name in list(sys.modules.keys()):
            if mod_name in ("handler", "utils", "utils.response", "queries",
                            "queries.top_products", "queries.revenue",
                            "queries.active_users", "queries.trends"):
                del sys.modules[mod_name]

        # Mock the top_products query before importing handler
        mock_data = [{"product_id": "prod_101", "views": 50, "purchases": 5, "score": 75}]

        import queries.top_products as tp_module
        original_fn = tp_module.get_top_products
        tp_module.get_top_products = lambda **kwargs: mock_data

        try:
            import handler as h
            event = {
                "path": "/analytics/top-products",
                "httpMethod": "GET",
                "queryStringParameters": {"date": "2026-05-20", "limit": "5"},
            }
            response = h.lambda_handler(event, None)
            assert response["statusCode"] == 200
            body = json.loads(response["body"])
            assert len(body) == 1
            assert body[0]["product_id"] == "prod_101"
        finally:
            tp_module.get_top_products = original_fn
