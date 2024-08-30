from django.urls import path

from waveview.websocket.stream import StreamConsumer
from waveview.websocket.waveview import WaveViewConsumer

websocket_urlpatterns = [
    path(
        "ws/stream/",
        StreamConsumer.as_asgi(),
        name="stream",
    ),
    path(
        "ws/waveview/",
        WaveViewConsumer.as_asgi(),
        name="waveview",
    ),
]
