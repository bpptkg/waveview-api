import docker.errors
from docker.models.containers import Container

import docker
from waveview.inventory.models import Inventory


class ContainerManager:
    def __init__(self, inventory: Inventory) -> None:
        self.client = docker.from_env()
        self.inventory = inventory
        self.container_name = inventory.get_seedlink_container_name()
        self.image_name = "seedlink:latest"
        self.network_name = "wv_network"

    def get_or_create_container(self) -> Container:
        try:
            container = self.client.containers.get(self.container_name)
        except docker.errors.NotFound:
            container = self.client.containers.run(
                self.image_name,
                name=self.container_name,
                detach=True,
                network=self.network_name,
                command=str(self.inventory.id),
            )
        return container

    def start(self) -> None:
        container = self.get_or_create_container()
        container.start()

    def stop(self) -> None:
        container = self.get_or_create_container()
        container.stop()

    def restart(self) -> None:
        container = self.get_or_create_container()
        container.restart()

    def get_status(self) -> str:
        container = self.get_or_create_container()
        return container.status
