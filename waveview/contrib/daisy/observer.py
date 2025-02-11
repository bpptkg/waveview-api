import logging
from typing import Any

import requests
from django.conf import settings

from waveview.event.observers import EventObserver

logger = logging.getLogger(__name__)


class DaisyWebhookObserver(EventObserver):
    """
    Observer that sends event data to a DAISY webhook endpoint.

    This observer POSTs event data to the configured webhook URL when events are
    created, updated, or deleted.
    """

    name = "webhook"

    def __init__(self):
        self.webhook_url = getattr(settings, "DAISY_WEBHOOK_URL", "https://cendana15.com/data-entry/veps/webhook")

    def _send_webhook(self, operation: str, event_id: str, data: dict[str, Any]) -> None:
        """Send the webhook request with event data."""
        payload = {
            "operation": operation,
            "event_id": event_id,
            "data": data,
        }
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        try:
            response = requests.post(self.webhook_url, json=payload, headers=headers, timeout=5)
            response.raise_for_status()
            logger.info(f"Webhook {operation} successful for event {event_id}: {response.status_code}")
        except requests.HTTPError:
            logger.error(f"Webhook {operation} failed for event {event_id}: HTTP {response.status_code} - {response.text}")
        except requests.RequestException as e:
            logger.error(f"Webhook {operation} failed for event {event_id}: {str(e)}")

    def create(self, event_id: str, data: dict[str, Any], **options: Any) -> None:
        """Send webhook when a new event is created."""
        self._send_webhook("create", event_id, data)

    def update(self, event_id: str, data: dict[str, Any], **options: Any) -> None:
        """Send webhook when an event is updated."""
        self._send_webhook("update", event_id, data)

    def delete(self, event_id: str, data: dict[str, Any], **options: Any) -> None:
        """Send webhook when an event is deleted."""
        self._send_webhook("delete", event_id, data)
