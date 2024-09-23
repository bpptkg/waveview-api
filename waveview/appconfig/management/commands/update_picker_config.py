import json
from typing import Any

from django.core.management.base import BaseCommand, CommandParser
from rest_framework import serializers

from waveview.appconfig.models import PickerConfig
from waveview.inventory.models import Channel
from waveview.organization.models import Organization
from waveview.volcano.models import Volcano


class ChannelSerializer(serializers.Serializer):
    channel_id = serializers.CharField()
    color = serializers.CharField(allow_null=True, required=False)

    def validate_channel_id(self, value: str) -> str:
        network, station, channel = value.split(".")
        try:
            instance = Channel.objects.filter(
                code=channel, station__code=station, station__network__code=network
            ).get()
        except Channel.DoesNotExist:
            raise serializers.ValidationError("Channel does not exist.")
        return str(instance.id)

    def validate_color(self, value: str | None) -> str | None:
        if value and not value.startswith("#"):
            raise serializers.ValidationError("Invalid color format.")
        return value


class PickerConfigSerializer(serializers.Serializer):
    helicorder_channel = ChannelSerializer()
    seismogram_channels = ChannelSerializer(many=True)
    window_size = serializers.IntegerField()
    force_center = serializers.BooleanField()
    helicorder_interval = serializers.IntegerField()
    helicorder_duration = serializers.IntegerField()


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
