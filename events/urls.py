from django.urls import path, include

from rest_framework.routers import DefaultRouter

from events.views import CategoryViewSet, EventViewSet

router = DefaultRouter()
router.register(r"category", CategoryViewSet)
router.register(r"events", EventViewSet)

urlpatterns = [
    path("", include(router.urls)),
]