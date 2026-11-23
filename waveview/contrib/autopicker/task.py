import logging

from celery import shared_task
from django.utils import timezone
from django.db import transaction
from obspy import UTCDateTime
from waveview.contrib.autoclass.task import enqueue_event
from waveview.contrib.autoclass.webhook import notify_sinoas

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
@transaction.atomic
def create_event(detection_result: dict) -> None:
    result = DetectionResult.from_dict(detection_result)

    if "sof_station" in detection_result:
        # Dari autopicker multi-stasiun (run_multi.py): SOF dan waktu event sudah
        # ditentukan dari pick berkualitas (kelas 0-2). SOF boleh kosong bila tidak
        # ada pick berkualitas; event tetap dibuat.
        sof = detection_result.get("sof_station") or ""
        t_event = UTCDateTime(detection_result.get("event_time") or detection_result["t_on"])
        duration = result.t_off - t_event
    else:
        # Dari autopicker lama (run.py): SOF = pick MEPAC, lalu MEPSL.
        pick = result.get_sof_pick()
        if pick is None:
            logger.error("No SOF pick found in the detection result.")
            return
        sof = pick.stream_id.split(".")[1]
        t_event = pick.t_pick
        duration = result.get_duration()

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
        if sof:
            station_of_first_arrival = Station.objects.get(code=sof)
        else:
            station_of_first_arrival = None
    except Station.DoesNotExist:
        logger.warning(f"Station with code '{sof}' does not exist.")
        station_of_first_arrival = None

    time = timezone.make_aware(t_event.datetime, timezone=timezone.utc)

    event = Event.objects.create(
        catalog=catalog,
        station_of_first_arrival=station_of_first_arrival,
        time=time,
        duration=duration,
        type=event_type,
        note="",
        method="stelte",
        evaluation_mode=EvaluationMode.AUTOMATIC,
        evaluation_status=EvaluationStatus.PRELIMINARY,
        author=user,
    )
    event.collaborators.add(user)
    enqueue_event(event)
    notify_sinoas("created", event)

    payload = NotifyEventData.from_event(
        str(user.id), str(volcano.organization.id), event
    )
    transaction.on_commit(
        lambda: notify_event.delay(OperationType.CREATE, payload.to_dict()), robust=True
    )
