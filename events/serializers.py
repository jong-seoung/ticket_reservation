from django.core.cache import cache

from rest_framework import serializers
from rest_framework.exceptions import ValidationError
import redis

from accounts.serializers import AuthorSerializer
from events.models import Category, Event, Seat, Reservation
from core.producer import producer

redis_client = redis.StrictRedis(host="redis", port=6379, db=0, decode_responses=True)

class CategorySerializers(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'

    @staticmethod
    def get_optimized_queryset():
        return Category.objects.all()
    

class EventSerializers(serializers.ModelSerializer):
    author = AuthorSerializer(read_only=True)
    category_name = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Event
        fields = '__all__'
    
    @staticmethod
    def get_optimized_queryset():
        return Event.objects.all()
    
    def get_category_name(self, obj):
        return obj.category.name if obj.category else None
    


class EventListSerializers(serializers.ModelSerializer):
    profile_image = serializers.ImageField(source='author.image', read_only=True)
    nickname = serializers.CharField(source='author.nickname', read_only=True)

    category_name = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Event
        fields = ['id', 'profile_image', 'nickname', 'category_name', 'title', 'price', 'event_date', 'created_at', 'period_start', 'period_end']
    
    def get_category_name(self, obj):
        return obj.category.name if obj.category else None


class SeatSerializers(serializers.ModelSerializer):
    seat = serializers.ListField(
        child=serializers.CharField(), 
        write_only=True
    )  

    class Meta:
        model = Seat
        fields = ['id', 'event', 'position', 'is_reserved', 'seat']  
        read_only_fields = ['id', 'is_reserved', 'position']

    def create(self, validated_data):
        event = validated_data.get("event")
        seat_positions = validated_data.pop("seat")

        seats = [Seat(event=event, position=position) for position in seat_positions]
        
        Seat.objects.bulk_create(seats)

        created_seats = Seat.objects.filter(event=event, position__in=seat_positions)
        
        return list(created_seats) 

    def get_optimized_queryset():
        return Seat.objects.all()
    

class ReservationSerializers(serializers.ModelSerializer):
    event_title = serializers.CharField(source='event.title', read_only=True)
    event_date = serializers.CharField(source='event.event_date', read_only=True)
    tickets = serializers.PrimaryKeyRelatedField(queryset=Seat.objects.all(), many=True)

    class Meta:
        model = Reservation
        fields = ['id', 'event_title', 'event_date', 'tickets', 'ticket_count']

    def create(self, validated_data):
        print(validated_data)
        tickets = validated_data.pop('tickets')
        profile = validated_data.pop('user')
        user = profile.user
        # 모든 좌석이 동일한 이벤트에 속하는지 확인
        event_ids = {ticket.event_id for ticket in tickets}

        if len(event_ids) > 1:
            raise ValidationError("모든 좌석은 동일한 이벤트에 속해야 합니다.")
        
        event = tickets[0].event
        validated_data['event'] = event

        for ticket in tickets:
            seat_key = f"seat_reservation: {event.id}-{ticket.position}"
            try:
                if redis_client.setnx(seat_key, user.id):
                    producer.send(
                        "seat_reservation",
                        {"event_id": event.id, "position": ticket.position, "user_id": user.id},
                    )
                else:
                    raise ValidationError("이미 예약된 좌석입니다.")
            except Exception as e:
                redis_client.delete(seat_key)
                raise ValidationError(f"예약 중 오류 발생: {str(e)}")
    
        reservation = self.Meta.model(id=None, event=event, user=profile)
        
        return reservation
    
    def get_optimized_queryset():
        return Reservation.objects.all()
