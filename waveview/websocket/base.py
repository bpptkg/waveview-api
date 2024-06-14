import enum
import json
from dataclasses import dataclass
from typing import Generic, Literal, TypeVar

T = TypeVar("T")


class CommandType(enum.Enum):
    ECHO = "echo"


class WebSocketMessageType(enum.Enum):
    REQUEST = "request"
    RESPONSE = "response"
    NOTIFY = "notify"


class WebSocketResponseStatus(enum.Enum):
    SUCCESS = "success"
    ERROR = "error"


@dataclass
class WebSocketRequest(Generic[T]):
    command: Literal[
        "stream.ssr",
        "stream.fetch",
        "ping",
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


@dataclass
class WebSocketErrorData:
    code: str
    message: str
