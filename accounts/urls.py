from django.urls import path

from accounts.views import SignupView

urlpatterns = [
    path('register/', SignupView.as_view(), name="signup"),
]
