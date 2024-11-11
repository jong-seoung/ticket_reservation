from config.celery import celery_app

from django.contrib.auth.models import update_last_login

from accounts.models import User


@celery_app.task
def update_user_last_login(sender, user_by_email):
    update_last_login(None, user_by_email)

@celery_app.task
def signup_user(data):
    user = User.objects.create_user(**data)
    return user
