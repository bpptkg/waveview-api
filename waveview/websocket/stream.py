import logging

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer

from waveview.signal.fetcher import FetcherData, get_fetcher
from waveview.signal.spectrogram import SpectrogramRequestData, get_spectrogram_adapter
from waveview.websocket.base import CommandType, WebSocketRequest

logger = logging.getLogger(__name__)


class StreamConsumer(AsyncWebsocketConsumer):
    async def connect(self) -> None:
        if self.scope["user"].is_authenticated:
            await self.accept()
        else:
            await self.close()

    async def receive(self, text_data: str) -> None:
        request: WebSocketRequest = WebSocketRequest.parse_raw(text_data)
        if request.command == CommandType.STREAM_FETCH:
            await self.stream_fetch(request)
        elif request.command == CommandType.STREAM_SPECTROGRAM:
            await self.stream_spectrogram(request)

    async def stream_fetch(self, request: WebSocketRequest) -> None:
        raw = request.data

        payload = FetcherData.parse_raw(raw)
        if not payload.channel_id:
            return

        fetcher = get_fetcher()
        data = await database_sync_to_async(fetcher.fetch)(payload)

        await self.send(bytes_data=data)

    async def stream_spectrogram(self, request: WebSocketRequest) -> None:
        raw = request.data

        payload = SpectrogramRequestData.parse_raw(raw)
        if not payload.channel_id:
            return

        adapter = get_spectrogram_adapter()
        data = await database_sync_to_async(adapter.spectrogram)(payload)

        await self.send(bytes_data=data)
