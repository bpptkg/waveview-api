import logging

from channels.generic.websocket import AsyncJsonWebsocketConsumer

from waveview.notifications.utils import user_channel
from waveview.websocket.base import (
    CommandType,
    MessageEvent,
    WebSocketMessageType,
    WebSocketResponse,
    WebSocketResponseStatus,
)

logger = logging.getLogger(__name__)


class WaveViewConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self) -> None:
        await self.accept()
        user = self.scope.get("user")
        if user and user.is_authenticated:
            await self.channel_layer.group_add(user_channel(user.pk), self.channel_name)
        else:
            await self.close(code=4001)

    async def disconnect(self, code: int) -> None:
        user = self.scope.get("user")
        if not user:
            return
        if user.is_authenticated:
            self.channel_layer.group_discard(user_channel(user.pk), self.channel_name)

    async def notify(self, event: MessageEvent[dict]) -> None:
        response = WebSocketResponse(
            status=WebSocketResponseStatus.SUCCESS,
            type=WebSocketMessageType.NOTIFY,
            command=CommandType.NOTIFY,
            data=event["data"],
        )
        await self.send_json(response.to_dict())
