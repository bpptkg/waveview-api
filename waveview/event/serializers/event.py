from typing import Dict, Type

from django.db import transaction
from django.utils.translation import gettext_lazy as _
from drf_yasg.utils import swagger_serializer_method
from rest_framework import serializers

from waveview.event.header import EvaluationMode, EvaluationStatus, ObservationType
from waveview.event.models import Attachment, Event, EventType
from waveview.event.serializers.amplitude import AmplitudeSerializer
from waveview.event.serializers.attachment import AttachmentSerializer
from waveview.event.serializers.event_type import EventTypeSerializer
from waveview.event.serializers.magnitude import MagnitudeSerializer
from waveview.event.serializers.origin import OriginSerializer
from waveview.inventory.models import Station
from waveview.observation.serializers import (
    ExplosionSerializer,
    PyroclasticFlowSerializer,
    RockfallSerializer,
    TectonicSerializer,
    VolcanicEmissionSerializer,
)
from waveview.users.serializers import UserSerializer


class EventSerializer(serializers.Serializer):
    id = serializers.UUIDField(help_text=_("Event ID."))
    catalog_id = serializers.UUIDField(help_text=_("Catalog ID."))
    station_of_first_arrival_id = serializers.UUIDField(
        help_text=_("Station of the first arrival ID.")
    )
    time = serializers.DateTimeField(help_text=_("Time of the event."))
    duration = serializers.FloatField(help_text=_("Duration of the event in seconds."))
    type = EventTypeSerializer()
    type_certainty = serializers.CharField(help_text=_("Event type certainty."))
    note = serializers.CharField(help_text=_("Event note."))
    method = serializers.CharField(help_text=_("Event method."))
    evaluation_mode = serializers.ChoiceField(
        help_text=_("Event evaluation mode."), choices=EvaluationMode.choices
    )
    evaluation_status = serializers.ChoiceField(
        help_text=_("Event evaluation status."), choices=EvaluationStatus.choices
    )
    created_at = serializers.DateTimeField(help_text=_("Event creation timestamp."))
    updated_at = serializers.DateTimeField(help_text=_("Event update timestamp."))
    author = UserSerializer()
    preferred_origin = OriginSerializer(allow_null=True)
    preferred_magnitude = MagnitudeSerializer(allow_null=True)
    is_bookmarked = serializers.SerializerMethodField(
        help_text=_("True if bookmarked.")
    )

    @swagger_serializer_method(serializer_or_field=serializers.BooleanField)
    def get_is_bookmarked(self, obj: Event) -> bool:
        if "request" not in self.context:
            return False
        user = self.context["request"].user
        return obj.bookmarked_by.filter(id=user.id).exists()


class EventDetailSerializer(EventSerializer):
    attachments = AttachmentSerializer(many=True)
    amplitudes = AmplitudeSerializer(many=True)
    magnitudes = MagnitudeSerializer(many=True)
    origins = OriginSerializer(many=True)
    observation = serializers.SerializerMethodField(
        help_text=_("Event observation."), allow_null=True
    )

    @swagger_serializer_method(serializer_or_field=serializers.DictField)
    def get_observation(self, event: Event) -> dict | None:
        observation_type = event.type.observation_type
        if observation_type == ObservationType.EXPLOSION:
            serializer = ExplosionSerializer(event.explosion)
        elif observation_type == ObservationType.PYROCLASTIC_FLOW:
            serializer = PyroclasticFlowSerializer(event.pyroclastic_flow)
        elif observation_type == ObservationType.TECTONIC:
            serializer = TectonicSerializer(event.tectonic)
        elif observation_type == ObservationType.VOLCANIC_EMISSION:
            serializer = VolcanicEmissionSerializer(event.volcanic_emission)
        elif observation_type == ObservationType.ROCKFALL:
            serializer = RockfallSerializer(event.rockfall)
        else:
            return None
        return serializer.data


