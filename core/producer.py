# app/kafka_producer.py
from kafka import KafkaProducer
import json

producer = KafkaProducer(
    bootstrap_servers=["kafka:19092"],
    value_serializer=lambda v: json.dumps(v).encode("utf-8"),
)