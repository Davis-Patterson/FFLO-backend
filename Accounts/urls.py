from django.urls import path
from .views import UserRegistrationView, LogoutView, CustomObtainAuthToken, PasswordChangeView, PasswordResetRequestView, PasswordResetView
from rest_framework.authtoken.views import obtain_auth_token

urlpatterns = [
    path('register/', UserRegistrationView.as_view(), name='register'),
    path('login/', CustomObtainAuthToken.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('password/change/', PasswordChangeView.as_view(), name='password-change'),
    path('password/reset/', PasswordResetRequestView.as_view(), name='password-reset-request'),
    path('password/reset/confirm/', PasswordResetView.as_view(), name='password-reset-confirm'),
]