import json
from django.db.models.signals import post_migrate
from django.dispatch import receiver
from django_celery_beat.models import PeriodicTask, IntervalSchedule


@receiver(post_migrate)
def create_batch_update_last_login(sender, **kwargs):
    if sender.name == "django_celery_beat":
        schedule, _ = IntervalSchedule.objects.get_or_create(
            every=60,
            period=IntervalSchedule.SECONDS,
        )

        task, created = PeriodicTask.objects.get_or_create(
            name="1분마다 로그인 정보 수정",
            defaults={
                "interval": schedule,
                "task": "accounts.tasks.batch_update_last_login",
                "args": json.dumps([]),
            }
        )

        if created:
            print("✔ 1분마다 로그인 정보 수정 작업이 생성되었습니다.")
        else:
            print("⚠ 1분마다 로그인 정보 수정은 이미 존재하는 주기적 작업입니다.")