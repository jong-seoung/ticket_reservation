from celery import shared_task
from django.utils.timezone import now

from django.contrib.auth import get_user_model
import redis

redis_client = redis.StrictRedis(host="redis", port=6379, db=0)
User = get_user_model()


@shared_task
def batch_update_last_login(user_ids=[]):
    """ 여러 사용자의 last_login을 한 번에 업데이트 (Batch 처리) """
    if not user_ids:
        user_ids = redis_client.smembers("recent_logins")  
        user_ids = [int(uid) for uid in user_ids]

    if not user_ids:
        return "No users to update."
    
    User.objects.filter(id__in=user_ids).update(last_login=now())

    for user_id in user_ids:
        redis_client.srem("recent_logins", user_id)
    return f"Updated last_login for users: {user_ids}"