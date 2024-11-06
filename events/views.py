from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated
from rest_framework.viewsets import GenericViewSet

from core.permissions import IsAuthorOrReadOnly

from events.serializers import CategorySerializers, EventSerializers, EventListSerializers, SeatSerializers, ReservationSerializers
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
        
        self.queryset = SeatSerializers.get_optimized_queryset().filter(event_id=event_id)
        return super().list(request, *args, **kwargs)
    

class ReservationViewSet(MappingViewSetMixin, GenericViewSet, CreateModelMixin, ListModelMixin, DestroyModelMixin):
    serializer_class=ReservationSerializers
    queryset=ReservationSerializers.get_optimized_queryset()
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user.profile)

    def list(self: GenericViewSet | LoggerMixin, request, *args, **kwargs):
        self.queryset = ReservationSerializers.get_optimized_queryset().filter(user=self.request.user.profile)
        return super().list(request, *args, **kwargs)