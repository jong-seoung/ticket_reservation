from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.contrib.auth.models import (
    BaseUserManager,
    AbstractBaseUser,
    PermissionsMixin,
)

from core.models import TimeStampModel


class UserManager(BaseUserManager):
    def _create_user(self, email, password, **extra_fields):
        if not email:
            return ValueError("이메일을 설정해야 합니다")

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        extra_fields.setdefault("is_active", True)

        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if not extra_fields["is_staff"]:
            raise ValueError("슈퍼유저는 is_staff=True이어야 합니다.")
        if not extra_fields["is_superuser"]:
            raise ValueError("슈퍼유저는 is_superuser=True이어야 합니다.")
        
        return self.create_user(email, password, **extra_fields)
        


def validate_birthday(value):
    if value > timezone.now().date():
        raise ValidationError("생년월일은 미래의 날짜가 될 수 없습니다.")
    

class User(TimeStampModel, AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=30)

    phone_regex = RegexValidator(
        regex=r'^(\+82|0)?1[0-9]{8,9}$',  # 예시: 한국 전화번호 형식
        message="올바른 전화번호를 입력하세요. 예: +821012345678 또는 01012345678"
    )
    phone_number = models.CharField(
        validators=[phone_regex],
        max_length=15,
        unique=True
    )
    birthday = models.DateField(
        validators=[validate_birthday]
    )
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    def save(self, *args, **kwargs):
        if not self.email:
            raise ValueError("이메일은 필수 항목입니다.")
        super().save(*args, **kwargs)