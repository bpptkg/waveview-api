from channels.generic.websocket import AsyncWebsocketConsumer

from waveview.signal.packet import get_data
from waveview.websocket.base import WebSocketRequestMessage


class StreamConsumer(AsyncWebsocketConsumer):
    async def connect(self) -> None:
        await self.accept()

    async def receive(self, text_data: str) -> None:
        request = WebSocketRequestMessage.parse_raw(text_data)
        start = request.data["start"]
        end = request.data["end"]
        data = get_data(start, end)
        await self.send(bytes_data=data)
