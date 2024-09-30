from urllib.parse import urljoin, quote

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
