from django.urls import path, include

from rest_framework.routers import DefaultRouter

from events.views import CategoryViewSet, EventViewSet, seatViewSet, ReservationViewSet

from .views import enter_ticket_page

router = DefaultRouter()
router.register(r"category", CategoryViewSet)
router.register(r"events", EventViewSet)
router.register(r"seats", seatViewSet)
router.register(r"reservations", ReservationViewSet)


urlpatterns = [
    path("", include(router.urls)),
    path("redis-ticket-page/", enter_ticket_page, name="ticket_page"),
]