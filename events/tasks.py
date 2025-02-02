# app/tasks.py
from celery import shared_task
import redis
from core.consumers import check_reservations

redis_client = redis.StrictRedis(host="redis", port=6379, db=0, decode_responses=True)
QUEUE_NAME = "ticketing_queue"

@shared_task
def process_queue_entry():
    """
    1초마다 10명씩 좌석 선택 페이지로 입장
    """
    for _ in range(10):  # 한 번 실행할 때 최대 10명 입장 처리

        message_data = redis_client.zpopmin(QUEUE_NAME)
        if not message_data:
            break

        print(f"User {message_data} is now allowed to enter ticket selection page")


@shared_task
def check_reservation_task():
    check_reservations()