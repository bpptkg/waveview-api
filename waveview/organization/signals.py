from typing import Any, Dict

from django.db.models.signals import post_save
from django.dispatch import receiver

from waveview.inventory.models import Inventory
from waveview.organization.models import Organization


@receiver(post_save, sender=Organization)
def organization_post_save(
    sender: Any, instance: Organization, **kwargs: Dict[str, Any]
) -> None:
    user = instance.author
    if not Inventory.objects.filter(organization=instance).exists():
        Inventory.objects.create(organization=instance, name="Default", author=user)
