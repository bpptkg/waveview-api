import logging

from waveview.celery import app
from waveview.inventory.models import Inventory
from waveview.inventory.stationxml import StationXMLAdapter

logger = logging.getLogger(__name__)


@app.task(
    name="waveview.tasks.update_inventory",
    default_retry_delay=60 * 5,
    max_retries=None,
)
def update_inventory(inventory: str) -> None:
    try:
        inventory = Inventory.objects.get(pk=inventory)
    except Inventory.DoesNotExist:
        logger.error(f"Inventory with id {inventory} does not exist")
        return

    adapter = StationXMLAdapter(inventory)
    adapter.update()
