# workers/payment_processor/main.py
"""
Payment Processor Worker
========================
Consumes: order_validated
Produces: order_payment_processed | order_payment_failed
Simulates payment gateway integration
"""
import json
import os
import logging
import sys
import random
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from confluent_kafka import Producer
from common.kafka_consumer import create_consumer, run_consumer

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger("payment_processor")

KAFKA_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:29092")

producer = Producer({
    "bootstrap.servers": KAFKA_SERVERS,
    "client.id": "payment-processor-producer",
})


def process_payment(order_data: dict) -> dict:
    """
    Simulate payment gateway call.
    In production: integrate with Stripe, PayPal, etc.
    """
    payment_method = order_data.get("payment_method", "CREDIT_CARD")
    amount = order_data.get("total_amount", 0)

    # Simulate processing delay (I/O bound)
    time.sleep(0.1)

    # Simulate 95% success rate
    success = random.random() < 0.95

    return {
        "success": success,
        "transaction_id": f"TXN-{__import__('uuid').uuid4().hex[:12].upper()}",
        "payment_method": payment_method,
        "amount_charged": amount,
        "gateway_response": "approved" if success else "declined",
    }


def handle_order_validated(order_data: dict):
    order_id = order_data.get("order_id")
    logger.info(f"Processing payment for order {order_id}...")

    payment_result = process_payment(order_data)

    if payment_result["success"]:
        event = {
            "event_type": "order.payment_processed",
            "order_id": order_id,
            "user_id": order_data.get("user_id"),
            "payment": payment_result,
            "processed_at": __import__("datetime").datetime.utcnow().isoformat(),
        }
        topic = "order_payment_processed"
        logger.info(f"Payment ✅ for order {order_id} | TXN: {payment_result['transaction_id']}")
    else:
        event = {
            "event_type": "order.payment_failed",
            "order_id": order_id,
            "reason": "Payment declined",
            "payment": payment_result,
        }
        topic = "order_payment_failed"
        logger.warning(f"Payment ❌ for order {order_id}")

    producer.produce(topic=topic, key=order_id, value=json.dumps(event))
    producer.flush()


if __name__ == "__main__":
    consumer = create_consumer("payment-processor-group", ["order_validated"])
    run_consumer(consumer, handle_order_validated, "PaymentProcessor")
