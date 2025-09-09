from dataclasses import dataclass
from datetime import datetime


@dataclass
class PickAssistantInput:
    t_onset: datetime
    pre_noise: float = 3.0
    post_noise: float = 237.0


@dataclass
class PickAssistantOutput:
    start: datetime
    end: datetime
    duration: float
    stream_id: str
    channel_id: str