class EventPayloadSerializer(serializers.Serializer):
    station_of_first_arrival_id = serializers.UUIDField(
        help_text=_("Station of the first arrival ID.")
    )
    time = serializers.DateTimeField(help_text=_("Time of the event."))
    duration = serializers.FloatField(help_text=_("Duration of the event in seconds."))
    type_id = serializers.UUIDField(help_text=_("Event type ID."))
    note = serializers.CharField(
        help_text=_("Event note."), allow_blank=True, default=""
    )
    method = serializers.CharField(help_text=_("Event method."))
    evaluation_mode = serializers.ChoiceField(
        help_text=_("Event evaluation mode."), choices=EvaluationMode.choices
    )
    evaluation_status = serializers.ChoiceField(
        help_text=_("Event evaluation status."), choices=EvaluationStatus.choices
    )
    attachment_ids = serializers.ListField(
        child=serializers.UUIDField(), help_text=_("Attachment IDs.")
    )
    observation = serializers.DictField(
        help_text=_("Event observation."),
        allow_null=True,
        default=None,
    )

    def validate_type_id(self, value: str) -> str:
        if not EventType.objects.filter(id=value).exists():
            raise serializers.ValidationError(_("Event type does not exist."))
        return value

    def validate_station_of_first_arrival_id(self, value: str) -> str:
        if not Station.objects.filter(id=value).exists():
            raise serializers.ValidationError(
                {"station_of_first_arrival_id": _("Station does not exist.")}
            )
        return value

    def validate_observation(self, value: dict | None) -> dict | None:
        type_id = self.initial_data.get("type_id")
        if not type_id:
            return None
        try:
            event_type = EventType.objects.get(id=type_id)
        except EventType.DoesNotExist:
            return None
        observation_type = event_type.observation_type
        serializer_map: Dict[ObservationType, Type[serializers.Serializer]] = {
            ObservationType.EXPLOSION: ExplosionSerializer,
            ObservationType.PYROCLASTIC_FLOW: PyroclasticFlowSerializer,
            ObservationType.TECTONIC: TectonicSerializer,
            ObservationType.VOLCANIC_EMISSION: VolcanicEmissionSerializer,
            ObservationType.ROCKFALL: RockfallSerializer,
        }

        serializer_class = serializer_map.get(observation_type)
        if serializer_class:
            serializer = serializer_class(data=value)
            serializer.is_valid(raise_exception=True)
            return serializer.validated_data

        return None

    @transaction.atomic
    def create(self, validated_data: dict) -> Event:
        user = self.context["request"].user
        catalog_id = self.context["catalog_id"]

        station_of_first_arrival_id = validated_data["station_of_first_arrival_id"]
        time = validated_data["time"]
        duration = validated_data["duration"]
        type_id = validated_data["type_id"]
        note = validated_data["note"]
        attachment_ids = validated_data["attachment_ids"]
        method = validated_data["method"]
        evaluation_mode = validated_data["evaluation_mode"]
        evaluation_status = validated_data["evaluation_status"]
        observation = validated_data["observation"]

        event = Event.objects.create(
            catalog_id=catalog_id,
            station_of_first_arrival_id=station_of_first_arrival_id,
            time=time,
            duration=duration,
            type_id=type_id,
            note=note,
            author=user,
            method=method,
            evaluation_mode=evaluation_mode,
            evaluation_status=evaluation_status,
        )
        Attachment.objects.filter(id__in=attachment_ids).update(event=event)
        self.update_observation(event, observation)
        return event

    @transaction.atomic
    def update(self, instance: Event, validated_data: dict) -> Event:
        attachment_ids = validated_data.pop("attachment_ids", [])
        observation = validated_data.pop("observation", None)
        for key, value in validated_data.items():
            setattr(instance, key, value)
        instance.save()

        Attachment.objects.filter(id__in=attachment_ids).update(event=instance)
        self.update_observation(instance, observation)
        return instance

    def update_observation(self, instance: Event, observation: dict | None) -> Event:
        observation_type = instance.type.observation_type
        if observation_type in ObservationType:
            if observation is None:
                raise ValueError(_("Observation data could not be empty."))

            serializer_map: Dict[ObservationType, Type[serializers.Serializer]] = {
                ObservationType.EXPLOSION: ExplosionSerializer,
                ObservationType.PYROCLASTIC_FLOW: PyroclasticFlowSerializer,
                ObservationType.TECTONIC: TectonicSerializer,
                ObservationType.VOLCANIC_EMISSION: VolcanicEmissionSerializer,
                ObservationType.ROCKFALL: RockfallSerializer,
            }

            serializer_class = serializer_map.get(observation_type)
            if not serializer_class:
                raise ValueError(_("Invalid observation type."))

            serializer = serializer_class(
                instance, data=observation, context={"event_id": instance.id}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
        return instance
