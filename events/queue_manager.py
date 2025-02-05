# app/queue_manager.py
import redis
import json
import time

redis_client = redis.StrictRedis(host="redis", port=6379, db=0, decode_responses=True)
QUEUE_NAME = "ticketing_queue"

def add_user_to_queue(user_id):
    """
    유저를 Redis ZSet에 추가
    """
    timestamp = int(time.time())  # 현재 타임스탬프를 기반으로 정렬
    user_data = json.dumps({"user_id": user_id, "timestamp": timestamp})
    redis_client.zadd(QUEUE_NAME, {user_data: timestamp})

def remove_user_from_queue(user_id):
    """
    유저가 새로고침하거나 페이지를 떠나면 Redis에서 제거
    """
    users = redis_client.zrange(QUEUE_NAME, 0, -1)

    for user_data in users:
        user_info = json.loads(user_data)
        if user_info.get("user_id") == user_id:
            redis_client.zrem(QUEUE_NAME, user_data)
            print(f"User {user_id} removed from queue")
            break
