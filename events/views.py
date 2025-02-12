from django.core.cache import cache
from datetime import datetime, timedelta

from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated
from rest_framework.viewsets import GenericViewSet
from rest_framework.exceptions import ValidationError
from rest_framework.views import APIView

from .models import Seat
from core.permissions import IsAuthorOrReadOnly, IsOwner
from events.serializers import CategorySerializers, EventSerializers, EventListSerializers, SeatSerializers, ReservationSerializers
from core.producer import producer
from core.mixins import (
    CreateModelMixin,
    LoggerMixin, 
    RetrieveModelMixin,
    ListModelMixin,
    UpdateModelMixin, 
    DestroyModelMixin, 
    MappingViewSetMixin
)


class CategoryViewSet(GenericViewSet, CreateModelMixin, ListModelMixin, UpdateModelMixin, DestroyModelMixin):
    serializer_class = CategorySerializers
    queryset = CategorySerializers.get_optimized_queryset()
    

class EventViewSet(MappingViewSetMixin, GenericViewSet, CreateModelMixin, RetrieveModelMixin, ListModelMixin, UpdateModelMixin, DestroyModelMixin):
    serializer_class=EventSerializers
    serializer_action_map = {
        "create": EventSerializers,
        "retrieve": EventSerializers,
        "list": EventListSerializers,
        "update": EventSerializers,
    }
    queryset = EventSerializers.get_optimized_queryset().select_related("author","author__user","category")

    permission_classes = [IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(author=self.request.user.profile)
    

class seatViewSet(MappingViewSetMixin, GenericViewSet, CreateModelMixin, ListModelMixin):
    serializer_class = SeatSerializers
    queryset = SeatSerializers.get_optimized_queryset()


    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        seats = serializer.save()
        response_serializer = self.get_serializer(seats, many=True)
        headers = self.get_success_headers(response_serializer.data)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def list(self: GenericViewSet | LoggerMixin, request, *args, **kwargs):
        event_id = self.request.query_params.get('event_id')

        if not event_id:
            return Response({"error":"event_id 값이 없습니다."})
        
        cache_key = f"event_{event_id}_seats"
        seats_data = cache.get(cache_key)

        if not seats_data:
            seats = Seat.objects.select_related('event').prefetch_related('reservations').filter(event_id=event_id)
            seats_data = self.serializer_class(seats, many=True).data
            cache.set(cache_key, seats_data, timeout=60*15) 

        return Response(seats_data)
    

class ReservationViewSet(MappingViewSetMixin, GenericViewSet, CreateModelMixin, ListModelMixin, DestroyModelMixin):
    serializer_class=ReservationSerializers
    queryset=ReservationSerializers.get_optimized_queryset()
    permission_classes = [IsAuthenticated, IsOwner]

    def perform_create(self, serializer):
        instance= serializer.save(user=self.request.user.profile)
        response_data = self.get_serializer(instance).data
        response_data["message"] = "예매 성공"

        return Response({"message": "예매 요청이 정상적으로 접수되었습니다."}, status=status.HTTP_202_ACCEPTED)

    def list(self: GenericViewSet | LoggerMixin, request, *args, **kwargs):
        self.queryset = ReservationSerializers.get_optimized_queryset().filter(user=self.request.user.profile)
        return super().list(request, *args, **kwargs)
    

############# redis를 이용한 대기열 시스템 #############
import json
import time
import redis
from django.http import StreamingHttpResponse
from .queue_manager import add_user_to_queue, remove_user_from_queue

redis_client = redis.StrictRedis(host="redis", port=6379, db=0, decode_responses=True)
QUEUE_NAME = "ticketing_queue"

def enter_ticket_page(request):
    """
    1. 유저가 `/redis-ticket-page`에 들어오면 대기열에 추가
    2. SSE를 통해 실시간 순번 확인
    """
    user_id = request.user.id

    add_user_to_queue(user_id)  # Redis ZSet에 유저 추가
    return StreamingHttpResponse(event_stream(user_id), content_type="text/event-stream")

def event_stream(user_id):
    """
    SSE를 통해 실시간으로 대기열 순번을 확인
    """
    while True:
        try:
            users = redis_client.zrange(QUEUE_NAME, 0, -1, withscores=True)
            total_user = len(users)
            position = None

            for index, (user_data, _) in enumerate(users):

                user_info = json.loads(user_data)
                if user_info.get("user_id") == user_id:

                    position = index + 1
                    break

            if position <= 10: 
                yield f"data: {json.dumps({'position': position, 'total_user':total_user, 'redirect': '/select-seat/'})}\n\n"
                break  # SSE 종료 → 클라이언트는 리디렉션 처리

            else:
                yield f"data: {json.dumps({'position': position, 'total_user':total_user, 'status': 'WAIT'})}\n\n"

            time.sleep(5)  # 5초마다 업데이트

        except Exception as e:
            print(f"Error in SSE: {e}")
            break


# 결제 확인
class TicketConfirmedView(APIView):
    def post(self, request):
        event_id = request.data.get("event_id")
        ticket_id = request.data.get("ticket_id")
        user_id = request.data.get("user_id")

        if not all([event_id, ticket_id, user_id]):
            raise ValidationError("event_id, ticket_id, user_id가 필요합니다.")

        seat_key = f"seat_reservation: {event_id}-{ticket_id}"
        # 기존 예약 정보 가져오기
        print("seat_key:", seat_key)
        existing_user_id = redis_client.get(seat_key)
        print("user_id", existing_user_id)
        if not existing_user_id:
            raise ValidationError("예약 정보가 존재하지 않습니다.")

        if int(existing_user_id) != user_id:
            raise ValidationError("해당 좌석의 예약자가 아닙니다.")

        # Kafka 이벤트 전송
        expiration_time = (datetime.now() + timedelta(hours=24)).isoformat()

        producer.send(
            "seat_reservation",
            {"seat_key": seat_key, "event_id": event_id, "ticket_id": ticket_id, "user_id": user_id, "status": "confirmed", "expiration_time": expiration_time},
        )

        return Response({"message": "좌석 예약이 확정되었습니다."}, status=200)