from django.utils.translation import gettext_lazy as _
from rest_framework import serializers


class ObservatoryPostSerializer(serializers.Serializer):
    id = serializers.UUIDField(help_text=_("Observatory post ID."))
    name = serializers.CharField(help_text=_("Observatory post name."))
    description = serializers.CharField(
        help_text=_("Observatory post description."), allow_null=True
    )
