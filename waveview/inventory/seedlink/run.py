import logging

from obspy import Trace
from obspy.clients.seedlink.slpacket import SLPacket

from waveview.inventory.models import Channel, Inventory
from waveview.inventory.models.datasource import DataSource, DataSourceType
from waveview.inventory.seedlink.client import EasySeedLinkClient, get_statefile
from waveview.inventory.datastream import preparebuffer

logger = logging.getLogger(__name__)


class SeedLinkClient(EasySeedLinkClient):
    def on_data(self, packet: SLPacket) -> None:
        try:
            self._on_data(packet)
        except Exception as e:
            logger.error(f"Error processing packet: {e}")

    def _on_data(self, packet: SLPacket) -> None:
        trace: Trace = packet.get_trace()
        if self.debug:
            logger.info(f"Received packet: {trace}")
        network: str = trace.stats.network
        station: str = trace.stats.station
        channel: str = trace.stats.channel

        instance = Channel.objects.filter(
            code=channel, station__code=station, station__network__code=network
        ).first()
        if not instance:
            logger.error(f"Channel {network}.{station}.{channel} not found.")
            return

        table = instance.get_datastream_id()
        st, et, sr, dtype, buf = preparebuffer(trace)
        self.schema.insert(table, st, et, sr, dtype, buf)


def run_seedlink(inventory_id: str, debug: bool = False) -> None:
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

    statefile = get_statefile()
    client.set_state_file(str(statefile))

    try:
        client.run()
    except KeyboardInterrupt:
        logger.info("Exiting Seedlink client.")
        client.close()
