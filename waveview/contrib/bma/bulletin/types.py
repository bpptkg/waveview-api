from dataclasses import dataclass


@dataclass
class BulletinData:
    server_url: str
    token: str

    @classmethod
    def from_dict(cls, data: dict) -> "BulletinData":
        return cls(
            server_url=data["server_url"],
            token=data["token"],
        )
