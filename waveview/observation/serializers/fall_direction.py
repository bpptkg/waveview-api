from django.utils.translation import gettext_lazy as _
from rest_framework import serializers


class FallDirectionSerializer(serializers.Serializer):
    id = serializers.UUIDField(help_text=_("Fall direction ID."))
    name = serializers.CharField(help_text=_("Fall direction name."))
    description = serializers.CharField(
        help_text=_("Fall direction description."), allow_null=True
    )
