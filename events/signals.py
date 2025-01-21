import json
from django.db.models.signals import post_migrate
from django.dispatch import receiver
from django_celery_beat.models import PeriodicTask, IntervalSchedule


@receiver(post_migrate)
def create_batch_update_last_login(sender, **kwargs):
    if sender.name == "django_celery_beat":
        schedule, _ = IntervalSchedule.objects.get_or_create(
            every=1,
            period=IntervalSchedule.SECONDS,
        )

        task, created = PeriodicTask.objects.get_or_create(
            name="실시간 대기열 처리",
            defaults={
                "interval": schedule,
                "task": "events.tasks.process_queue_entry",
                "args": json.dumps([]),
            }
        )

        if created:
            print("✔ 실시간 대기열 처리 작업이 생성되었습니다.")
        else:
            print("⚠ 실시간 대기열 처리은 이미 존재하는 주기적 작업입니다.")