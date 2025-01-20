from celery import shared_task
from datetime import datetime

@shared_task
def my_scheduled_task():
    print(f"주기적인 작업 실행! 현지 시간: {datetime.now()} / end")
    return "Success"