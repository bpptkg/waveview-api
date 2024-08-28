from typing import Any, Dict

from django.db.models.signals import post_save
from django.dispatch import receiver

from waveview.event.models import Attachment, Catalog, Event
from waveview.tasks.magnitude import calc_magnitude
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
def event_post_save(sender: Any, instance: Event, **kwargs: Dict[str, Any]) -> None:
    event_id = str(instance.id)
    volcano_id = str(instance.catalog.volcano.id)
    organization_id = str(instance.catalog.volcano.organization.id)
    calc_magnitude.delay(organization_id, volcano_id, event_id)
