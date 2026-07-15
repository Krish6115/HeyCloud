"""
HeyCloud Stream Processor — Lambda Handler

Entry point for the Kinesis → Lambda event source mapping.
Terraform config: handler = "handler.lambda_handler"

Processing pipeline per invocation:
  1. Receive batch of Kinesis records (up to 100)
  2. Decode base64 → JSON → validate schema
  3. Write valid events to DynamoDB (hot storage)
  4. Archive raw events to S3 (cold storage / data lake)
  5. Update aggregation counters (revenue, counts, active users)
  6. Emit custom CloudWatch metrics
  7. Report batch results

Error handling:
  - Individual record failures don't fail the batch
  - bisect_batch_on_function_error splits failing batches
  - After max retries, failed records go to SQS DLQ
"""

import time

from processors.transform import transform_kinesis_record, transform_sqs_record
from processors.aggregation import aggregate_events
from storage.dynamodb_writer import write_events
from storage.s3_writer import archive_events
from utils.logger import get_logger
from utils.metrics import emit_processing_metrics

logger = get_logger(__name__)


def lambda_handler(event: dict, context) -> dict:
    """Process a batch of Kinesis or SQS records.

    Args:
        event: Event containing list of records.
        context: Lambda runtime context (request ID, remaining time, etc.).

    Returns:
        Dict with batch processing results for CloudWatch logging.
    """
    start_time = time.time()
    records = event.get("Records", [])
    batch_size = len(records)

    logger.info(
        f"Processing batch of {batch_size} records",
        extra={"batch_size": batch_size},
    )

    # =========================================================================
    # Step 1: Transform — decode and validate each record
    # =========================================================================
    valid_events = []
    invalid_count = 0

    for record in records:
        if "kinesis" in record:
            processed = transform_kinesis_record(record)
        elif "body" in record:
            processed = transform_sqs_record(record)
        else:
            logger.warning("Unknown record format")
            processed = None

        if processed:
            valid_events.append(processed)
        else:
            invalid_count += 1

    logger.info(
        f"Transformation complete: {len(valid_events)} valid, {invalid_count} invalid"
    )

    if not valid_events:
        logger.warning("No valid events in batch — skipping storage writes")
        return {
            "statusCode": 200,
            "batchSize": batch_size,
            "processed": 0,
            "invalid": invalid_count,
        }

    # =========================================================================
    # Step 2: Write to DynamoDB (hot path — real-time queries)
    # =========================================================================
    dynamo_result = write_events(valid_events)

    # =========================================================================
    # Step 3: Archive to S3 (cold path — data lake)
    # =========================================================================
    s3_result = archive_events(valid_events)

    # =========================================================================
    # Step 4: Update aggregations (atomic counters)
    # =========================================================================
    agg_result = aggregate_events(valid_events)

    # =========================================================================
    # Step 5: Emit custom CloudWatch metrics
    # =========================================================================
    duration_ms = round((time.time() - start_time) * 1000, 2)

    emit_processing_metrics(
        events_processed=len(valid_events),
        events_failed=invalid_count + dynamo_result["failed"] + s3_result["failed"],
        duration_ms=duration_ms,
        event_type_counts=agg_result["event_type_counts"],
    )

    # =========================================================================
    # Result summary
    # =========================================================================
    result = {
        "statusCode": 200,
        "batchSize": batch_size,
        "processed": len(valid_events),
        "invalid": invalid_count,
        "dynamodb": dynamo_result,
        "s3": s3_result,
        "aggregations": agg_result,
        "durationMs": duration_ms,
    }

    logger.info(
        f"Batch complete in {duration_ms}ms: "
        f"{len(valid_events)} processed, {invalid_count} invalid, "
        f"revenue=${agg_result['revenue']}",
        extra={"duration_ms": duration_ms, "batch_size": batch_size},
    )

    return result
