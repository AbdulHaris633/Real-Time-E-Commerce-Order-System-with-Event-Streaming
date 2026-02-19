# workers/inventory_manager/main.py
"""
Inventory Manager Worker
========================
Consumes: order_payment_processed, order_cancelled
Produces: order_fulfilled | order_out_of_stock
Manages stock levels after payment
"""
import json
import os
import logging
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from confluent_kafka import Producer
from common.kafka_consumer import create_consumer, run_consumer

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger("inventory_manager")

KAFKA_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:29092")

producer = Producer({
    "bootstrap.servers": KAFKA_SERVERS,
    "client.id": "inventory-manager-producer",
})

# In-memory stock (in production: database table or external service)
_stock = {}


def reserve_inventory(order_data: dict) -> bool:
    """Reserve stock for all order items."""
    items = order_data.get("items", [])
    for item in items:
        product_id = item.get("product_id")
        qty = item.get("quantity", 1)
        available = _stock.get(product_id, 999)  # Default: unlimited stock in demo
        if available < qty:
            return False
        _stock[product_id] = available - qty
    return True


def release_inventory(order_data: dict):
    """Release reserved stock on cancellation."""
    items = order_data.get("items", [])
    for item in items:
        product_id = item.get("product_id")
        qty = item.get("quantity", 1)
        _stock[product_id] = _stock.get(product_id, 0) + qty


def handle_payment_processed(order_data: dict):
    order_id = order_data.get("order_id")
    logger.info(f"Reserving inventory for order {order_id}...")

    success = reserve_inventory(order_data)
    if success:
        event = {
            "event_type": "order.fulfilled",
            "order_id": order_id,
            "user_id": order_data.get("user_id"),
            "fulfilled_at": datetime.now(timezone.utc).isoformat(),
        }
        producer.produce(topic="order_fulfilled", key=order_id, value=json.dumps(event))
        logger.info(f"Inventory reserved ✅ for order {order_id}")
    else:
        event = {
            "event_type": "order.out_of_stock",
            "order_id": order_id,
            "reason": "Insufficient inventory",
        }
        producer.produce(topic="order_out_of_stock", key=order_id, value=json.dumps(event))
        logger.warning(f"Out of stock ❌ for order {order_id}")

    producer.flush()


def handle_event(order_data: dict):
    event_type = order_data.get("event_type", "")
    if event_type == "order.payment_processed":
        handle_payment_processed(order_data)
    elif event_type == "order.cancelled":
        release_inventory(order_data)
        logger.info(f"Inventory released for cancelled order {order_data.get('order_id')}")


if __name__ == "__main__":
    consumer = create_consumer(
        "inventory-manager-group",
        ["order_payment_processed", "order_cancelled"]
    )
    run_consumer(consumer, handle_event, "InventoryManager")
