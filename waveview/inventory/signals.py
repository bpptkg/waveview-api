from typing import Any, Dict

from django.db import connection
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from waveview.inventory.db.schema import TimescaleSchemaEditor
from waveview.inventory.models import InventoryFile
from waveview.inventory.models.channel import Channel
from waveview.tasks.update_inventory import update_inventory


@receiver(post_save, sender=Channel)
def channel_post_save(sender: Any, instance: Channel, **kwargs: Dict[str, Any]) -> None:
    schema = TimescaleSchemaEditor(connection, atomic=True)
    table = instance.get_datastream_id()
    if not schema.is_table_exists(table):
        schema.create_table(table)
        schema.create_hypertable(table)


@receiver(post_delete, sender=Channel)
def channel_post_delete(
    sender: Any, instance: Channel, **kwargs: Dict[str, Any]
) -> None:
    schema = TimescaleSchemaEditor(connection, atomic=True)
    table = instance.get_datastream_id()
    schema.drop_table(table)


@receiver(post_save, sender=InventoryFile)
def inventory_post_save(
    sender: Any, instance: InventoryFile, **kwargs: Dict[str, Any]
) -> None:
    inventory_id = str(instance.id)
    update_inventory.delay(inventory_id)
