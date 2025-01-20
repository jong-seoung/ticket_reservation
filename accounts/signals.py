from django.db.models.signals import post_migrate
from django.dispatch import receiver
from django_celery_beat.models import PeriodicTask, IntervalSchedule
import json

@receiver(post_migrate)
def create_periodic_task(sender, **kwargs):
    if sender.name == "django_celery_beat":
        schedule, _ = IntervalSchedule.objects.get_or_create(
            every=1,
            period=IntervalSchedule.SECONDS,
        )

        task, created = PeriodicTask.objects.get_or_create(
            name="주기적인 작업 예제",
            defaults={
                "interval": schedule,
                "task": "accounts.tasks.my_scheduled_task",
                "args": json.dumps([]),
            }
        )

        if created:
            print("✔ 주기적인 작업이 생성되었습니다.")
        else:
            print("⚠ 이미 존재하는 주기적 작업입니다.")
