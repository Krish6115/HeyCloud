"""
Custom CloudWatch metrics publisher.

Why custom metrics:
  - Built-in Lambda metrics only track invocations/errors/duration
  - We need business metrics: events_processed, events_by_type, processing_latency
  - Custom metrics enable CloudWatch Alarms on business conditions
  - Namespace isolation per environment prevents metric collision
"""

import os
import time
from typing import Optional

import boto3

from utils.logger import get_logger

logger = get_logger(__name__)

cloudwatch = boto3.client("cloudwatch")

NAMESPACE = os.environ.get("METRICS_NAMESPACE", "heycloud/dev")


def put_metric(
    metric_name: str,
    value: float,
    unit: str = "Count",
    dimensions: Optional[list[dict]] = None,
) -> None:
    """Publish a custom metric to CloudWatch.

    Args:
        metric_name: Name of the metric (e.g., "EventsProcessed").
        value: Metric value.
        unit: CloudWatch unit (Count, Milliseconds, Bytes, etc.).
        dimensions: Optional list of {"Name": ..., "Value": ...} dicts.
    """
    try:
        metric_data = {
            "MetricName": metric_name,
            "Value": value,
            "Unit": unit,
            "Timestamp": time.time(),
        }

        if dimensions:
            metric_data["Dimensions"] = dimensions

        cloudwatch.put_metric_data(
            Namespace=NAMESPACE,
            MetricData=[metric_data],
        )
    except Exception as e:
        # Metrics should never break the main processing pipeline
        logger.warning(f"Failed to publish metric {metric_name}: {e}")


def emit_processing_metrics(
    events_processed: int,
    events_failed: int,
    duration_ms: float,
    event_type_counts: dict[str, int],
) -> None:
    """Emit a batch of processing metrics after each Lambda invocation."""
    put_metric("EventsProcessed", events_processed)
    put_metric("EventsFailed", events_failed)
    put_metric("ProcessingLatencyMs", duration_ms, unit="Milliseconds")

    for event_type, count in event_type_counts.items():
        put_metric(
            "EventsByType",
            count,
            dimensions=[{"Name": "EventType", "Value": event_type}],
        )
