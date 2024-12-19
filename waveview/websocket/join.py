from dataclasses import dataclass

from waveview.users.models import User
from waveview.users.serializers import UserSerializer


@dataclass
class JoinChannelData:
    users: list[dict]

    @classmethod
    def from_dict(cls, data: dict) -> "JoinChannelData":
        return cls(
            users=data["users"],
        )

    def to_dict(self) -> dict:
        return {
            "users": self.users,
        }


def get_join_channel_data(ids: list[str]) -> dict:
    users = User.objects.filter(pk__in=ids).all()
    serializer = UserSerializer(users, many=True)
    data = JoinChannelData(users=serializer.data).to_dict()
    return data
