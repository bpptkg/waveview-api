import logging

from obspy import Trace
from obspy.clients.seedlink import EasySeedLinkClient

from waveview.inventory.models import Inventory
from waveview.inventory.models.datasource import DataSource, DataSourceType

logger = logging.getLogger(__name__)


class SeedLinkClient(EasySeedLinkClient):
    def on_data(self, trace: Trace) -> None:
        print(trace)


def run_seedlink(inventory_id: str) -> None:
    datasource = DataSource.objects.filter(
        inventory_id=inventory_id, source=DataSourceType.SEEDLINK
    ).first()
    if not datasource:
        logger.error("Seedlink data source not found.")
        return
    server_url = datasource.data.get("server_url")
    if not server_url:
        logger.error("Seedlink server URL not found.")
        return

    client = SeedLinkClient(server_url=server_url, autoconnect=True)

    inventory = Inventory.objects.get(id=inventory_id)
    networks = inventory.networks.all()
    for network in networks:
        for station in network.stations.all():
            for channel in station.channels.all():
                logger.info(
                    f"Subscribing to {network.code}.{station.code}.{channel.code}"
                )
                client.select_stream(
                    net=network.code, station=station.code, selector=channel.code
                )

    client.run()
