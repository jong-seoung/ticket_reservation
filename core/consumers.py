# app/kafka_consumer.py
from datetime import datetime
from kafka import KafkaConsumer
import json
import redis
from events.queue_manager import add_user_to_queue
from events.models import Reservation, Seat
from django.db import transaction

redis_client = redis.StrictRedis(host="redis", port=6379, db=0, decode_responses=True)

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



def check_reservations():
    consumer = KafkaConsumer(
        'seat_reservation',
        bootstrap_servers=['kafka:19092'],
        group_id='reservation_group',
        auto_offset_reset='latest',
        value_deserializer=lambda x: json.loads(x.decode('utf-8'))
    )

    for message in consumer:
        try:
            if isinstance(message.value, dict):  # 이미 dict이면 그대로 사용
                data = message.value
            else:  
                data = json.loads(message.value)  # JSON 문자열이면 변환

            seat_key = data["seat_key"]
            event_id = data["event_id"]
            ticket_id = data["ticket_id"]
            expiration_time = datetime.fromisoformat(data["expiration_time"])

            print(f"처리할 예약: {seat_key}, ticket_id: {ticket_id}, Expiration: {expiration_time}")

            if redis_client.exists(seat_key):
                if datetime.now() > expiration_time:
                    print(f"예약 {seat_key}이 자동 취소되었습니다.")
                else:
                    if data["status"] == "confirmed":
                        with transaction.atomic():
                            reservation = Reservation.objects.create(
                                user_id=data["user_id"],
                                event_id=event_id,
                            )
                            print(ticket_id)
                            seat = Seat.objects.get(id=ticket_id)
                            print(seat)
                            reservation.tickets.set([seat])

                            redis_client.delete(seat_key)
                            print(f"Redis에서 {seat_key} 삭제 완료")
                            print(f"예약 확정: {seat_key} (사용자 {data['user_id']})")
                    else:
                        print(f"예약 상태 확인 필요: {data['status']}")
                
        except KeyError as e:
            print(f"KeyError: {e} (Kafka 메시지에 필요한 필드가 없습니다)")
        except json.JSONDecodeError as e:
            print(f"JSONDecodeError: {e} (잘못된 JSON 형식)")
        except Exception as e:
            print(f"Unexpected Error: {e}")
