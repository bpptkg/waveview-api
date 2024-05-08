import os
from uuid import uuid4

from django.utils.deconstruct import deconstructible


@deconstructible
class MediaPath(object):
    def __init__(self, path: str) -> None:
        self.path = path

    def __call__(self, instance: object, filename: str) -> str:
        ext = filename.split(".")[-1]
        filename = "{}.{}".format(uuid4(), ext)
        return os.path.join(self.path, filename)
