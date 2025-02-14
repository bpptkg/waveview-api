import re
from io import BytesIO

from django.core.files.uploadedfile import InMemoryUploadedFile
from django.utils.translation import gettext_lazy as _
from drf_yasg.utils import swagger_serializer_method
from phonenumber_field.serializerfields import PhoneNumberField
from PIL import Image
from rest_framework import serializers

from waveview.users.models import User


class UserSerializer(serializers.Serializer):
    id = serializers.UUIDField(help_text=_("User ID."))
    username = serializers.CharField(help_text=_("Username."))
    name = serializers.CharField(help_text=_("User name."), allow_blank=True)
    avatar = serializers.ImageField(
        help_text=_("User avatar image URL."), allow_null=True
    )


def get_organization_membership_serializer():
    from waveview.organization.serializers import OrganizationMembershipSerializer

    return OrganizationMembershipSerializer(many=True)


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
    organization_memberships = serializers.SerializerMethodField()

    @swagger_serializer_method(
        serializer_or_field=get_organization_membership_serializer()
    )
    def get_organization_memberships(self, instance: User) -> list:
        from waveview.organization.serializers import OrganizationMembershipSerializer

        return OrganizationMembershipSerializer(
            instance.organization_memberships, many=True
        ).data


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
    email = serializers.EmailField(
        help_text=_("User email."), allow_blank=True, required=False
    )
    phone_number = PhoneNumberField(
        help_text=_("User phone number."), allow_blank=True, required=False
    )

    def validate_avatar(self, value: InMemoryUploadedFile) -> InMemoryUploadedFile:
        if value:
            if value.size > 5 * 1024 * 1024:
                raise serializers.ValidationError(_("Avatar file too large."))
            try:
                image = Image.open(value)
            except Exception:
                raise serializers.ValidationError(_("Invalid image file."))

            if image.mode in ("RGBA", "LA"):
                background = Image.new("RGB", image.size, (255, 255, 255))
                background.paste(image, mask=image.split()[3])
                image = background
            elif image.mode != "RGB":
                image = image.convert("RGB")

            output = BytesIO()
            image.save(output, format="JPEG", quality=85)
            output.seek(0)
            value = InMemoryUploadedFile(
                output, "ImageField", value.name, "image/jpeg", output.tell(), None
            )
        return value

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
