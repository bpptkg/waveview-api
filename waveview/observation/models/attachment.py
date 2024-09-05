import os
import tempfile
import uuid
from io import BytesIO

from django.conf import settings
from django.core.files.base import ContentFile
from django.db import models
from moviepy.editor import ImageClip, VideoFileClip
from PIL import Image

from waveview.utils.media import MediaType


class BaseAttachment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    media_type = models.CharField(max_length=255, choices=MediaType.choices)
    file = models.FileField()
    thumbnail = models.ImageField(null=True, blank=True)
    name = models.CharField(max_length=255)
    size = models.PositiveIntegerField()
    uploaded_at = models.DateTimeField(auto_now_add=True)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )

    class Meta:
        abstract = True

    def __str__(self) -> str:
        return self.name

    def delete(self, *args, **kwargs) -> None:
        self.file.delete(save=False)
        if self.thumbnail:
            self.thumbnail.delete(save=False)
        super().delete(*args, **kwargs)

    def generate_thumbnail(self) -> None:
        if self.media_type == MediaType.PHOTO:
            self.generate_photo_thumbnail()
        elif self.media_type == MediaType.VIDEO:
            self.generate_video_thumbnail()

    def generate_photo_thumbnail(self) -> None:
        with Image.open(self.file) as img:
            img.thumbnail((300, 300))
            thumb_io = BytesIO()
            img.save(thumb_io, img.format)
            self.thumbnail.save(
                f"thumb-{self.file.name}",
                ContentFile(thumb_io.getvalue(), name=f"thumb-{self.file.name}"),
                save=False,
            )
            self.save()

    def generate_video_thumbnail(self) -> None:
        with VideoFileClip(self.file.path) as clip:
            thumbnail_filename = f"{uuid.uuid4()}.jpg"
            thumbnail_path = os.path.join(tempfile.gettempdir(), thumbnail_filename)
            thumbnail_time = clip.duration / 2

            thumbnail = clip.get_frame(thumbnail_time)
            thumbnail_image = ImageClip(thumbnail)
            thumbnail_image.save_frame(thumbnail_path)

            with open(thumbnail_path, "rb") as f:
                self.thumbnail.save(
                    thumbnail_filename,
                    ContentFile(f.read(), name=thumbnail_filename),
                    save=True,
                )
            os.remove(thumbnail_path)
            self.save()
