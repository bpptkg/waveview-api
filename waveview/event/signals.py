from typing import Any, Dict

from django.db.models.signals import post_save
from django.dispatch import receiver

from waveview.event.models import Catalog
from waveview.volcano.models import Volcano


@receiver(post_save, sender=Volcano)
def volcano_post_save(sender: Any, volcano: Volcano, **kwargs: Dict[str, Any]) -> None:
    if Catalog.objects.filter(volcano_id=volcano.id).exists():
        return
    Catalog.objects.create(
        volcano_id=volcano.id,
        name=volcano.name,
        description=f"Default catalog for {volcano.name}.",
        is_default=True,
        author=volcano.author,
    )
