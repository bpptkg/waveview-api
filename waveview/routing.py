from django.urls import path

from waveview.websocket.stream import StreamConsumer

websocket_urlpatterns = [
    path(
        "ws/stream/",
        StreamConsumer.as_asgi(),
        name="stream",
    )
]
