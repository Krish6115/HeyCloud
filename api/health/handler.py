"""
Health check Lambda — simple ping endpoint.

Returns service status for uptime monitoring.
"""

import json


def lambda_handler(event: dict, context) -> dict:
    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
        "body": json.dumps({
            "status": "healthy",
            "service": "heycloud",
            "version": "1.0",
        }),
    }
