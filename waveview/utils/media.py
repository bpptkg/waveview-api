import os
from uuid import uuid4

from django.db import models
from django.db.models import Model
from django.utils import timezone
from django.utils.deconstruct import deconstructible


@deconstructible
class MediaPath(object):
    def __init__(self, path: str, prefix: bool = True) -> None:
        self.path = path
        self.prefix = prefix

    def __call__(self, instance: Model, name: str) -> str:
        ext = name.split(".")[-1]
        filename = "{}.{}".format(uuid4(), ext)
        today = timezone.now().date()
        path = today.strftime(self.path)
        if self.prefix:
            if instance.id is None:
                instance.id = uuid4()
            return os.path.join(path, str(instance.id), filename)
        return os.path.join(path, filename)


class MediaType(models.TextChoices):
    PHOTO = "photo", "Photo"
    VIDEO = "video", "Video"
    AUDIO = "audio", "Audio"
    DOCUMENT = "document", "Document"
    OTHER = "other", "Other"
