import logging
from datetime import datetime

from django.db import transaction
from django.utils import timezone
from obspy import UTCDateTime, read_inventory
from obspy.core.inventory import Channel as ObspyChannel
from obspy.core.inventory import Inventory as ObspyInventory
from obspy.core.inventory import Network as ObspyNetwork
from obspy.core.inventory import Station as ObspyStation

from waveview.inventory.header import RestrictedStatus
from waveview.inventory.models import Channel, InventoryFile, Network, Station

logger = logging.getLogger(__name__)


def dt(dt: UTCDateTime | None) -> datetime | None:
    """
    Convert ObsPy UTCDateTime to Django datetime. If dt is None, return None.
    """
    if dt is None:
        return None
    ts = datetime.fromtimestamp(dt.timestamp)
    return timezone.make_aware(ts, timezone.utc)


def f(value: float | None, default: float = 0) -> float:
    """
    Convert value to float. If value is None, return default.
    """
    if value is None:
        return default
    try:
        val = float(value)
    except (ValueError, TypeError):
        val = default
    return val


class StationXMLAdapter:
    def __init__(self, inventory_file: InventoryFile) -> None:
        self.inventory_file = inventory_file
        self.inventory = inventory_file.inventory

    @transaction.atomic
    def update(self) -> None:
        try:
            inv: ObspyInventory = read_inventory(self.inventory_file.file.path)
            for net in inv:
                net: ObspyNetwork
                network = self._update_network(net)
                for sta in net:
                    sta: ObspyStation
                    station = self._update_station(network, sta)
                    for cha in sta:
                        cha: ObspyChannel
                        self._update_channel(station, cha)
        except Exception as e:
            logger.error(f"Failed to update inventory: {e}")

    def _update_network(self, net: ObspyNetwork) -> Network:
        logger.info(f"Updating network {net.code}")
        code = net.code
        alternate_code = net.alternate_code
        start_date = dt(net.start_date)
        end_date = dt(net.end_date)
        historical_code = net.historical_code
        description = net.description
        author = self.inventory.author
        network, __ = Network.objects.update_or_create(
            inventory=self.inventory,
            code=code,
            defaults=dict(
                alternate_code=alternate_code,
                start_date=start_date,
                end_date=end_date,
                historical_code=historical_code,
                description=description,
                author=author,
            ),
        )
        return network

    def _update_station(self, network: Network, sta: ObspyStation) -> Station:
        logger.info(f"Updating station {sta.code}")
        code = sta.code
        alternate_code = sta.alternate_code
        start_date = dt(sta.start_date)
        end_date = dt(sta.end_date)
        historical_code = sta.historical_code
        latitude = sta.latitude
        longitude = sta.longitude
        elevation = sta.elevation
        restricted_status = sta.restricted_status
        if restricted_status is None or restricted_status not in RestrictedStatus:
            restricted_status = RestrictedStatus.OPEN
        description = sta.description
        place = sta.site.region
        country = sta.site.country
        author = self.inventory.author
        station, __ = Station.objects.update_or_create(
            network=network,
            code=code,
            defaults=dict(
                alternate_code=alternate_code,
                start_date=start_date,
                end_date=end_date,
                historical_code=historical_code,
                latitude=latitude,
                longitude=longitude,
                elevation=elevation,
                restricted_status=restricted_status,
                description=description,
                place=place,
                country=country,
                author=author,
            ),
        )
        return station

    def _update_channel(self, station: Station, cha: ObspyChannel) -> Channel:
        logger.info(f"Updating channel {cha.code}.{cha.location_code}")
        code = cha.code
        alternate_code = cha.alternate_code
        start_date = dt(cha.start_date)
        end_date = dt(cha.end_date)
        historical_code = cha.historical_code
        location_code = cha.location_code
        latitude = float(cha.latitude)
        longitude = float(cha.longitude)
        elevation = float(cha.elevation)
        depth = float(cha.depth)
        restricted_status = cha.restricted_status
        if restricted_status is None or restricted_status not in RestrictedStatus:
            restricted_status = RestrictedStatus.OPEN
        description = cha.description
        azimuth = f(cha.azimuth)
        dip = f(cha.dip)
        water_level = f(cha.water_level)
        sample_rate = f(cha.sample_rate, default=1)
        sample_rate_ratio_number_samples = f(
            cha.sample_rate_ratio_number_samples, default=1
        )
        sample_rate_ratio_number_seconds = f(
            cha.sample_rate_ratio_number_seconds, default=1
        )
        clock_drift = f(cha.clock_drift_in_seconds_per_sample)
        calibration_units = cha.calibration_units
        calibration_units_description = cha.calibration_units_description
        author = self.inventory.author
        channel, __ = Channel.objects.update_or_create(
            station=station,
            code=code,
            location_code=location_code,
            defaults=dict(
                alternate_code=alternate_code,
                start_date=start_date,
                end_date=end_date,
                historical_code=historical_code,
                latitude=latitude,
                longitude=longitude,
                elevation=elevation,
                depth=depth,
                azimuth=azimuth,
                dip=dip,
                sample_rate=sample_rate,
                restricted_status=restricted_status,
                description=description,
                water_level=water_level,
                sample_rate_ratio_number_samples=sample_rate_ratio_number_samples,
                sample_rate_ratio_number_seconds=sample_rate_ratio_number_seconds,
                clock_drift=clock_drift,
                calibration_units=calibration_units,
                calibration_units_description=calibration_units_description,
                author=author,
            ),
        )
        return channel
