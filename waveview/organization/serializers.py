from rest_framework import serializers

from waveview.organization.models import Organization


class OrganizationSerializer(serializers.Serializer):
    class Meta:
        model = Organization
        fields = "__all__"
