from django.urls import path

from accounts.views import SignupView, LoginView

urlpatterns = [
    path('register/', SignupView.as_view(), name="signup"),
    path('login/', LoginView.as_view(), name="login"),
]
