import base64
import logging

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer

from waveview.signal.fetcher import FetcherRequestData, get_fetcher_adapter
from waveview.signal.filtering import FilterRequestData, get_filter_adapter
from waveview.signal.spectrogram import SpectrogramRequestData, get_spectrogram_adapter
from waveview.websocket.base import CommandType, MessageEvent, WebSocketRequest
from waveview.websocket.subscribe import StreamSubscribeData, StreamUnsubscribeData

logger = logging.getLogger(__name__)


class StreamConsumer(AsyncWebsocketConsumer):
    async def connect(self) -> None:
        await self.accept()
        self.subscribed_channels = set()
        user = self.scope.get("user")
        if user and user.is_authenticated:
            pass
        else:
            await self.close(code=4001)

    async def disconnect(self, code: int) -> None:
        for channel_id in self.subscribed_channels:
            await self.channel_layer.group_discard(channel_id, self.channel_name)
        self.subscribed_channels.clear()
        await self.close()

    async def receive(self, text_data: str) -> None:
        request: WebSocketRequest = WebSocketRequest.parse_raw(text_data)
        if request.command == CommandType.STREAM_FETCH:
            await self.stream_fetch(request)
        elif request.command == CommandType.STREAM_SPECTROGRAM:
            await self.stream_spectrogram(request)
        elif request.command == CommandType.STREAM_FILTER:
            await self.stream_filter(request)
        elif request.command == CommandType.STREAM_SUBSCRIBE:
            await self.stream_subscribe(request)
        elif request.command == CommandType.STREAM_UNSUBSCRIBE:
            await self.stream_unsubscribe(request)

    async def stream_fetch(self, request: WebSocketRequest) -> None:
        raw = request.data

        payload = FetcherRequestData.from_raw_data(raw)
        if not payload.channel_id:
            return

        fetcher = get_fetcher_adapter()
        data = await database_sync_to_async(fetcher.fetch)(payload)

        await self.send(bytes_data=data)

    async def stream_spectrogram(self, request: WebSocketRequest) -> None:
        raw = request.data

        payload = SpectrogramRequestData.from_raw_data(raw)
        if not payload.channel_id:
            return

        adapter = get_spectrogram_adapter()
        data = await database_sync_to_async(adapter.spectrogram)(payload)

        await self.send(bytes_data=data)

    async def stream_filter(self, request: WebSocketRequest) -> None:
        raw = request.data

        payload = FilterRequestData.from_raw_data(raw)
        if not payload.channel_id:
            return

        adapter = get_filter_adapter()
        data = await database_sync_to_async(adapter.filter)(payload)

        await self.send(bytes_data=data)

    async def stream_subscribe(self, request: WebSocketRequest) -> None:
        raw = request.data
        payload = StreamSubscribeData.from_raw_data(raw)
        for channel_id in payload.channel_ids:
            await self.channel_layer.group_add(channel_id, self.channel_name)
            self.subscribed_channels.add(channel_id)

    async def stream_unsubscribe(self, request: WebSocketRequest) -> None:
        raw = request.data
        payload = StreamUnsubscribeData.from_raw_data(raw)
        for channel_id in payload.channel_ids:
            await self.channel_layer.group_discard(channel_id, self.channel_name)
            self.subscribed_channels.discard(channel_id)

    async def send_trace_buffer(self, event: MessageEvent[str]) -> None:
        data = base64.base64decode(event.data)
        await self.send(bytes_data=data)
