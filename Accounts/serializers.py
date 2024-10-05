from Accounts.models import Membership, Transaction
from Server.models import BookRental
from django.contrib.auth import get_user_model, authenticate
from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.utils.crypto import get_random_string
from django.core.mail import send_mail

User = get_user_model()

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
    )
    password2 = serializers.CharField(write_only=True, required=True)
    joined_date = serializers.ReadOnlyField()

    class Meta:
        model = User
        fields = ('id', 'email', 'password', 'password2', 'first_name', 'last_name', 'joined_date')
        extra_kwargs = {
            'first_name': {'required': True},
            'last_name': {'required': False},
        }

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Passwords do not match."})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password2')
        user = User.objects.create_user(**validated_data)
        return user

class CurrentBookSerializer(serializers.ModelSerializer):
    class Meta:
        model = BookRental
        fields = ['book', 'rental_date', 'return_date']

class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = ['transaction_date', 'amount', 'item']

class CurrentMembershipSerializer(serializers.ModelSerializer):
    transaction_history = TransactionSerializer(many=True, read_only=True)
    recurrence = serializers.DateField()

    class Meta:
        model = Membership
        fields = ['start_date', 'end_date', 'free_books_used', 'active', 'recurrence', 'transaction_history']

class UserInfoSerializer(serializers.ModelSerializer):
    active_membership = serializers.SerializerMethodField()
    current_book = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'is_staff', 'joined_date', 'active_membership', 'current_book']
        read_only_fields = ['id', 'email', 'joined_date']

    def get_active_membership(self, obj):
        active_membership = obj.memberships.filter(active=True).first()
        if active_membership:
            return CurrentMembershipSerializer(active_membership).data
        return None

    def get_current_book(self, obj):
        current_book = obj.rented_books.filter(return_date__isnull=True).first()
        if current_book:
            return CurrentBookSerializer(current_book).data
        return None

class UserDetailSerializer(serializers.ModelSerializer):
    current_membership = serializers.SerializerMethodField()
    membership_history = CurrentMembershipSerializer(many=True, read_only=True, source='memberships')
    transaction_history = TransactionSerializer(many=True, read_only=True, source='transactions')
    current_book = serializers.SerializerMethodField()
    book_history = CurrentBookSerializer(many=True, read_only=True, source='rented_books')

    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'is_staff', 'joined_date', 'active_membership', 'membership_history', 'transaction_history', 'current_book', 'book_history']
        read_only_fields = ['id', 'email', 'joined_date']

    def get_active_membership(self, obj):
        active_membership = obj.memberships.filter(active=True).first()
        if active_membership:
            return CurrentMembershipSerializer(active_membership).data
        return None

    def get_current_book(self, obj):
        current_book = obj.rented_books.filter(return_date__isnull=True).first()
        if current_book:
            return CurrentBookSerializer(current_book).data
        return None

class StaffUserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
    )
    password2 = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ('id', 'email', 'password', 'password2', 'first_name', 'last_name')
        extra_kwargs = {
            'first_name': {'required': True},
            'last_name': {'required': False},
        }

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Passwords do not match."})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password2')
        user = User.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
        )
        user.is_staff = True  # Make sure the created user is a staff user
        user.save()
        return user

class CustomAuthTokenSerializer(serializers.Serializer):
    email = serializers.EmailField(label="Email")
    password = serializers.CharField(
        label="Password",
        style={'input_type': 'password'},
        trim_whitespace=False,
    )

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        if email and password:
            user = authenticate(request=self.context.get('request'), email=email, password=password)
            if not user:
                msg = 'Unable to log in with provided credentials.'
                raise serializers.ValidationError(msg, code='authorization')
        else:
            msg = 'Must include "email" and "password".'
            raise serializers.ValidationError(msg, code='authorization')

        attrs['user'] = user
        return attrs

class PasswordChangeSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(required=True, write_only=True)
    new_password2 = serializers.CharField(required=True, write_only=True)

    def validate(self, data):
        user = self.context['request'].user
        
        # Check if the old password is correct
        if not user.check_password(data['old_password']):
            raise serializers.ValidationError({"old_password": "Old password is incorrect"})

        # Check if the new passwords match
        if data['new_password'] != data['new_password2']:
            raise serializers.ValidationError({"new_password": "The two passwords do not match"})
        
        # Validate the new password (using Django's built-in validators)
        validate_password(data['new_password'], user)
        
        return data

    def save(self):
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()

class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        # Check if a user with this email exists
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError("No user is registered with this email address.")
        return value

    def save(self):
        email = self.validated_data['email']
        user = User.objects.get(email=email)
        
        # Generate a unique code (e.g., a 6-digit code or token)
        reset_code = get_random_string(length=6, allowed_chars='1234567890')
        
        # Store this reset code on the user object (or use a separate model for tokens)
        user.reset_code = reset_code
        user.save()

        # Send an email to the user with the reset code
        send_mail(
            subject="Password Reset Request",
            message=f"Your password reset code is: {reset_code}",
            from_email='FFLO',
            recipient_list=[email],
            fail_silently=False,
        )

class PasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField()
    reset_code = serializers.CharField(required=True)
    new_password = serializers.CharField(write_only=True, required=True)
    new_password2 = serializers.CharField(write_only=True, required=True)

    def validate(self, data):
        # Validate the new passwords
        if data['new_password'] != data['new_password2']:
            raise serializers.ValidationError("The two passwords do not match.")

        # Validate that the reset code is correct
        user = User.objects.filter(email=data['email'], reset_code=data['reset_code']).first()
        if not user:
            raise serializers.ValidationError("Invalid reset code or email.")
        
        return data

    def save(self):
        user = User.objects.get(email=self.validated_data['email'])
        user.set_password(self.validated_data['new_password'])
        user.reset_code = None  # Clear the reset code
        user.save()

class CreateMembershipSerializer(serializers.ModelSerializer):
    class Meta:
        model = Membership
        fields = ['user', 'start_date', 'recurrence']

    def create(self, validated_data):
        user = validated_data['user']
        membership = Membership.objects.create(
            user=user,
            start_date=validated_data.get('start_date', timezone.now()),
            recurrence=validated_data.get('recurrence', timezone.now() + timedelta(days=30)),
            active=True
        )
        return membership
