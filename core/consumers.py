# app/kafka_consumer.py
from datetime import datetime
from kafka import KafkaConsumer
import json
import redis
from events.queue_manager import add_user_to_queue
from events.models import Reservation
from django.db import transaction

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


consumer = KafkaConsumer(
    'seat_reservation',
    bootstrap_servers=['kafka:9092'],
    value_deserializer=lambda x: json.loads(x.decode('utf-8'))
)

def check_reservations():
    for message in consumer:
        data = json.loads(message.value)
        seat_key = data["seat_key"]
        expiration_time = datetime.fromisoformat(data["expiration_time"])

        if redis_client.exists(seat_key):
            if datetime.now() > expiration_time:
                print(f"예약 {seat_key}이 자동 취소되었습니다.")
            else:
                if data["status"] == "confirmed":
                    with transaction.atomic():
                        Reservation.objects.create(
                            user_id=data["user_id"],
                            seat_id=seat_key,
                            event_id=data["event_id"],
                            position=data["position"],
                        )
                else:
                    pass
            redis_client.delete(seat_key)