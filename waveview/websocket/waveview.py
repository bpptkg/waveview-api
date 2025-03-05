import logging

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.layers import get_channel_layer

from waveview.notifications.utils import user_channel
from waveview.websocket.base import (
    CommandType,
    MessageEvent,
    WebSocketMessageType,
    WebSocketResponse,
    WebSocketResponseStatus,
)
from waveview.websocket.join import get_join_channel_data

logger = logging.getLogger(__name__)


class WaveViewConsumer(AsyncJsonWebsocketConsumer):
    joined_channels = set()

    async def connect(self) -> None:
        await self.accept()
        user = self.scope.get("user")
        if user and user.is_authenticated:
            await self.channel_layer.group_add(user_channel(user.pk), self.channel_name)
            self.joined_channels.add(str(user.pk))
            await self.broadcast()
        else:
            await self.close(code=4001)

    async def disconnect(self, code: int) -> None:
        user = self.scope.get("user")
        if user and user.is_authenticated:
            await self.channel_layer.group_discard(
                user_channel(user.pk), self.channel_name
            )
            if str(user.pk) in self.joined_channels:
                self.joined_channels.remove(str(user.pk))
            await self.broadcast()
        await self.close()

    async def notify(self, event: MessageEvent[dict]) -> None:
        response = WebSocketResponse(
            status=WebSocketResponseStatus.SUCCESS,
            type=WebSocketMessageType.NOTIFY,
            command=CommandType.NOTIFY,
            data=event["data"],
        )
        await self.send_json(response.to_dict())

    async def broadcast(self) -> None:
        joined_channels = self.joined_channels.copy()
        data = await database_sync_to_async(get_join_channel_data)(joined_channels)
        channel_layer = get_channel_layer()
        for user_id in joined_channels:
            await channel_layer.group_send(
                user_channel(user_id),
                {
                    "type": "broadcast_message",
                    "data": data,
                },
            )

    async def broadcast_message(self, event: MessageEvent[dict]) -> None:
        response = WebSocketResponse(
            status=WebSocketResponseStatus.SUCCESS,
            type=WebSocketMessageType.RESPONSE,
            command=CommandType.JOIN,
            data=event["data"],
        )
        await self.send_json(response.to_dict())
