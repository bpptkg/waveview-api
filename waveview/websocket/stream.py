import logging

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer

from waveview.signal.fetcher import FetcherData, get_fetcher
from waveview.websocket.base import WebSocketRequest

logger = logging.getLogger(__name__)


class StreamConsumer(AsyncWebsocketConsumer):
    async def connect(self) -> None:
        if self.scope["user"].is_anonymous:
            await self.close()
        await self.accept()

    async def receive(self, text_data: str) -> None:
        request: WebSocketRequest = WebSocketRequest.parse_raw(text_data)
        if request.command == "stream.fetch":
            await self.stream_fetch(request)

    async def stream_fetch(self, request: WebSocketRequest) -> None:
        raw = request.data

        payload = FetcherData.parse_raw(raw)
        if not payload.channel_id:
            return

        fetcher = get_fetcher()
        data = await database_sync_to_async(fetcher.fetch)(payload)

        await self.send(bytes_data=data)
