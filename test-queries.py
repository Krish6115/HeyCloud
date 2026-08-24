import os
import sys

# Set environment variables for the queries to use the correct tables
os.environ['EVENTS_TABLE_NAME'] = 'heycloud-dev-events'
os.environ['AGGREGATIONS_TABLE_NAME'] = 'heycloud-dev-aggregations'

# Add API to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "api", "analytics")))

from queries.top_products import get_top_products
from queries.revenue import get_revenue

print("Testing get_top_products()...")
try:
    products = get_top_products()
    print("Top Products Result:")
    for p in products:
        print(f"  {p}")
except Exception as e:
    print(f"Error: {e}")

print("\nTesting get_revenue()...")
try:
    revenue = get_revenue()
    print("Revenue Result:")
    print(f"  Date: {revenue['date']}")
    print(f"  Total Revenue: {revenue['total_revenue']}")
    print("  Timeline (first 5):", revenue['timeline'][:5])
except Exception as e:
    print(f"Error: {e}")
