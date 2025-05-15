from typing import Dict, Type
from uuid import UUID

from django.db import transaction
from django.utils.translation import gettext_lazy as _
from drf_yasg.utils import swagger_serializer_method
from rest_framework import serializers

from waveview.event.header import (
    AmplitudeCategory,
    AmplitudeUnit,
    EvaluationMode,
    EvaluationStatus,
    ObservationType,
)
from waveview.event.models import Amplitude, Attachment, Event, EventType
from waveview.event.serializers.amplitude import AmplitudeSerializer
from waveview.event.serializers.attachment import AttachmentSerializer
from waveview.event.serializers.event_type import EventTypeSerializer
from waveview.event.serializers.magnitude import MagnitudeSerializer
from waveview.event.serializers.origin import OriginSerializer
from waveview.inventory.models import Channel, Station
from waveview.observation.serializers import (
    ExplosionPayloadSerializer,
    ExplosionSerializer,
    PyroclasticFlowPayloadSerializer,
    PyroclasticFlowSerializer,
    RockfallPayloadSerializer,
    RockfallSerializer,
    TectonicPayloadSerializer,
    TectonicSerializer,
    VolcanicEmissionPayloadSerializer,
    VolcanicEmissionSerializer,
)
from waveview.users.models import User
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
    collaborators = UserSerializer(many=True)
    preferred_origin = OriginSerializer(allow_null=True)
    preferred_magnitude = MagnitudeSerializer(allow_null=True)
    preferred_amplitude = AmplitudeSerializer(allow_null=True)
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
        serializer_map: Dict[ObservationType, Type[serializers.Serializer]] = {
            ObservationType.EXPLOSION: ExplosionSerializer,
            ObservationType.PYROCLASTIC_FLOW: PyroclasticFlowSerializer,
            ObservationType.TECTONIC: TectonicSerializer,
            ObservationType.VOLCANIC_EMISSION: VolcanicEmissionSerializer,
            ObservationType.ROCKFALL: RockfallSerializer,
        }
        serializer = serializer_map.get(observation_type)
        if serializer:
            instance = getattr(event, observation_type, None)
            observation = serializer(instance)
            return observation.data
        return None


class AmplitudeManualInputPayloadSerializer(serializers.Serializer):
    channel_id = serializers.UUIDField(help_text=_("Channel ID."))
    amplitude = serializers.FloatField(help_text=_("Amplitude value."), allow_null=True)
    type = serializers.CharField(
        help_text=_("Type of the amplitude, e.g Amax, A10, etc.")
    )
    label = serializers.CharField(help_text=_("Label of the amplitude."))
    method = serializers.CharField(
        help_text=_(
            """
            Method name used to identify the amplitude, e.g veps, seiscomp, etc.
            If channel ID with the same method will be overwrite the existing
            amplitude.
            """
        )
    )
    category = serializers.ChoiceField(
        choices=AmplitudeCategory.choices,
        help_text=_("Category of the amplitude."),
    )
    unit = serializers.ChoiceField(
        choices=AmplitudeUnit.choices, help_text=_("Unit of the amplitude.")
    )
    is_preferred = serializers.BooleanField(
        help_text=_("True if this amplitude is preferred."),
        default=False,
    )
    time = serializers.DateTimeField(
        help_text=_("Reference point in time or central point.")
    )
    begin = serializers.FloatField(
        help_text=_("Duration of time interval before reference point in time window.")
    )
    end = serializers.FloatField(
        help_text=_("Duration of time interval after reference point in time window.")
    )

    def validate_channel_id(self, value: str) -> UUID:
        try:
            channel = Channel.objects.get(id=value)
        except Channel.DoesNotExist:
            raise serializers.ValidationError(_("Channel does not exist."))
        return channel.id


