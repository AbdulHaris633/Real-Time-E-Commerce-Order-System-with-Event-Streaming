# app/services/kafka_producer.py
from confluent_kafka import Producer
from app.config import settings
import json
import logging
from typing import Any, Dict
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

_producer: Producer | None = None


def get_producer() -> Producer:
    global _producer
    if _producer is None:
        _producer = Producer({
            "bootstrap.servers": settings.kafka_bootstrap_servers,
            "client.id": "order-api-producer",
            "acks": "all",
            "retries": 3,
        })
    return _producer


def _delivery_callback(err, msg):
    if err:
        logger.error(f"Kafka delivery failed: {err}")
    else:
        logger.debug(f"Message delivered → topic={msg.topic()} partition={msg.partition()} offset={msg.offset()}")


async def produce_order_event(event_type: str, order: Any) -> None:
    """Publish an order lifecycle event to Kafka."""
    topic = event_type.replace(".", "_")
    payload: Dict[str, Any] = {
        "event_type": event_type,
        "order_id": str(order.order_id),
        "user_id": str(order.user_id),
        "status": str(order.status.value if hasattr(order.status, "value") else order.status),
        "total_amount": float(order.total_amount),
        "items": order.items,
        "shipping_address": order.shipping_address,
        "payment_method": order.payment_method,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    try:
        producer = get_producer()
        producer.produce(
            topic=topic,
            key=str(order.order_id),
            value=json.dumps(payload),
            callback=_delivery_callback,
        )
        producer.poll(0)   # Trigger delivery report callbacks
        logger.info(f"Event published → topic={topic} order_id={order.order_id}")
    except Exception as e:
        logger.error(f"Failed to publish event {event_type}: {e}")
        raise


def flush_producer():
    """Flush on shutdown."""
    if _producer:
        _producer.flush(timeout=5)
        logger.info("Kafka producer flushed.")
