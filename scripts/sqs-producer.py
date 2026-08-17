"""
HeyCloud SQS Event Producer — Main Entry Point

Generates simulated e-commerce streaming events and sends them directly to
the SQS events queue in batches of up to 10.
"""

import argparse
import json
import os
import random
import signal
import sys
import time

import boto3
from botocore.exceptions import ClientError

# Add the event-producer package to the path so we can reuse the models
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "services", "event-producer"))

from config import config
from generators import (
    CartEventGenerator,
    PaymentGenerator,
    ProductViewGenerator,
    PurchaseGenerator,
    SearchQueryGenerator,
    UserLoginGenerator,
)
from utils.logger import get_logger

logger = get_logger(__name__, config.LOG_LEVEL)

GENERATORS = {
    "PRODUCT_VIEW": ProductViewGenerator(),
    "SEARCH": SearchQueryGenerator(),
    "ADD_TO_CART": CartEventGenerator(),
    "USER_LOGIN": UserLoginGenerator(),
    "PURCHASE": PurchaseGenerator(),
    "PAYMENT": PaymentGenerator(),
}


def _pick_event_type() -> str:
    """Select an event type based on weighted probabilities."""
    types = list(config.EVENT_WEIGHTS.keys())
    weights = list(config.EVENT_WEIGHTS.values())
    return random.choices(types, weights=weights, k=1)[0]


class SQSProducer:
    """Orchestrates continuous event generation and transmission to SQS."""

    def __init__(self, queue_url: str):
        self.sqs = boto3.client("sqs")
        self.queue_url = queue_url
        self.running = True
        self.events_sent = 0
        self.errors = 0
        self.start_time = time.time()

        signal.signal(signal.SIGINT, self._shutdown)
        signal.signal(signal.SIGTERM, self._shutdown)

    def _shutdown(self, signum, frame):
        logger.info(
            f"Shutdown signal received. Sent {self.events_sent} events "
            f"with {self.errors} errors in "
            f"{round(time.time() - self.start_time, 1)}s"
        )
        self.running = False

    def send_batch(self, events: list[dict]) -> bool:
        """Send up to 10 events to SQS."""
        entries = []
        for i, event in enumerate(events):
            entries.append({
                "Id": str(i),
                "MessageBody": json.dumps(event)
            })

        start_time = time.time()
        try:
            response = self.sqs.send_message_batch(
                QueueUrl=self.queue_url,
                Entries=entries
            )
            
            failed = response.get("Failed", [])
            if failed:
                logger.warning(f"Failed to send {len(failed)} messages to SQS", extra={"errors": failed})
                self.errors += len(failed)
            
            success = response.get("Successful", [])
            if success:
                self.events_sent += len(success)
                duration_ms = round((time.time() - start_time) * 1000, 2)
                logger.debug(
                    f"Sent batch of {len(success)} messages to SQS",
                    extra={"duration_ms": duration_ms}
                )
            
            return len(failed) == 0
            
        except ClientError as e:
            logger.error(f"SQS send_message_batch failed: {e}", exc_info=True)
            self.errors += len(events)
            return False

    def run(self, count: int = 0):
        """Run the producer loop."""
        interval = 1.0 / config.EVENTS_PER_SECOND
        logger.info(
            f"Starting SQS producer: {config.EVENTS_PER_SECOND} events/sec → "
            f"{self.queue_url}"
        )

        batch = []
        
        while self.running:
            try:
                event_type = _pick_event_type()
                generator = GENERATORS[event_type]
                event = generator.generate()
                batch.append(event.to_json_dict())

                # Send batch when full or when count is reached
                if len(batch) >= 10 or (count > 0 and self.events_sent + len(batch) >= count):
                    self.send_batch(batch)
                    batch = []

                if count > 0 and self.events_sent >= count:
                    logger.info(f"Reached target count of {count} events. Stopping.")
                    break

                if self.events_sent > 0 and self.events_sent % 100 == 0:
                    elapsed = round(time.time() - self.start_time, 1)
                    rate = round(self.events_sent / elapsed, 1)
                    logger.info(
                        f"Progress: {self.events_sent} sent, "
                        f"{self.errors} errors, "
                        f"{rate} events/sec actual"
                    )

                time.sleep(interval)

            except KeyboardInterrupt:
                self._shutdown(None, None)
            except Exception as e:
                logger.error(f"Unexpected error in producer loop: {e}", exc_info=True)
                self.errors += 1
                time.sleep(1)
                
        # Flush any remaining messages
        if batch:
            self.send_batch(batch)


def main():
    parser = argparse.ArgumentParser(description="HeyCloud SQS Event Producer")
    parser.add_argument("--count", type=int, default=0, help="Number of events to generate (0 = infinite)")
    parser.add_argument("--queue-url", type=str, required=True, help="URL of the SQS events queue")
    args = parser.parse_args()

    logger.info("=" * 60)
    logger.info("  HeyCloud SQS Event Producer v1.0")
    logger.info("=" * 60)
    logger.info(f"  Target:  {args.queue_url}")
    logger.info(f"  Rate:    {config.EVENTS_PER_SECOND} events/sec")
    logger.info("=" * 60)

    producer = SQSProducer(args.queue_url)
    producer.run(args.count)


if __name__ == "__main__":
    main()
