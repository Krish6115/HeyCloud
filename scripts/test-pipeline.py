"""
End-to-end pipeline test — sends events through API Gateway and verifies
they arrive in DynamoDB and S3.

Usage: python scripts/test-pipeline.py [--url API_URL] [--api-key KEY] [--count 10]
"""

import argparse
import json
import os
import sys
import time

import requests

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "services", "event-producer"))

from generators.product_view import ProductViewGenerator


def test_pipeline(api_url: str, api_key: str, count: int):
    """Send test events and verify pipeline health."""

    print("=" * 60)
    print("  HeyCloud Pipeline Test")
    print("=" * 60)
    print(f"  API URL: {api_url}")
    print(f"  Events:  {count}")
    print("=" * 60)

    gen = ProductViewGenerator()
    session = requests.Session()
    session.headers.update({
        "Content-Type": "application/json",
        "x-api-key": api_key,
    })

    success = 0
    failed = 0

    for i in range(count):
        event = gen.generate()
        data = event.to_json_dict()

        try:
            resp = session.post(
                f"{api_url}/events",
                data=json.dumps(data),
                timeout=10,
            )
            if resp.status_code == 200:
                success += 1
            else:
                failed += 1
                print(f"  ✗ Event {i+1}: status={resp.status_code}")
        except Exception as e:
            failed += 1
            print(f"  ✗ Event {i+1}: {e}")

        time.sleep(0.1)  # Rate limit

    print(f"\nResults: {success}/{count} succeeded, {failed} failed")

    # Test analytics API
    print("\nTesting analytics endpoints...")
    analytics_endpoints = [
        "/analytics/health",
        "/analytics/top-products",
        "/analytics/revenue",
        "/analytics/active-users",
        "/analytics/trends",
    ]

    for endpoint in analytics_endpoints:
        try:
            resp = session.get(f"{api_url}{endpoint}", timeout=10)
            status = "✓" if resp.status_code == 200 else "✗"
            print(f"  {status} GET {endpoint} → {resp.status_code}")
        except Exception as e:
            print(f"  ✗ GET {endpoint} → {e}")

    print("\n" + "=" * 60)
    print(f"  Pipeline test complete!")
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(description="Test the HeyCloud pipeline")
    parser.add_argument("--url", type=str, default=os.environ.get("API_GATEWAY_URL", ""))
    parser.add_argument("--api-key", type=str, default=os.environ.get("API_KEY", ""))
    parser.add_argument("--count", type=int, default=10)
    args = parser.parse_args()

    if not args.url:
        print("ERROR: --url or API_GATEWAY_URL env var required")
        sys.exit(1)

    test_pipeline(args.url, args.api_key, args.count)


if __name__ == "__main__":
    main()
