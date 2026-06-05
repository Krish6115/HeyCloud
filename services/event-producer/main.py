"""
HeyCloud Event Producer — Main Entry Point

Generates simulated e-commerce streaming events and sends them to the
API Gateway endpoint which routes them into the Kinesis data stream.

Architecture:
  Producer (this) → HTTP POST → API Gateway → Kinesis → Lambda

Features:
  - Weighted random event type selection (mirrors real traffic)
  - Configurable TPS (transactions per second)
  - Exponential backoff retry on failures
  - Graceful shutdown on SIGINT/SIGTERM
  - Structured JSON logging
  - Batch mode for throughput optimization
"""

import json
import random
import signal
import time
from typing import Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

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

# =============================================================================
# Event Generator Registry
# =============================================================================
# Maps event types to their generators. The weighted random selection in
# _pick_generator() uses config.EVENT_WEIGHTS to simulate realistic
# e-commerce traffic (product views > searches > cart > login > purchase > payment).

GENERATORS = {
    "PRODUCT_VIEW": ProductViewGenerator(),
    "SEARCH": SearchQueryGenerator(),
    "ADD_TO_CART": CartEventGenerator(),
    "USER_LOGIN": UserLoginGenerator(),
    "PURCHASE": PurchaseGenerator(),
    "PAYMENT": PaymentGenerator(),
}


# =============================================================================
# HTTP Client with Retry
# =============================================================================

def create_http_session() -> requests.Session:
    """Create an HTTP session with exponential backoff retry.

    Why:
      - Transient network errors are normal in distributed systems.
      - Retrying with backoff prevents thundering herd on recovery.
      - Connection pooling via Session improves throughput.
    """
    session = requests.Session()

    retry_strategy = Retry(
        total=config.MAX_RETRIES,
        backoff_factor=config.RETRY_BACKOFF_FACTOR,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["POST"],
    )

    adapter = HTTPAdapter(
        max_retries=retry_strategy,
        pool_connections=10,
        pool_maxsize=10,
    )
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    # Set default headers
    session.headers.update({
        "Content-Type": "application/json",
    })

    # Add API key if configured
    if config.API_KEY:
        session.headers["x-api-key"] = config.API_KEY

    return session


# =============================================================================
# Event Production Logic
# =============================================================================

def _pick_event_type() -> str:
    """Select an event type based on weighted probabilities."""
    types = list(config.EVENT_WEIGHTS.keys())
    weights = list(config.EVENT_WEIGHTS.values())
    return random.choices(types, weights=weights, k=1)[0]


def send_event(session: requests.Session, event_data: dict) -> Optional[int]:
    """Send a single event to the API Gateway.

    Returns:
        HTTP status code on success, None on failure.
    """
    url = f"{config.API_GATEWAY_URL}/events"
    start_time = time.time()

    try:
        response = session.post(
            url,
            data=json.dumps(event_data),
            timeout=config.REQUEST_TIMEOUT,
        )
        duration_ms = round((time.time() - start_time) * 1000, 2)

        if response.status_code == 200:
            logger.debug(
                "Event sent successfully",
                extra={
                    "event_type": event_data.get("event_type"),
                    "status_code": response.status_code,
                    "duration_ms": duration_ms,
                },
            )
        else:
            logger.warning(
                f"Unexpected status code: {response.status_code}",
                extra={
                    "status_code": response.status_code,
                    "duration_ms": duration_ms,
                    "error": response.text[:200],
                },
            )
        return response.status_code

    except requests.exceptions.ConnectionError as e:
        logger.error(
            "Connection failed — is API Gateway running?",
            extra={"error": str(e)},
        )
        return None
    except requests.exceptions.Timeout:
        logger.error(
            f"Request timed out after {config.REQUEST_TIMEOUT}s",
            extra={"event_type": event_data.get("event_type")},
        )
        return None
    except requests.exceptions.RequestException as e:
        logger.error("Request failed", extra={"error": str(e)})
        return None


# =============================================================================
# Main Loop
# =============================================================================

class EventProducer:
    """Orchestrates continuous event generation and transmission."""

    def __init__(self):
        self.session = create_http_session()
        self.running = True
        self.events_sent = 0
        self.errors = 0
        self.start_time = time.time()

        # Register graceful shutdown handlers
        signal.signal(signal.SIGINT, self._shutdown)
        signal.signal(signal.SIGTERM, self._shutdown)

    def _shutdown(self, signum, frame):
        """Handle shutdown signals gracefully."""
        logger.info(
            f"Shutdown signal received. Sent {self.events_sent} events "
            f"with {self.errors} errors in "
            f"{round(time.time() - self.start_time, 1)}s"
        )
        self.running = False

    def run(self):
        """Main production loop — generates and sends events continuously."""
        interval = 1.0 / config.EVENTS_PER_SECOND
        logger.info(
            f"Starting event producer: {config.EVENTS_PER_SECOND} events/sec → "
            f"{config.API_GATEWAY_URL}"
        )

        while self.running:
            try:
                # Pick event type and generate
                event_type = _pick_event_type()
                generator = GENERATORS[event_type]
                event = generator.generate()
                event_data = event.to_json_dict()

                # Send to API Gateway
                status = send_event(self.session, event_data)

                if status == 200:
                    self.events_sent += 1
                else:
                    self.errors += 1

                # Log progress every 100 events
                if self.events_sent > 0 and self.events_sent % 100 == 0:
                    elapsed = round(time.time() - self.start_time, 1)
                    rate = round(self.events_sent / elapsed, 1)
                    logger.info(
                        f"Progress: {self.events_sent} sent, "
                        f"{self.errors} errors, "
                        f"{rate} events/sec actual"
                    )

                # Throttle to target TPS
                time.sleep(interval)

            except KeyboardInterrupt:
                self._shutdown(None, None)
            except Exception as e:
                logger.error(f"Unexpected error in producer loop: {e}", exc_info=True)
                self.errors += 1
                time.sleep(1)  # Back off on unexpected errors


def main():
    """Entry point for the event producer."""
    logger.info("=" * 60)
    logger.info("  HeyCloud Event Producer v1.0")
    logger.info("=" * 60)
    logger.info(f"  Target:  {config.API_GATEWAY_URL}")
    logger.info(f"  Rate:    {config.EVENTS_PER_SECOND} events/sec")
    logger.info(f"  Retries: {config.MAX_RETRIES} with {config.RETRY_BACKOFF_FACTOR}s backoff")
    logger.info("=" * 60)

    producer = EventProducer()
    producer.run()


if __name__ == "__main__":
    main()
