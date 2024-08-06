from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer

from waveview.signal.packet import FetcherData, StreamFetcher
from waveview.websocket.base import WebSocketRequest


class StreamConsumer(AsyncWebsocketConsumer):
    async def connect(self) -> None:
        await self.accept()

    async def receive(self, text_data: str) -> None:
        request: WebSocketRequest = WebSocketRequest.parse_raw(text_data)
        if request.command == "stream.fetch":
            await self.stream_fetch(request)

    async def stream_fetch(self, request: WebSocketRequest) -> None:
        raw = request.data

        payload = FetcherData.parse_raw(raw)
        fetcher = StreamFetcher()
        data = await database_sync_to_async(fetcher.fetch)(payload)

        await self.send(bytes_data=data)
