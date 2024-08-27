from dataclasses import dataclass

import requests
from django.contrib.auth.backends import BaseBackend
from django.http import HttpRequest

from waveview.users.models import User

BASE_URL = "https://auth.cendana15.com"
TOKEN_URL = f"{BASE_URL}/login"
REFRESH_URL = f"{BASE_URL}/refresh"
REVOKE_URL = f"{BASE_URL}/revoke"
USER_URL = f"https://cendana15.com/user"


@dataclass
class JwtToken:
    access_token: str
    refresh_token: str


@dataclass
class Cendana15User:
    id: int
    username: str
    name: str
    email: str | None
    phone: str | None


class Cendana15Backend(BaseBackend):
    def authenticate(
        self,
        request: HttpRequest,
        username: str | None = None,
        password: str | None = None,
    ) -> User | None:
        try:
            token = self.get_jwt_token(username, password)
        except requests.HTTPError as e:
            if e.response.status_code == 401:
                return None
            raise
        cendana15_user = self.get_user_info(token.access_token)

        try:
            user, created = User.objects.get_or_create(
                username=self.clean_username(cendana15_user.username),
            )
            if created:
                self.configure_user(user, cendana15_user)
        except User.DoesNotExist:
            return None

    def get_user(self, user_id: str) -> User | None:
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None

    def get_jwt_token(self, username: str, password: str) -> JwtToken:
        response = requests.post(
            TOKEN_URL,
            json={"username": username, "password": password},
        )
        response.raise_for_status()
        data = response.json()
        return JwtToken(data["access_token"], data["refresh_token"])

    def refresh_jwt_token(self, refresh_token: str) -> JwtToken:
        response = requests.post(
            REFRESH_URL,
            json={"refresh_token": refresh_token},
        )
        response.raise_for_status()
        data = response.json()
        return JwtToken(data["access_token"], data["refresh_token"])

    def revoke_jwt_token(self, refresh_token: str) -> None:
        response = requests.post(
            REVOKE_URL,
            json={"refresh_token": refresh_token},
        )
        response.raise_for_status()

    def get_user_info(self, access_token: str) -> Cendana15User:
        response = requests.get(
            USER_URL,
            headers={"Authorization": f"Bearer {access_token}"},
        )
        response.raise_for_status()
        data = response.json()
        return Cendana15User(
            id=data["id"],
            username=data["username"],
            name=data.get("name", ""),
            email=data.get("email"),
            phone=data.get("phone"),
        )

    def clean_username(self, username: str) -> str:
        return username.lower().strip()

    def configure_user(self, user: User, cendana15_user: Cendana15User) -> None:
        username = self.clean_username(cendana15_user.username)
        email = cendana15_user.email
        if email is None:
            email = f"{username}@cendana15.com"
        phone = cendana15_user.phone
        user.username = username
        user.email = email
        user.name = cendana15_user.name
        user.phone_number = phone
        user.save()
