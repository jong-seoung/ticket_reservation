from django.core.cache import cache

from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from django_redis import get_redis_connection
from kafka import KafkaProducer
import json

from accounts.serializers import AuthorSerializer
from events.models import Category, Event, Seat, Reservation


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
    is_reserved = serializers.SerializerMethodField() 

    class Meta:
        model = Seat
        fields = ['id', 'event', 'position', 'is_reserved', 'seat']  
        read_only_fields = ['id', 'is_reserved', 'position']

    def get_is_reserved(self, obj):
        return obj.is_reserved

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
    user_name = serializers.CharField(source='user.user.name', read_only=True)

    class Meta:
        model = Reservation
        fields = ['id', 'event_title', 'event_date', 'user_name', 'tickets', 'ticket_count']

    def create(self, validated_data):
        tickets = validated_data.pop('tickets')
        
        # 모든 좌석이 동일한 이벤트에 속하는지 확인
        event_ids = {ticket.event_id for ticket in tickets}
        if len(event_ids) > 1:
            raise ValidationError("모든 좌석은 동일한 이벤트에 속해야 합니다.")
        
        validated_data['event'] = tickets[0].event

        # Redis 연결 및 좌석별 잠금 설정
        redis_conn = get_redis_connection('default')
        lock_keys = [f"seat_lock_{ticket.id}" for ticket in tickets]
        locks = [redis_conn.lock(lock_key, timeout=5) for lock_key in lock_keys]

        try:
            # 모든 좌석에 대해 잠금 확보
            for lock in locks:
                if not lock.acquire(blocking=True):
                    raise ValidationError("예약 중 다른 사용자가 예약을 진행 중인 좌석이 있습니다.")
            
            # 이미 예약된 좌석이 있는지 확인
            reserved_seats = Seat.objects.filter(id__in=[ticket.id for ticket in tickets], is_reserved=True)
            if reserved_seats.exists():
                raise ValidationError("이미 예약된 좌석이 포함되어 있습니다.")
            
            # 예약 생성 및 좌석 상태 업데이트
            reservation = Reservation.objects.create(**validated_data)
            reservation.tickets.set(tickets)
            Seat.objects.filter(id__in=[ticket.id for ticket in tickets]).update(is_reserved=True)

            # Kafka로 예약 이벤트 전송
            producer = KafkaProducer(
                bootstrap_servers='localhost:9092',
                value_serializer=lambda v: json.dumps(v).encode('utf-8')
            )
            for ticket in tickets:
                event_data = {
                    "seat_id": ticket.id,
                    "event_id": ticket.event.id,
                    "position": ticket.position,
                    "status": "reserved"
                }
                producer.send('seat_reservations', event_data)
            producer.flush()

            # 캐시 갱신
            cache_key = f"event_{tickets[0].event.id}_seats"
            cache.delete(cache_key) 

        finally:
            # 모든 잠금 해제
            for lock in locks:
                lock.release()
    
        return reservation
    
    def get_optimized_queryset():
        return Reservation.objects.all()