import enum
import json
from dataclasses import dataclass
from typing import Generic, Literal, TypedDict, TypeVar

T = TypeVar("T")


class ChannelEvent(TypedDict):
    type: str
    data: dict


class CommandType(enum.StrEnum):
    ECHO = "echo"


class WebSocketMessageType(enum.StrEnum):
    REQUEST = "request"
    RESPONSE = "response"
    NOTIFY = "notify"


class WebSocketResponseStatus(enum.StrEnum):
    SUCCESS = "success"
    ERROR = "error"


@dataclass
class WebSocketRequest(Generic[T]):
    command: Literal[
        "stream.ssr",
        "stream.fetch",
        "ping",
        "notify",
    ]
    data: T

    @staticmethod
    def parse_raw(text_data: str) -> "WebSocketRequest":
        return WebSocketRequest(**json.loads(text_data))


@dataclass
class WebSocketResponse(Generic[T]):
    status: str
    type: str
    data: T

    def to_dict(self) -> dict:
        return {
            "status": self.status,
            "type": self.type,
            "data": self.data,
        }


@dataclass
class WebSocketErrorData:
    code: str
    message: str
