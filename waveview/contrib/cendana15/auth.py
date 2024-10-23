import logging
from dataclasses import dataclass

import requests
from django.contrib.auth.backends import BaseBackend
from django.http import HttpRequest

from waveview.organization.models import Organization, OrganizationMember
from waveview.users.models import User

BASE_URL = "https://auth.cendana15.com"
TOKEN_URL = f"{BASE_URL}/login"
REFRESH_URL = f"{BASE_URL}/refresh"
REVOKE_URL = f"{BASE_URL}/revoke"
USER_URL = f"https://cendana15.com/user"

logger = logging.getLogger(__name__)


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
            self.get_jwt_token(username, password)
        except requests.HTTPError as e:
            if e.response.status_code == 401:
                return None
            raise
        cendana15_user = self.get_user_info(username)

        try:
            user, created = User.objects.get_or_create(
                username=self.clean_username(cendana15_user.username),
                defaults={"email": cendana15_user.email, "name": cendana15_user.name},
            )
            if created:
                self.configure_user(user)
        except User.DoesNotExist:
            return None
        return user

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

    def get_user_info(self, username: str) -> Cendana15User:
        return Cendana15User(
            id=username,
            username=username,
            name=username,
            phone=None,
            email=f"{username}@cendana15.com",
        )

    def clean_username(self, username: str) -> str:
        return username.lower().strip()

    def configure_user(self, user: User) -> None:
        self.add_user_to_organization(user)

    def add_user_to_organization(self, user: User) -> None:
        try:
            organization = Organization.objects.get(slug="bpptkg")
        except Organization.DoesNotExist:
            logger.error("Organization with slug 'bpptkg' does not exist")
            return
        if not (
            OrganizationMember.objects.filter(
                user=user, organization=organization
            ).exists()
        ):
            OrganizationMember.objects.create(user=user, organization=organization)
