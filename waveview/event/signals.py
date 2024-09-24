from typing import Any, Dict

from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from waveview.event.models import Attachment, Catalog, Event
from waveview.tasks.notify_event_observer import OperationType, notify_event_observer
from waveview.utils.media import MediaType
from waveview.volcano.models import Volcano


@receiver(post_save, sender=Volcano)
def volcano_post_save(sender: Any, instance: Volcano, **kwargs: Dict[str, Any]) -> None:
    if Catalog.objects.filter(volcano_id=instance.id).exists():
        return
    Catalog.objects.create(
        volcano=instance,
        name=instance.name,
        description=f"Default catalog for {instance.name}.",
        is_default=True,
        author=instance.author,
    )


@receiver(post_save, sender=Attachment)
def attachment_post_save(
    sender: Any, instance: Attachment, **kwargs: Dict[str, Any]
) -> None:
    if (
        instance.media_type in [MediaType.PHOTO, MediaType.VIDEO]
        and not instance.thumbnail
    ):
        instance.generate_thumbnail()


@receiver(post_save, sender=Event)
def event_post_save(
    sender: Any, instance: Event, created: bool, **kwargs: Dict[str, Any]
) -> None:
    event_id: str = str(instance.id)
    volcano_id: str = str(instance.catalog.volcano.id)
    if created:
        operation = OperationType.CREATE
    else:
        operation = OperationType.UPDATE
    notify_event_observer.delay(operation, event_id, volcano_id)


@receiver(post_delete, sender=Event)
def event_post_delete(sender: Any, instance: Event, **kwargs: Dict[str, Any]) -> None:
    event_id: str = str(instance.id)
    volcano_id: str = str(instance.catalog.volcano.id)
    notify_event_observer.delay(OperationType.DELETE, event_id, volcano_id)
