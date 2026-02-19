# workers/fulfillment/main.py
"""
Fulfillment Worker
==================
Consumes: order_fulfilled
Produces: order_shipped
Handles warehouse picking, packing, and carrier handoff
"""
import json
import os
import logging
import sys
import uuid
from datetime import datetime, timezone, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from confluent_kafka import Producer
from common.kafka_consumer import create_consumer, run_consumer

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger("fulfillment")

KAFKA_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:29092")

producer = Producer({
    "bootstrap.servers": KAFKA_SERVERS,
    "client.id": "fulfillment-producer",
})

CARRIERS = ["UPS", "FedEx", "DHL", "USPS"]


def generate_tracking_number(carrier: str) -> str:
    prefix = {"UPS": "1Z", "FedEx": "FX", "DHL": "DH", "USPS": "US"}
    return f"{prefix.get(carrier, 'XX')}{uuid.uuid4().hex[:14].upper()}"


def handle_order_fulfilled(order_data: dict):
    order_id = order_data.get("order_id")
    logger.info(f"Processing fulfillment for order {order_id}...")

    import random
    carrier = random.choice(CARRIERS)
    tracking_number = generate_tracking_number(carrier)
    now = datetime.now(timezone.utc)
    estimated_delivery = now + timedelta(days=random.randint(2, 7))

    event = {
        "event_type": "order.shipped",
        "order_id": order_id,
        "user_id": order_data.get("user_id"),
        "shipping": {
            "carrier": carrier,
            "tracking_number": tracking_number,
            "shipped_at": now.isoformat(),
            "estimated_delivery": estimated_delivery.date().isoformat(),
        },
    }

    producer.produce(topic="order_shipped", key=order_id, value=json.dumps(event))
    producer.flush()
    logger.info(f"Order {order_id} shipped ✅ via {carrier} | Tracking: {tracking_number}")


if __name__ == "__main__":
    consumer = create_consumer("fulfillment-group", ["order_fulfilled"])
    run_consumer(consumer, handle_order_fulfilled, "Fulfillment")
