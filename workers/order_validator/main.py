# workers/order_validator/main.py
"""
Order Validator Worker
======================
Consumes: order_created
Produces: order_validated | order_failed
Validates: inventory, pricing, customer eligibility
"""
import json
import os
import logging
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from confluent_kafka import Producer
from common.kafka_consumer import create_consumer, run_consumer

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger("order_validator")

KAFKA_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:29092")

producer = Producer({
    "bootstrap.servers": KAFKA_SERVERS,
    "client.id": "order-validator-producer",
})


def validate_order(order_data: dict) -> dict:
    """
    Perform validation checks:
    - Inventory availability
    - Pricing consistency
    - Customer account status
    """
    order_id = order_data.get("order_id")
    items = order_data.get("items", [])
    total_amount = order_data.get("total_amount", 0)

    # ── Pricing validation ─────────────────────────────────────
    calculated_total = sum(
        item.get("unit_price", 0) * item.get("quantity", 1) for item in items
    )
    pricing_ok = abs(calculated_total - float(total_amount)) < 0.01

    # ── Inventory check (mocked) ───────────────────────────────
    inventory_ok = all(item.get("quantity", 0) > 0 for item in items)

    # ── Customer check (mocked) ────────────────────────────────
    customer_ok = bool(order_data.get("user_id"))

    return {
        "pricing_check": pricing_ok,
        "inventory_check": inventory_ok,
        "customer_check": customer_ok,
        "is_valid": pricing_ok and inventory_ok and customer_ok,
    }


def handle_order_created(order_data: dict):
    order_id = order_data.get("order_id")
    logger.info(f"Validating order {order_id}...")

    validation = validate_order(order_data)

    if validation["is_valid"]:
        event = {
            "event_type": "order.validated",
            "order_id": order_id,
            "user_id": order_data.get("user_id"),
            "validation_result": validation,
            "validated_at": __import__("datetime").datetime.utcnow().isoformat(),
        }
        topic = "order_validated"
    else:
        event = {
            "event_type": "order.failed",
            "order_id": order_id,
            "reason": "Validation failed",
            "validation_result": validation,
        }
        topic = "order_failed"

    producer.produce(
        topic=topic,
        key=order_id,
        value=json.dumps(event),
    )
    producer.flush()
    logger.info(f"Order {order_id} → {'validated ✅' if validation['is_valid'] else 'failed ❌'}")


if __name__ == "__main__":
    consumer = create_consumer("order-validator-group", ["order_created"])
    run_consumer(consumer, handle_order_created, "OrderValidator")
