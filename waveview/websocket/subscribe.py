from dataclasses import dataclass


@dataclass
class StreamSubscribeData:
    channel_ids: list[str]

    @staticmethod
    def from_raw_data(raw: dict) -> "StreamSubscribeData":
        channel_ids = raw.get("channel_ids", [])
        return StreamSubscribeData(channel_ids=channel_ids)


@dataclass
class StreamUnsubscribeData:
    channel_ids: list[str]

    @staticmethod
    def from_raw_data(raw: dict) -> "StreamUnsubscribeData":
        channel_ids = raw.get("channel_ids", [])
        return StreamUnsubscribeData(channel_ids=channel_ids)
