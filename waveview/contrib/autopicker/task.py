import logging

from celery import shared_task
from django.utils import timezone

from waveview.contrib.bpptkg.realtime_detect_pick import DetectionResult
from waveview.event.header import EvaluationMode, EvaluationStatus
from waveview.event.models import Catalog, Event, EventType
from waveview.event.observers import OperationType
from waveview.inventory.models import Station
from waveview.notifications.types import NotifyEventData
from waveview.tasks.notify_event import notify_event
from waveview.users.models import User
from waveview.volcano.models import Volcano

logger = logging.getLogger(__name__)


@shared_task
def create_event(detection_result: dict) -> None:
    result = DetectionResult.from_dict(detection_result)

    user = User.objects.get_or_create(
        email="autopicker@cendana15.com",
        defaults={
            "username": "autopicker",
            "name": "Autopicker",
        },
    )[0]

    try:
        volcano = Volcano.objects.get(slug="merapi")
    except Volcano.DoesNotExist:
        logger.error("Volcano with slug 'merapi' does not exist.")
        return

    try:
        catalog = Catalog.objects.get(volcano=volcano, is_default=True)
    except Catalog.DoesNotExist:
        logger.error("Default catalog for volcano 'merapi' does not exist.")
        return

    try:
        event_type = EventType.objects.get(
            organization=volcano.organization, code="AUTO"
        )
    except EventType.DoesNotExist:
        logger.error("EventType with code 'AUTO' does not exist.")
        return

    try:
        sof = result.get_sof()
        if sof:
            station_of_first_arrival = Station.objects.get(code=sof)
        else:
            station_of_first_arrival = None
    except Station.DoesNotExist:
        logger.warning(f"Station with code '{sof}' does not exist.")
        station_of_first_arrival = None

    time = timezone.make_aware(result.t_on.datetime, timezone=timezone.utc)
    duration = result.get_duration()

    event = Event.objects.create(
        catalog=catalog,
        station_of_first_arrival=station_of_first_arrival,
        time=time,
        duration=duration,
        type=event_type,
        note="",
        method="autopicker/bpptkg",
        evaluation_mode=EvaluationMode.AUTOMATIC,
        evaluation_status=EvaluationStatus.PRELIMINARY,
        author=user,
    )
    event.collaborators.add(user)

    payload = NotifyEventData.from_event(
        str(user.id), str(volcano.organization.id), event
    )
    notify_event.delay(OperationType.CREATE, payload.to_dict())
