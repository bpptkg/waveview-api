import re

from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from waveview.users.models import User


class UserSerializer(serializers.Serializer):
    id = serializers.UUIDField(help_text=_("User ID."))
    username = serializers.CharField(help_text=_("Username."))
    name = serializers.CharField(help_text=_("User name."), allow_blank=True)
    avatar = serializers.ImageField(
        help_text=_("User avatar image URL."), allow_null=True
    )


class UserDetailSerializer(UserSerializer):
    email = serializers.EmailField(help_text=_("User email."))
    phone_number = serializers.CharField(help_text=_("User phone number."))
    date_joined = serializers.DateTimeField(help_text=_("Date when user fist joined."))
    bio = serializers.CharField(
        help_text=_("User biography description."), allow_blank=True
    )
    is_staff = serializers.BooleanField(help_text=_("True if user is an admin staff."))
    is_superuser = serializers.BooleanField(
        help_text=_("True if the user is a superuser.")
    )


class UserUpdatePayloadSerializer(serializers.Serializer):
    name = serializers.CharField(
        help_text=_("User name."), allow_blank=True, required=False
    )
    avatar = serializers.ImageField(
        help_text=_("User avatar image URL."), allow_null=True, required=False
    )
    bio = serializers.CharField(
        help_text=_("User biography description."), allow_blank=True, required=False
    )

    def update(self, instance: User, validated_data: dict) -> User:
        for key, value in validated_data.items():
            setattr(instance, key, value)
        instance.save()
        return instance


class RegisterUserSerializer(serializers.Serializer):
    username = serializers.CharField(help_text=_("Username."))
    email = serializers.EmailField(help_text=_("User email."))
    password = serializers.CharField(help_text=_("User password."), write_only=True)
    name = serializers.CharField(
        help_text=_("User name."), allow_blank=True, required=False
    )
    avatar = serializers.ImageField(
        help_text=_("User avatar image URL."), allow_null=True, required=False
    )

    def create(self, validated_data: dict) -> User:
        return User.objects.create_user(**validated_data)

    def validate_username(self, value: str) -> str:
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError(_("Username already exists."))
        return value

    def validate_email(self, value: str) -> str:
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError(_("Email already exists."))
        return value

    def validate_password(self, value: str) -> str:
        # Minimum eight characters, at least one uppercase letter, one lowercase
        # letter, one number and one special character
        password_pattern = (
            r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$"
        )

        if not re.match(password_pattern, value):
            raise serializers.ValidationError(
                _(
                    "Password must be at least 8 characters long, "
                    "include at least one uppercase letter, "
                    "one lowercase letter, one number, "
                    "and one special character."
                )
            )

        return value
