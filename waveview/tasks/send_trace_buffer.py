import logging

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from waveview.celery import app

logger = logging.getLogger(__name__)


@app.task(
    name="waveview.tasks.send_trace_buffer",
    autoretry_for=(),
    max_retries=0,
)
def send_trace_buffer(channel_id: str, buffer: str) -> None:
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        channel_id,
        {
            "type": "send_trace_buffer",
            "data": buffer,
        },
    )
