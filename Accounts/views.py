from django.shortcuts import render
from rest_framework import generics, permissions, status, permissions
from .serializers import UserRegistrationSerializer, UserInfoSerializer, UserDetailSerializer, CustomAuthTokenSerializer, PasswordChangeSerializer, PasswordResetRequestSerializer, PasswordResetSerializer, StaffUserRegistrationSerializer, CreateMembershipSerializer
from django.contrib.auth import get_user_model
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.permissions import AllowAny, IsAuthenticated
from .models import Membership

User = get_user_model()

class IsStaffPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_staff

class UserRegistrationView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = [permissions.AllowAny]
    serializer_class = UserRegistrationSerializer

class CreateStaffUserView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = StaffUserRegistrationSerializer
    permission_classes = [permissions.IsAdminUser]

class CustomObtainAuthToken(ObtainAuthToken):
    serializer_class = CustomAuthTokenSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data,
                                           context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)
        return Response({
            'token': token.key,
        })

class AllUsersView(generics.ListAPIView):
    queryset = User.objects.all()
    serializer_class = UserInfoSerializer
    permission_classes = [IsStaffPermission]

class SpecificUserView(generics.RetrieveAPIView):
    queryset = User.objects.all()
    serializer_class = UserDetailSerializer
    permission_classes = [IsStaffPermission]
    lookup_field = 'id'

class CurrentUserView(generics.RetrieveAPIView):
    serializer_class = UserInfoSerializer

    def get_object(self):
        return self.request.user

class MembershipInfoView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        active_membership = Membership.objects.filter(user=user, active=True).first()
        
        if active_membership:
            return Response({
                "active_membership": True,
                "free_books_used": active_membership.free_books_used,
                "next_payment_date": active_membership.recurrence
            })
        else:
            return Response({
                "active_membership": False
            })

class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        request.user.auth_token.delete()
        return Response(status=status.HTTP_200_OK)

class PasswordChangeView(generics.UpdateAPIView):
    serializer_class = PasswordChangeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def update(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"detail": "Password changed successfully"}, status=status.HTTP_200_OK)

class PasswordResetRequestView(generics.GenericAPIView):
    serializer_class = PasswordResetRequestSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"detail": "Password reset code sent"}, status=status.HTTP_200_OK)

class PasswordResetView(generics.GenericAPIView):
    serializer_class = PasswordResetSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"detail": "Password has been reset successfully"}, status=status.HTTP_200_OK)

class CreateMembershipView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        user = request.user

        # Check if user is already a member
        if user.memberships.filter(active=True).exists():
            return Response({"detail": "User is already a member."}, status=status.HTTP_400_BAD_REQUEST)

        # Create new membership (the price is handled by the model's default value)
        membership = Membership.objects.create(user=user)
        
        # Set the next recurrence automatically
        membership.set_next_recurrence()

        return Response({"detail": "Membership created successfully."}, status=status.HTTP_201_CREATED)

class ResetFreeBooksView(APIView):
    permission_classes = [IsStaffPermission]

    def post(self, request, *args, **kwargs):
        active_memberships = Membership.objects.filter(active=True)

        for membership in active_memberships:
            membership.free_books_used = 0
            membership.save()

        return Response({"detail": "Free books count has been reset for all active memberships."}, status=status.HTTP_200_OK)
