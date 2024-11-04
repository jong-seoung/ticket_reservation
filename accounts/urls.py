from django.urls import path

from accounts.views import SignupView, LoginView, LogoutView, ProfileView

urlpatterns = [
    path('register/', SignupView.as_view(), name="signup"),
    path('login/', LoginView.as_view(), name="login"),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('profile/', ProfileView.as_view(), name='profile'),
]
