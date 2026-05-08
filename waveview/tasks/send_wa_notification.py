import logging
from datetime import datetime
from zoneinfo import ZoneInfo

import requests
from django.conf import settings

from waveview.celery import app
from waveview.event.models import Event, Amplitude
from waveview.observation.models import PyroclasticFlow
from waveview.whatsapp.models import Group

logger = logging.getLogger(__name__)

INDONESIAN_DAYS = [
    "Senin",
    "Selasa",
    "Rabu",
    "Kamis",
    "Jumat",
    "Sabtu",
    "Minggu",
]

INDONESIAN_MONTHS = [
    "",
    "Januari",
    "Februari",
    "Maret",
    "April",
    "Mei",
    "Juni",
    "Juli",
    "Agustus",
    "September",
    "Oktober",
    "November",
    "Desember",
]


def format_indonesian_date(dt: datetime) -> str:
    day_name = INDONESIAN_DAYS[dt.weekday()]
    month_name = INDONESIAN_MONTHS[dt.month]
    return f"{day_name}, {dt.day} {month_name} {dt.year}"


def format_decimal(value: float) -> str:
    formatted = f"{value:.2f}"
    if "." in formatted:
        formatted = formatted.rstrip("0").rstrip(".")
    return formatted


def get_amplitude(event: Event) -> str:
    manual_analog_method = "manual_analog"
    manual_analog_amplitude = (
        Amplitude.objects.filter(event=event, method=manual_analog_method)
        .order_by("-updated_at")
        .first()
    )
    if (
        manual_analog_amplitude is not None
        and manual_analog_amplitude.amplitude is not None
    ):
        return f"{format_decimal(manual_analog_amplitude.amplitude)} {manual_analog_amplitude.unit}"

    analog_method = "analog"
    amplitude = (
        Amplitude.objects.filter(event=event, method=analog_method)
        .order_by("-updated_at")
        .first()
    )
    if amplitude is None or amplitude.amplitude is None:
        return "tidak dapat ditentukan"
    return f"{format_decimal(amplitude.amplitude)} {amplitude.unit}"


def build_final_message(event: Event, pf: PyroclasticFlow) -> str:
    event_time_wib = event.time.astimezone(ZoneInfo("Asia/Jakarta"))

    tanggal = format_indonesian_date(event_time_wib)
    jam = event_time_wib.strftime("%H.%M")

    if pf.runout_distance == 0:
        runout = "tidak dapat ditentukan"
    else:
        runout = f"{int(pf.runout_distance)} m"

    directions = [fd.name for fd in pf.fall_directions.all()]
    arah = ", ".join(directions) if directions else "visual tidak terlihat"

    message = (
        f"*Info APG:*\n"
        f"Tanggal: {tanggal}\n"
        f"Jam: {jam} WIB\n"
        f"Durasi: {format_decimal(event.duration)} detik\n"
        f"Amplitudo maks: {get_amplitude(event)}\n"
        f"Estimasi jarak luncur: {runout}\n"
        f"Arah: {arah}"
    )

    if settings.BROADCAST_TESTING:
        message = "[Pesan ini hanya untuk uji coba. Mohon diabaikan.]\n" + message

    return message


@app.task(
    name="waveview.tasks.send_wa_notification",
    default_retry_delay=60,
    max_retries=3,
)
def send_wa_notification(event_id: str) -> None:
    try:
        event = Event.objects.get(id=event_id)
    except Event.DoesNotExist:
        logger.error(f"Event with ID {event_id} does not exist.")
        return

    try:
        pf = PyroclasticFlow.objects.get(event=event)
    except PyroclasticFlow.DoesNotExist:
        logger.error(f"No Pyroclastic Flow observation found for event ID {event_id}.")
        return

    groups = Group.objects.filter(excluded=False)
    url = "https://broadcast-api.cendana15.com/messages"
    headers = {
        "Authorization": f"Bearer {settings.BROADCAST_TOKEN}",
        "Content-Type": "application/json",
    }
    final_message = build_final_message(event, pf)
    body = {
        "type": "WA Group",
        "is_wa": 1,
        "is_sms": 0,
        "message": final_message,
        "receiver": [{"id": group.group_id, "name": group.name} for group in groups],
    }

    response = requests.post(url, json=body, headers=headers)
    if response.status_code != 200:
        logger.error(
            f"Failed to send message to WA. Status code: {response.status_code}, Response: {response.text}"
        )
        return

    logger.info(f"Event {event_id} has been sent to WA successfully.")
