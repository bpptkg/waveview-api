import enum
import json
from dataclasses import dataclass
from typing import Generic, TypedDict, TypeVar

T = TypeVar("T")


class ChannelEvent(TypedDict):
    type: str
    data: dict


class CommandType(enum.StrEnum):
    STREAM_FETCH = "stream.fetch"
    STREAM_SPECTROGRAM = "stream.spectrogram"
    PING = "ping"
    NOTIFY = "notify"


class WebSocketMessageType(enum.StrEnum):
    REQUEST = "request"
    RESPONSE = "response"
    NOTIFY = "notify"


class WebSocketResponseStatus(enum.StrEnum):
    SUCCESS = "success"
    ERROR = "error"


@dataclass
class WebSocketRequest(Generic[T]):
    command: CommandType
    data: T

    @staticmethod
    def parse_raw(text_data: str) -> "WebSocketRequest":
        return WebSocketRequest(**json.loads(text_data))


@dataclass
class WebSocketResponse(Generic[T]):
    status: str
    type: str
    command: CommandType
    data: T

    def to_dict(self) -> dict:
        return {
            "status": self.status,
            "type": self.type,
            "command": self.command,
            "data": self.data,
        }


@dataclass
class WebSocketErrorData:
    code: str
    message: str
