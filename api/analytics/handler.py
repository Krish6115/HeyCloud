"""
HeyCloud Analytics API — Lambda Handler

Entry point for the API Gateway → Lambda proxy integration.
Terraform config: handler = "handler.lambda_handler"

Routes:
  GET /analytics/top-products?date=YYYY-MM-DD&limit=10
  GET /analytics/revenue?date=YYYY-MM-DD
  GET /analytics/active-users?date=YYYY-MM-DD
  GET /analytics/trends?date=YYYY-MM-DD
  GET /analytics/health

API Gateway proxy integration passes the full HTTP request as the event.
We parse the path and query parameters to route to the correct query module.
"""

import logging
import os
import sys
import time

from queries.top_products import get_top_products
from queries.revenue import get_revenue
from queries.active_users import get_active_users
from queries.trends import get_trends
from utils.response import success_response, error_response

# Configure structured logging
logger = logging.getLogger(__name__)
handler = logging.StreamHandler(sys.stdout)
logger.addHandler(handler)
logger.setLevel(os.environ.get("LOG_LEVEL", "INFO"))


def lambda_handler(event: dict, context) -> dict:
    """Route API Gateway proxy requests to the correct query handler.

    Args:
        event: API Gateway proxy event with path, httpMethod, queryStringParameters.
        context: Lambda runtime context.

    Returns:
        API Gateway proxy response with statusCode, headers, body.
    """
    start_time = time.time()

    path = event.get("path", "")
    method = event.get("httpMethod", "GET")
    params = event.get("queryStringParameters") or {}

    logger.info(f"Request: {method} {path} params={params}")

    # =========================================================================
    # Route handling
    # =========================================================================

    try:
        # Strip the /analytics prefix from the path
        route = path.replace("/analytics", "").strip("/")

        if route == "health":
            return success_response({
                "status": "healthy",
                "service": "analytics-api",
                "version": "1.0",
            })

        elif route == "top-products":
            date = params.get("date")
            limit = int(params.get("limit", "10"))
            data = get_top_products(date=date, limit=limit)
            return success_response(data)

        elif route == "revenue":
            date = params.get("date")
            data = get_revenue(date=date)
            return success_response(data)

        elif route == "active-users":
            date = params.get("date")
            data = get_active_users(date=date)
            return success_response(data)

        elif route == "trends":
            date = params.get("date")
            data = get_trends(date=date)
            return success_response(data)

        elif route == "summary":
            # Combined summary endpoint for dashboard
            date = params.get("date")
            data = {
                "top_products": get_top_products(date=date, limit=5),
                "revenue": get_revenue(date=date),
                "active_users": get_active_users(date=date),
                "trends": get_trends(date=date),
            }
            return success_response(data)

        else:
            return error_response(
                f"Unknown route: /analytics/{route}. "
                f"Available: top-products, revenue, active-users, trends, summary, health",
                status_code=404,
            )

    except ValueError as e:
        logger.error(f"Invalid parameter: {e}")
        return error_response(f"Invalid parameter: {e}", status_code=400)

    except Exception as e:
        duration_ms = round((time.time() - start_time) * 1000, 2)
        logger.error(f"Request failed after {duration_ms}ms: {e}", exc_info=True)
        return error_response(f"Internal server error: {str(e)}", status_code=500)
