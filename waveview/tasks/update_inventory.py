import logging

from waveview.celery import app
from waveview.inventory.models import InventoryFile
from waveview.inventory.stationxml import StationXMLAdapter

logger = logging.getLogger(__name__)


@app.task(
    name="waveview.tasks.update_inventory",
    default_retry_delay=60 * 5,
    max_retries=None,
)
def update_inventory(file_id: str) -> None:
    try:
        inventory_file = InventoryFile.objects.get(pk=file_id)
    except InventoryFile.DoesNotExist:
        logger.error(f"Inventory with id {file_id} does not exist")
        return

    adapter = StationXMLAdapter(inventory_file)
    adapter.update()
