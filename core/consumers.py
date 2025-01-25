# app/kafka_consumer.py
from kafka import KafkaConsumer
import json
import redis
from events.queue_manager import add_user_to_queue

redis_client = redis.StrictRedis(host="localhost", port=6379, db=0, decode_responses=True)

def kafka_consumer_task(game_id):
    """
    Kafka Consumer: 해당 경기의 대기열 메시지를 Redis ZSet에 저장
    """
    consumer = KafkaConsumer(
        f"game_{game_id}",
        bootstrap_servers=["kafka:19092"],
        value_deserializer=lambda x: json.loads(x.decode("utf-8")),
    )

    print(f"Listening for messages on game_{game_id} queue...")

    for message in consumer:
        try:
            data = message.value
            user_id = data.get("user_id")

            if not user_id:
                continue

            add_user_to_queue(user_id)  # Redis ZSet에 유저 추가
            print(f"User {user_id} added to Redis queue for game {game_id}")

        except Exception as e:
            print(f"Error processing message: {e}")

