from django.urls import path
from .views import UserRegistrationView, LogoutView, CustomObtainAuthToken, PasswordChangeView, PasswordResetRequestView, PasswordResetView, CreateStaffUserView, AllUsersView, SpecificUserView, CurrentUserView, MembershipInfoView, CreateMembershipView, ResetFreeBooksView
from rest_framework.authtoken.views import obtain_auth_token

urlpatterns = [
    path('register/', UserRegistrationView.as_view(), name='register'),
    path('login/', CustomObtainAuthToken.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('password/change/', PasswordChangeView.as_view(), name='password-change'),
    path('password/reset/', PasswordResetRequestView.as_view(), name='password-reset-request'),
    path('password/reset/confirm/', PasswordResetView.as_view(), name='password-reset-confirm'),
    path('staff/create/', CreateStaffUserView.as_view(), name='create-staff-user'),
    path('users/all/', AllUsersView.as_view(), name='all-users'),
    path('users/<int:id>/', SpecificUserView.as_view(), name='specific-user'),
    path('users/me/', CurrentUserView.as_view(), name='current-user'),
    path('users/membership/', MembershipInfoView.as_view(), name='membership-info'),
    path('membership/create/', CreateMembershipView.as_view(), name='create-membership'),
    path('memberships/reset-free-books/', ResetFreeBooksView.as_view(), name='reset-free-books'),
]