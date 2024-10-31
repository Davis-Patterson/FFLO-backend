import stripe
from django.conf import settings
from django.shortcuts import render
from rest_framework import generics, permissions, status, permissions
from .serializers import UserRegistrationSerializer, UserInfoSerializer, UserDetailSerializer, UserProfileUpdateSerializer, CustomAuthTokenSerializer, PasswordChangeSerializer, PasswordResetRequestSerializer, PasswordResetConfirmSerializer, PasswordResetSerializer, StaffUserRegistrationSerializer, CreateMembershipSerializer
from django.contrib.auth import get_user_model
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authentication import BasicAuthentication
from rest_framework.permissions import AllowAny, IsAuthenticated
from .models import Membership
from Payments.models import Payment

User = get_user_model()
stripe.api_key = settings.STRIPE_SECRET_KEY

class IsStaffPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_staff


class VerifyTokenView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        user_data = UserInfoSerializer(user).data
        return Response({
            "detail": "Token is valid.",
            "user_info": user_data
        }, status=status.HTTP_200_OK)


class UserRegistrationView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = [permissions.AllowAny]
    serializer_class = UserRegistrationSerializer

    def perform_create(self, serializer):
        user = serializer.save()


class CreateStaffUserView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = StaffUserRegistrationSerializer
    permission_classes = [IsStaffPermission]


class CustomObtainAuthToken(ObtainAuthToken):
    serializer_class = CustomAuthTokenSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)
        
        user_data = UserInfoSerializer(user).data
        
        return Response({
            'token': token.key,
            'user': user_data
        }, status=status.HTTP_200_OK)


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


class UpdateProfileView(generics.UpdateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserProfileUpdateSerializer

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        return Response(UserInfoSerializer(instance).data, status=status.HTTP_200_OK)


class MembershipInfoView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        active_membership = Membership.objects.filter(user=user, active=True).first()
        
        if active_membership:
            return Response({
                "active_membership": True,
                "monthly_books": active_membership.monthly_books,
                "next_payment_date": active_membership.recurrence
            })
        else:
            return Response({
                "active_membership": False
            })


class LogoutView(APIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def post(self, request):
        auth_header = request.META.get('HTTP_AUTHORIZATION', None)

        if auth_header:
            try:
                token_key = auth_header.split()[1] if 'Token' in auth_header else None
                if token_key:
                    token = Token.objects.get(key=token_key)
                    token.delete()
                    return Response({"detail": "Logout successful."}, status=status.HTTP_200_OK)
            except Token.DoesNotExist:
                return Response({"detail": "Invalid or expired token."}, status=status.HTTP_401_UNAUTHORIZED)

        return Response({"detail": "No token provided."}, status=status.HTTP_400_BAD_REQUEST)


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
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"detail": "Password reset code sent"}, status=status.HTTP_200_OK)


class PasswordResetConfirmView(APIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = PasswordResetConfirmSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        return Response({"detail": "Reset code confirmed."}, status=status.HTTP_200_OK)


class PasswordResetView(APIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = PasswordResetSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"detail": "Password has been reset successfully."}, status=status.HTTP_200_OK)


class CreateMembershipView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        user = request.user

        if user.memberships.filter(active=True).exists():
            return Response({"detail": "User is already a member."}, status=status.HTTP_400_BAD_REQUEST)

        # Create the membership
        membership = Membership.objects.create(user=user)
        membership.set_next_recurrence()

        # Save the membership without handling payments for now
        membership.save()

        return Response({"detail": "Membership created successfully."}, status=status.HTTP_201_CREATED)


class ResetMonthlyBooksView(APIView):
    permission_classes = [IsStaffPermission]

    def post(self, request, *args, **kwargs):
        active_memberships = Membership.objects.filter(active=True)

        for membership in active_memberships:
            membership.monthly_books = 0 
            membership.save()

        return Response({"detail": "Monthly books count has been reset for all active memberships."}, status=200)
