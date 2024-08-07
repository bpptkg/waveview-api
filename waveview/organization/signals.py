from typing import Any, Dict

from django.db.models.signals import post_save
from django.dispatch import receiver

from waveview.organization.models import Organization, OrganizationSettings


@receiver(post_save, sender=Organization)
def organization_post_save(
    sender: Any, instance: Organization, **kwargs: Dict[str, Any]
) -> None:
    OrganizationSettings.objects.get_or_create(organization=instance)
