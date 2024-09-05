from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from waveview.feedback.models import Feedback


class FeedbackSerializer(serializers.Serializer):
    id = serializers.UUIDField(read_only=True, help_text=_("Feedback ID"))
    user = serializers.UUIDField(read_only=True, help_text=_("User ID"))
    message = serializers.CharField(read_only=True, help_text=_("Feedback message"))
    created_at = serializers.DateTimeField(
        read_only=True, help_text=_("Feedback creation time")
    )
    updated_at = serializers.DateTimeField(
        read_only=True, help_text=_("Feedback update time")
    )


class FeedbackPayloadSerializer(serializers.Serializer):
    message = serializers.CharField(help_text=_("Feedback message"))

    def create(self, validated_data: dict) -> Feedback:
        user = self.context["request"].user
        message = validated_data["message"]
        return Feedback.objects.create(user=user, message=message)
