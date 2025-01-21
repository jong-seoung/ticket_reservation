from django.core.exceptions import ValidationError
from django.db import models
from django.conf import settings

from core.models import TimeStampModel
from accounts.models import Profile

class Category(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name
    
    
class Event(TimeStampModel):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="categorys")
    author = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='author')
    title = models.CharField(max_length=300)
    period_start = models.DateField()
    period_end = models.DateField()
    price = models.SmallIntegerField()
    event_date = models.DateField()
    content = models.TextField()

    def clean(self):
        if self.period_start > self.period_end:
            raise ValidationError("시작 날짜는 종료 날짜보다 이전이어야 합니다.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def formatted_price(self):
        return f"{self.price} 원"

    def __str__(self):
        return f"{self.title}"
    

class Seat(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="seats")
    position = models.CharField(max_length=30)
    is_reserved = models.BooleanField(default=False)

    def __str__(self) -> str:
        return f"{self.event} - {self.position}"

class Reservation(models.Model):
    event = models.ForeignKey(Event, on_delete=models.PROTECT, related_name='events')
    user = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='reservation_user')
    tickets = models.ManyToManyField(Seat, related_name="reservations")

    @property
    def ticket_count(self):
        return self.tickets.count()
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.user} 예약 - {self.event} (티켓 수: {self.ticket_count})"