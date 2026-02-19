# workers/common/kafka_consumer.py
"""Shared base Kafka consumer for all workers."""
from confluent_kafka import Consumer, KafkaError, KafkaException
import json
import logging
import os
from typing import Callable, List

logger = logging.getLogger(__name__)

KAFKA_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:29092")


def create_consumer(group_id: str, topics: List[str]) -> Consumer:
    conf = {
        "bootstrap.servers": KAFKA_SERVERS,
        "group.id": group_id,
        "auto.offset.reset": "earliest",
        "enable.auto.commit": True,
        "auto.commit.interval.ms": 5000,
        "session.timeout.ms": 30000,
    }
    consumer = Consumer(conf)
    consumer.subscribe(topics)
    logger.info(f"Consumer [{group_id}] subscribed to: {topics}")
    return consumer


def run_consumer(consumer: Consumer, handler: Callable[[dict], None], worker_name: str):
    """Main consumer loop with error handling."""
    logger.info(f"[{worker_name}] Worker started, waiting for messages...")
    try:
        while True:
            msg = consumer.poll(timeout=1.0)
            if msg is None:
                continue
            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    logger.debug(f"Reached end of partition: {msg.topic()}[{msg.partition()}]")
                else:
                    raise KafkaException(msg.error())
                continue

            try:
                data = json.loads(msg.value().decode("utf-8"))
                logger.info(f"[{worker_name}] Processing event: {data.get('event_type')} order={data.get('order_id')}")
                handler(data)
            except json.JSONDecodeError as e:
                logger.error(f"[{worker_name}] Invalid JSON: {e}")
            except Exception as e:
                logger.error(f"[{worker_name}] Handler error: {e}", exc_info=True)

    except KeyboardInterrupt:
        logger.info(f"[{worker_name}] Shutdown signal received.")
    finally:
        consumer.close()
        logger.info(f"[{worker_name}] Consumer closed.")
