"""Push detector output to SINOAS (Telegram); off while SINOAS_WEBHOOK_URL is empty."""

import logging
from functools import partial

import requests
from django.conf import settings
from django.db import transaction

from waveview.celery import app

logger = logging.getLogger(__name__)


def build_payload(kind, event):
    autoclass = event.autoclass or {}
    result = autoclass.get("result") or {}
    return {
        "kind": kind,
        "event_id": str(event.id),
        "time": event.time.isoformat(),
        "duration": event.duration,
        "method": event.method,
        "type": event.type.code,
        "autoclass": {
            "jenis": result.get("jenis"),
            "prob_jenis": result.get("prob_jenis"),
            "model": result.get("model"),
            "versi": result.get("versi"),
            "applied": autoclass.get("applied", False),
        }
        if kind == "classified"
        else None,
    }


def _dispatch(body):
    # A broker outage must never break detection or classification.
    try:
        send_sinoas_webhook.delay(body)
    except Exception:
        logger.exception("Could not dispatch SINOAS webhook for %s", body["event_id"])


def notify_sinoas(kind, event):
    if not settings.SINOAS_WEBHOOK_URL or event.catalog.volcano.slug != "merapi":
        return
    try:
        transaction.on_commit(partial(_dispatch, build_payload(kind, event)))
    except Exception:
        logger.exception("Could not build SINOAS webhook for event %s", event.id)


@app.task(
    name="waveview.contrib.autoclass.send_sinoas_webhook",
    autoretry_for=(requests.RequestException,),
    retry_backoff=True,
    max_retries=3,
)
def send_sinoas_webhook(body):
    response = requests.post(
        settings.SINOAS_WEBHOOK_URL,
        json=body,
        headers={"X-Token": settings.SINOAS_WEBHOOK_TOKEN},
        timeout=(5, 10),
    )
    response.raise_for_status()