class EventPayloadSerializer(serializers.Serializer):
    station_of_first_arrival_id = serializers.UUIDField(
        help_text=_("Station of the first arrival ID.")
    )
    time = serializers.DateTimeField(
        help_text=_("Time of the event in ISO 8601 format.")
    )
    duration = serializers.FloatField(help_text=_("Duration of the event in seconds."))
    type_id = serializers.UUIDField(help_text=_("Event type ID."))
    note = serializers.CharField(
        help_text=_("Additional note describing the event."),
        allow_blank=True,
        default="",
    )
    method = serializers.CharField(
        help_text=_(
            """
        Method name used to identify the event, e.g veps, seiscomp, etc.
        """
        )
    )
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
        help_text=_(
            """
            Event observation data. The structure of the data depends on the
            event type. For example, if the event type is explosion, the data
            should be in the format of explosion observation. If the event type
            is pyroclastic flow, the data should be in the format of pyroclastic
            flow observation.
            """
        ),
        allow_null=True,
        default=None,
    )
    use_outlier_filter = serializers.BooleanField(
        help_text=_("Use outlier filter when calculating the amplitude."),
        required=False,
        default=False,
    )
    amplitude_manual_inputs = AmplitudeManualInputPayloadSerializer(
        many=True,
        help_text=_("Manual inputs for the amplitude."),
        required=False,
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
            ObservationType.EXPLOSION: ExplosionPayloadSerializer,
            ObservationType.PYROCLASTIC_FLOW: PyroclasticFlowPayloadSerializer,
            ObservationType.TECTONIC: TectonicPayloadSerializer,
            ObservationType.VOLCANIC_EMISSION: VolcanicEmissionPayloadSerializer,
            ObservationType.ROCKFALL: RockfallPayloadSerializer,
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
        amplitude_manual_inputs = validated_data.pop("amplitude_manual_inputs", [])

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
        event.collaborators.add(user)
        Attachment.objects.filter(id__in=attachment_ids).update(event=event)
        self.update_observation(event, observation)
        self.update_amplitude(event, amplitude_manual_inputs, user)
        return event

    @transaction.atomic
    def update(self, instance: Event, validated_data: dict) -> Event:
        user = self.context["request"].user
        attachment_ids = validated_data.pop("attachment_ids", [])
        observation = validated_data.pop("observation", None)
        amplitude_manual_inputs = validated_data.pop("amplitude_manual_inputs", [])
        for key, value in validated_data.items():
            if hasattr(instance, key):
                setattr(instance, key, value)
        if user not in instance.collaborators.all():
            instance.collaborators.add(user)
        instance.save()

        Attachment.objects.filter(id__in=attachment_ids).update(event=instance)
        self.update_observation(instance, observation)
        self.update_amplitude(instance, amplitude_manual_inputs, user)
        return instance

    def update_observation(self, instance: Event, observation: dict | None) -> Event:
        observation_type = instance.type.observation_type
        if observation_type in ObservationType.values:
            if observation is None:
                raise serializers.ValidationError(
                    _("Observation data could not be empty.")
                )

            serializer_map: Dict[ObservationType, Type[serializers.Serializer]] = {
                ObservationType.EXPLOSION: ExplosionPayloadSerializer,
                ObservationType.PYROCLASTIC_FLOW: PyroclasticFlowPayloadSerializer,
                ObservationType.TECTONIC: TectonicPayloadSerializer,
                ObservationType.VOLCANIC_EMISSION: VolcanicEmissionPayloadSerializer,
                ObservationType.ROCKFALL: RockfallPayloadSerializer,
            }

            serializer_class = serializer_map.get(observation_type)
            if not serializer_class:
                raise ValueError(_("Invalid observation type."))

            serializer = serializer_class(
                data=observation, context={"event_id": instance.id}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
        return instance

    def update_amplitude(
        self, instance: Event, amplitude_manual_inputs: list[dict], author: User
    ) -> Event:
        for item in amplitude_manual_inputs:
            amplitude = item["amplitude"]
            channel_id = item["channel_id"]
            label = item["label"]
            method = item["method"]
            category = item["category"]
            unit = item["unit"]
            type = item["type"]
            time = item["time"]
            begin = item["begin"]
            end = item["end"]
            is_preferred = item.get("is_preferred", False)

            channel = Channel.objects.get(id=channel_id)

            Amplitude.objects.update_or_create(
                event=instance,
                waveform=channel,
                method=method,
                defaults={
                    "amplitude": amplitude,
                    "type": type,
                    "category": category,
                    "unit": unit,
                    "evaluation_mode": EvaluationMode.MANUAL,
                    "author": author,
                    "is_preferred": is_preferred,
                    "label": label,
                    "time": time,
                    "begin": begin,
                    "end": end,
                },
            )
        return instance
