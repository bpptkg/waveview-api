from django.utils.translation import gettext_lazy as _
from rest_framework import serializers


class UserSerializer(serializers.Serializer):
    id = serializers.UUIDField(help_text=_("User ID."))
    username = serializers.CharField(help_text=_("Username."))
    email = serializers.EmailField(help_text=_("User email."))
    name = serializers.CharField(help_text=_("User name."), allow_blank=True)
    date_joined = serializers.DateTimeField(help_text=_("Date when user fist joined."))
    avatar = serializers.ImageField(
        help_text=_("User avatar image URL."), allow_null=True
    )
    bio = serializers.CharField(
        help_text=_("User biography description."), allow_blank=True
    )
    is_staff = serializers.BooleanField(help_text=_("True if user is an admin staff."))
    is_superuser = serializers.BooleanField(
        help_text=_("True if the user is a superuser.")
    )
