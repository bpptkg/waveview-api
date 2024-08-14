from django.utils.translation import gettext_lazy as _
from drf_yasg import openapi
from rest_framework import serializers

from waveview.event.models import Attachment
from waveview.users.serializers import UserSerializer
from waveview.utils.media import MediaType


class AttachmentSerializer(serializers.Serializer):
    id = serializers.UUIDField(help_text=_("Attachment ID."))
    event_id = serializers.UUIDField(help_text=_("Event ID."))
    media_type = serializers.ChoiceField(
        help_text=_("Attachment media type."), choices=MediaType.values
    )
    file = serializers.FileField(help_text=_("Attachment file."))
    thumbnail = serializers.ImageField(
        help_text=_("Attachment thumbnail."), allow_null=True
    )
    name = serializers.CharField(help_text=_("Attachment name."))
    size = serializers.IntegerField(help_text=_("Attachment size in bytes."))
    uploaded_at = serializers.DateTimeField(help_text=_("Attachment upload timestamp."))
    author = UserSerializer()


class AttachmentPayloadSerializer(serializers.Serializer):
    media_type = serializers.ChoiceField(
        help_text=_("Attachment media type."), choices=MediaType.values
    )
    file = serializers.FileField(help_text=_("Attachment file."))

    def create(self, validated_data: dict) -> Attachment:
        file = validated_data["file"]
        user = self.context["request"].user
        validated_data["author"] = user
        validated_data["size"] = file.size
        validated_data["name"] = file.name
        return Attachment.objects.create(**validated_data)

    def validate_file(self, value: bytes) -> bytes:
        if not self.respects_filesize_limit(value.size):
            raise serializers.ValidationError(_("File size exceeds the allowed limit."))
        return value

    def respects_filesize_limit(self, size: int) -> bool:
        MAX_FILE_SIZE = 100 * 1024 * 1024  # 50 MB
        return size <= MAX_FILE_SIZE


AttachmentPayloadSchema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    required=["file", "media_type"],
    properties={
        "file": openapi.Schema(
            type=openapi.TYPE_FILE,
            description="Attachment file. The maximum file size is 50 MB.",
        ),
        "media_type": openapi.Schema(
            type=openapi.TYPE_STRING,
            enum=MediaType.values,
            description="Attachment media type.",
        ),
    },
)
