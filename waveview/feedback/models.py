import uuid

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class Feedback(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Feedback")
        verbose_name_plural = _("Feedback")

    def __str__(self) -> str:
        return f"{self.user}: {self.message}"
