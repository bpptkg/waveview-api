from datetime import datetime
from urllib.parse import quote, urljoin

import pytz
import requests


class BulletinClient:
    def __init__(self, base_url: str, token: str) -> None:
        self.base_url = base_url
        self.api = requests.Session()
        self.api.headers.update(
            {
                "Content-Type": "application/json",
                "Accept": "application/json",
                "Authorization": f"Token {token}",
            }
        )

    def list(self, start: datetime, end: datetime) -> list[dict]:
        tz = pytz.timezone("Asia/Jakarta")
        start = start.astimezone(tz)
        end = end.astimezone(tz)

        url = urljoin(self.base_url, "api/v1/crud/bulletin/")
        try:
            response = self.api.get(url, params={"start": start, "end": end})
        except requests.exceptions.RequestException as e:
            raise Exception("Failed to list events") from e
        if not response.ok:
            raise Exception(f"Failed to list events: {response.text}")
        return response.json()

    def get(self, id: str) -> dict:
        url = urljoin(self.base_url, f"api/v1/crud/bulletin/{quote(id)}/")
        try:
            response = self.api.get(url)
        except requests.exceptions.RequestException as e:
            raise Exception("Failed to get event") from e
        if not response.ok:
            raise Exception(f"Failed to get event: {response.text}")
        return response.json()

    def create(self, payload: dict) -> None:
        url = urljoin(self.base_url, "api/v1/crud/bulletin/")
        try:
            response = self.api.post(url, json=payload)
        except requests.exceptions.RequestException as e:
            raise Exception("Failed to create event") from e
        if not response.ok:
            raise Exception(f"Failed to create event: {response.text}")

    def update(self, id: str, payload: dict) -> None:
        url = urljoin(self.base_url, f"api/v1/crud/bulletin/{quote(id)}/")
        try:
            response = self.api.put(url, json=payload)
        except requests.exceptions.RequestException as e:
            raise Exception("Failed to update event") from e
        if not response.ok:
            raise Exception(f"Failed to update event: {response.text}")

    def delete(self, id: str) -> None:
        url = urljoin(self.base_url, f"api/v1/crud/bulletin/{quote(id)}/")
        try:
            response = self.api.delete(url)
        except requests.exceptions.RequestException as e:
            raise Exception("Failed to delete event") from e
        if not response.ok:
            raise Exception(f"Failed to delete event: {response.text}")
