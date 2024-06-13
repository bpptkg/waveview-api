import enum
import json
from dataclasses import dataclass
from typing import Generic, TypeVar

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
class WebSocketRequestMessage(Generic[T]):
    command: str
    data: T

    @staticmethod
    def parse_raw(text_data: str) -> "WebSocketRequestMessage":
        return WebSocketRequestMessage(**json.loads(text_data))


@dataclass
class WebSocketResponseMessage(Generic[T]):
    status: str
    type: str
    data: T


@dataclass
class WebSocketErrorData:
    code: str
    message: str
