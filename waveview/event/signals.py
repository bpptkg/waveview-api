from typing import Any, Dict

from django.db.models.signals import post_save
from django.dispatch import receiver

from waveview.event.amplitude import register_amplitude_calculators
from waveview.event.models import Attachment, Catalog
from waveview.event.observers import register_observers
from waveview.utils.media import MediaType
from waveview.volcano.models import Volcano

register_observers()
register_amplitude_calculators()


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
