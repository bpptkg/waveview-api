import logging

from channels.generic.websocket import AsyncJsonWebsocketConsumer

from waveview.notifications.utils import user_channel
from waveview.websocket.base import (
    ChannelEvent,
    CommandType,
    WebSocketMessageType,
    WebSocketResponse,
    WebSocketResponseStatus,
)

logger = logging.getLogger(__name__)


class WaveViewConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self) -> None:
        user = self.scope["user"]
        if user.is_anonymous:
            await self.close()
        else:
            await self.channel_layer.group_add(user_channel(user.pk), self.channel_name)
            await self.accept()

    def disconnect(self, close_code: int) -> None:
        user = self.scope["user"]
        if user.is_authenticated:
            self.channel_layer.group_discard(
                user_channel(self.user.pk), self.channel_name
            )

    async def notify(self, event: ChannelEvent) -> None:
        response = WebSocketResponse(
            status=WebSocketResponseStatus.SUCCESS,
            type=WebSocketMessageType.NOTIFY,
            command=CommandType.NOTIFY,
            data=event["data"],
        )
        await self.send_json(response.to_dict())
