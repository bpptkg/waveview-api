from channels.generic.websocket import AsyncWebsocketConsumer

from waveview.signal.packet import FetcherData, StreamFetcher
from waveview.ssr.renderer import Renderer
from waveview.ssr.types import ContextData
from waveview.websocket.base import WebSocketRequest


class StreamConsumer(AsyncWebsocketConsumer):
    async def connect(self) -> None:
        await self.accept()

    async def receive(self, text_data: str) -> None:
        request: WebSocketRequest = WebSocketRequest.parse_raw(text_data)
        if request.command == "stream.ssr":
            await self.render_ssr(request)
        elif request.command == "stream.fetch":
            await self.stream_fetch(request)

    async def render_ssr(self, request: WebSocketRequest) -> None:
        raw = request.data

        context = ContextData.parse_raw(raw)
        renderer = Renderer(context)
        data = renderer.render()

        await self.send(bytes_data=data)

    async def stream_fetch(self, request: WebSocketRequest) -> None:
        raw = request.data

        payload = FetcherData.parse_raw(raw)
        fetcher = StreamFetcher(payload)
        data = fetcher.fetch()

        await self.send(bytes_data=data)
