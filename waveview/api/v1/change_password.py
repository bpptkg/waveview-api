from django.utils import timezone
from django.utils.crypto import constant_time_compare
from django.utils.translation import gettext_lazy as _
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import serializers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from waveview.api.base import Endpoint
from waveview.users.models import User


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(help_text=_("Old password."))
    new_password = serializers.CharField(help_text=_("New password."))
    new_password_verify = serializers.CharField(help_text=_("New password verify."))

    def validate_old_password(self, value: str) -> str:
        user: User = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError(
                _("The password you entered is not correct.")
            )
        return value

    def validate(self, attrs: dict) -> dict:
        if not constant_time_compare(
            attrs["new_password"], attrs["new_password_verify"]
        ):
            raise serializers.ValidationError(
                _("The passwords you entered did not match.")
            )
        if constant_time_compare(attrs["old_password"], attrs["new_password"]):
            raise serializers.ValidationError(
                _("You can't use old password as a new password.")
            )
        return attrs

    def save(self, **kwargs) -> User:
        new_password = self.validated_data["new_password"]
        user: User = self.context["request"].user
        user.set_password(new_password)
        user.last_password_change = timezone.now()
        user.save()
        return user


class ChangePasswordEndpoint(Endpoint):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_id="Change Password",
        operation_description=(
            """
            Change current user password. Changing password will not invalidate
            previous access token. So, the token remains valid until it's
            expired.
            """
        ),
        tags=["Account"],
        request_body=ChangePasswordSerializer,
        responses={
            status.HTTP_204_NO_CONTENT: openapi.Response("No Content"),
        },
    )
    def post(self, request: Request) -> Response:
        serializer = ChangePasswordSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(status=status.HTTP_204_NO_CONTENT)
