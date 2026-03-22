import os
import json
import logging
from datetime import datetime, timezone
from kafka import KafkaConsumer
from elasticsearch import Elasticsearch

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

KAFKA_HOST = os.environ.get("KAFKA_HOST", "kafka:9092")
KAFKA_TOPIC = os.environ.get("KAFKA_TOPIC", "task-events")
ES_HOST = os.environ.get("ES_HOST", "http://elasticsearch:9200")
ES_INDEX = os.environ.get("ES_INDEX", "task-audit")


def get_es():
    try:
        client = Elasticsearch(ES_HOST)
        if client.ping():
            logger.info(f"Elasticsearch connected: {ES_HOST}")
            return client
    except Exception as e:
        logger.error(f"Elasticsearch connection failed: {e}")
    return None


def process_event(event: dict, es: Elasticsearch | None):
    enriched = {
        **event,
        "processed_at": datetime.now(timezone.utc).isoformat(),
        "consumer_host": os.environ.get("HOSTNAME", "unknown"),
    }
    logger.info(f"Event: {enriched['event']} | task_id={enriched.get('id', 'N/A')}")

    if es:
        try:
            es.index(index=ES_INDEX, document=enriched)
        except Exception as e:
            logger.error(f"ES write failed: {e}")


def main():
    logger.info(f"Starting consumer: {KAFKA_HOST} topic={KAFKA_TOPIC}")

    consumer = KafkaConsumer(
        KAFKA_TOPIC,
        bootstrap_servers=KAFKA_HOST,
        value_deserializer=lambda m: json.loads(m.decode("utf-8")),
        group_id="task-audit-consumer",
        auto_offset_reset="earliest",
    )

    es = get_es()

    for message in consumer:
        process_event(message.value, es)


if __name__ == "__main__":
    main()