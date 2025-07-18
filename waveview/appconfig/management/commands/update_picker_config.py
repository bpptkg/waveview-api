import json
from typing import Any

from django.core.management.base import BaseCommand, CommandParser
from rest_framework import serializers

from waveview.appconfig.models import PickerConfig
from waveview.appconfig.models.picker import build_filter_config
from waveview.inventory.models import Channel
from waveview.organization.models import Organization
from waveview.volcano.models import Volcano


class ChannelSerializer(serializers.Serializer):
    channel_id = serializers.CharField()
    color = serializers.CharField(allow_null=True, required=False)
    label = serializers.CharField(allow_null=True, required=False)
    is_analog = serializers.BooleanField(allow_null=True, required=False)
    slope = serializers.FloatField(allow_null=True, required=False)
    offset = serializers.FloatField(allow_null=True, required=False)

    def validate_channel_id(self, value: str) -> str:
        network, station, channel = value.split(".")
        try:
            instance = Channel.objects.filter(
                code=channel, station__code=station, station__network__code=network
            ).get()
        except Channel.DoesNotExist:
            raise serializers.ValidationError(f"Channel does not exist: {value}")
        return str(instance.id)

    def validate_color(self, value: str | None) -> str | None:
        if value and not value.startswith("#"):
            raise serializers.ValidationError("Invalid color format.")
        return value


class AmplitudeManualInputSerializer(serializers.Serializer):
    channel_id = serializers.CharField()
    label = serializers.CharField()
    method = serializers.CharField()
    category = serializers.CharField()
    unit = serializers.CharField()
    type = serializers.CharField()
    is_preferred = serializers.BooleanField(default=False)

    def validate_channel_id(self, value: str) -> str:
        network, station, channel = value.split(".")
        try:
            instance = Channel.objects.filter(
                code=channel, station__code=station, station__network__code=network
            ).get()
        except Channel.DoesNotExist:
            raise serializers.ValidationError(f"Channel does not exist: {value}")
        return str(instance.id)


class AmplitudeConfigSerializer(serializers.Serializer):
    amplitude_calculator = serializers.CharField()
    channels = ChannelSerializer(many=True)
    manual_inputs = AmplitudeManualInputSerializer(many=True, required=False)


class PickerConfigSerializer(serializers.Serializer):
    helicorder_channel = ChannelSerializer()
    helicorder_filter = serializers.JSONField(default=dict)
    helicorder_filters = serializers.JSONField(default=list)
    seismogram_filters = serializers.JSONField(default=list)
    seismogram_channels = ChannelSerializer(many=True)
    window_size = serializers.IntegerField()
    force_center = serializers.BooleanField()
    helicorder_interval = serializers.IntegerField()
    helicorder_duration = serializers.IntegerField()
    amplitude_config = AmplitudeConfigSerializer()

    def validate_helicorder_filter(self, value: dict | None) -> dict | None:
        if value is not None:
            return build_filter_config(value).to_dict()
        return None

    def validate_seismogram_filters(self, items: list) -> list[dict]:
        validated = []
        for item in items:
            fi = build_filter_config(item)
            validated.append(fi.to_dict())
        return validated

    def validate_helicorder_filters(self, items: list) -> list[dict]:
        validated = []
        for item in items:
            fi = build_filter_config(item)
            validated.append(fi.to_dict())
        return validated


class Command(BaseCommand):
    help = "Update picker configuration for certain organization and volcano."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("path", type=str, help="Path to the JSON config file.")
        parser.add_argument("org", type=str, help="Organization slug.")
        parser.add_argument("volcano", type=str, help="Volcano slug.")

    def handle(self, *args: Any, **options: Any) -> None:
        path = options["path"]
        with open(path) as f:
            config = json.load(f)

        org = Organization.objects.get(slug=options["org"])
        volcano = Volcano.objects.get(slug=options["volcano"])

        serializer = PickerConfigSerializer(data=config)
        serializer.is_valid(raise_exception=True)

        __, created = PickerConfig.objects.update_or_create(
            organization=org,
            volcano=volcano,
            defaults={"data": serializer.validated_data},
        )
        if created:
            self.stdout.write(self.style.SUCCESS("Picker config created."))
        else:
            self.stdout.write(self.style.SUCCESS("Picker config updated."))
