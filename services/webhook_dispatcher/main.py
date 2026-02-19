# services/webhook_dispatcher/main.py
"""
Webhook Dispatcher Service
===========================
Consumes all order events from Kafka.
Finds registered webhooks for the user.
Delivers HTTP POST with HMAC signature.
Implements exponential-backoff retry logic.
"""
import asyncio
import hashlib
import hmac
import json
import logging
import os
import time
from datetime import datetime, timezone

import aiohttp

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger("webhook_dispatcher")

KAFKA_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:29092")
MAX_RETRIES = int(os.getenv("WEBHOOK_MAX_RETRIES", "3"))
RETRY_DELAYS = [10, 30, 120]  # seconds

TOPICS = [
    "order_created", "order_validated", "order_payment_processed",
    "order_fulfilled", "order_shipped", "order_cancelled",
]

# In-memory webhook registry (in production: query from database)
_webhook_registry: dict = {}


def compute_hmac_signature(payload: str, secret: str) -> str:
    """Compute HMAC-SHA256 signature for webhook payload."""
    return hmac.new(
        secret.encode("utf-8"),
        payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


async def deliver_webhook(url: str, payload: dict, secret: str, attempt: int = 1) -> bool:
    """Deliver webhook with HMAC signature and retry logic."""
    payload_str = json.dumps(payload, default=str)
    signature = compute_hmac_signature(payload_str, secret)

    headers = {
        "Content-Type": "application/json",
        "X-Webhook-Signature": f"sha256={signature}",
        "X-Webhook-Timestamp": datetime.now(timezone.utc).isoformat(),
        "X-Webhook-Attempt": str(attempt),
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url,
                data=payload_str,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=10),
            ) as response:
                if response.status < 300:
                    logger.info(f"Webhook delivered ✅ → {url} [HTTP {response.status}]")
                    return True
                else:
                    logger.warning(f"Webhook failed → {url} [HTTP {response.status}]")
                    return False
    except aiohttp.ClientError as e:
        logger.error(f"Webhook connection error → {url}: {e}")
        return False


async def dispatch_with_retry(url: str, payload: dict, secret: str):
    """Dispatch with exponential backoff retries."""
    for attempt in range(1, MAX_RETRIES + 1):
        success = await deliver_webhook(url, payload, secret, attempt)
        if success:
            return
        if attempt < MAX_RETRIES:
            delay = RETRY_DELAYS[attempt - 1]
            logger.info(f"Retrying in {delay}s (attempt {attempt}/{MAX_RETRIES})")
            await asyncio.sleep(delay)
    logger.error(f"Webhook permanently failed after {MAX_RETRIES} attempts → {url}")


async def process_event(event_data: dict):
    """Find matching webhooks and dispatch."""
    event_type = event_data.get("event_type", "").replace("_", ".")
    user_id = event_data.get("user_id")

    # Get webhooks for this user+event (from registry or DB)
    user_webhooks = _webhook_registry.get(user_id, [])
    matching = [w for w in user_webhooks if event_type in w.get("event_types", [])]

    if not matching:
        logger.debug(f"No webhooks for user={user_id} event={event_type}")
        return

    tasks = [
        dispatch_with_retry(w["url"], event_data, w["secret"])
        for w in matching
    ]
    await asyncio.gather(*tasks)


def run_dispatcher():
    from confluent_kafka import Consumer, KafkaError
    consumer = Consumer({
        "bootstrap.servers": KAFKA_SERVERS,
        "group.id": "webhook-dispatcher-group",
        "auto.offset.reset": "earliest",
    })
    consumer.subscribe(TOPICS)
    logger.info("Webhook dispatcher started, listening to all order events...")

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        while True:
            msg = consumer.poll(1.0)
            if msg is None:
                continue
            if msg.error():
                if msg.error().code() != KafkaError._PARTITION_EOF:
                    logger.error(f"Kafka error: {msg.error()}")
                continue

            try:
                data = json.loads(msg.value().decode("utf-8"))
                loop.run_until_complete(process_event(data))
            except Exception as e:
                logger.error(f"Dispatcher error: {e}", exc_info=True)

    except KeyboardInterrupt:
        logger.info("Shutting down webhook dispatcher...")
    finally:
        consumer.close()
        loop.close()


if __name__ == "__main__":
    run_dispatcher()
