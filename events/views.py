from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.viewsets import GenericViewSet

from core.permissions import IsAuthorOrReadOnly

from events.serializers import CategorySerializers, EventSerializers, EventListSerializers
from core.mixins import (
    CreateModelMixin, 
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