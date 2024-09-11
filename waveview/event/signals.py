from typing import Any, Dict, Type

from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.module_loading import import_string

from waveview.event.magnitude import (
    BaseMagnitudeEstimator,
    register_magnitude_estimator,
)
from waveview.event.models import Attachment, Catalog, Event
from waveview.event.observers import event_registry
from waveview.utils.media import MediaType
from waveview.volcano.models import Volcano


def setup_magnitude_estimator() -> None:
    for estimator in settings.MAGNITUDE_ESTIMATORS:
        klass: Type[BaseMagnitudeEstimator] = import_string(estimator)
        register_magnitude_estimator(klass.method, klass)


setup_magnitude_estimator()


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
    event_registry.notify(instance)
