import base64
import binascii
import imghdr
import io
import uuid

from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils.translation import gettext_lazy as _
from rest_framework.serializers import ImageField, ValidationError


class FlexibleImageField(ImageField):
    EMPTY_VALUES = (None, "", [], (), {})
    ALLOWED_TYPES = ("jpeg", "jpg", "png", "gif")
    INVALID_FILE_MESSAGE = _("Please upload a valid image.")
    INVALID_TYPE_MESSAGE = _("The type of the image couldn't be determined.")

    def get_file_extension(self, filename, decoded_file):
        try:
            from PIL import Image
        except ImportError:
            raise ImportError("Pillow is not installed.")
        extension = imghdr.what(filename, decoded_file)

        # Try with PIL as fallback if format not detected due
        # to bug in imghdr https://bugs.python.org/issue16512
        if extension is None:
            try:
                image = Image.open(io.BytesIO(decoded_file))
            except OSError:
                raise ValidationError(self.INVALID_FILE_MESSAGE)

            extension = image.format.lower()

        extension = "jpg" if extension == "jpeg" else extension
        return extension

    def get_file_name(self, decoded_file):
        return str(uuid.uuid4())

    def to_internal_value(self, data):
        if data in self.EMPTY_VALUES:
            return None

        if isinstance(data, str):
            file_mime_type = None

            if ";base64," in data:
                header, data = data.split(";base64,")
                file_mime_type = header.replace("data:", "")

            try:
                decoded_file = base64.b64decode(data)
            except (TypeError, binascii.Error, ValueError):
                raise ValidationError(self.INVALID_FILE_MESSAGE)

            file_name = self.get_file_name(decoded_file)

            file_extension = self.get_file_extension(file_name, decoded_file)

            if file_extension not in self.ALLOWED_TYPES:
                raise ValidationError(self.INVALID_TYPE_MESSAGE)

            complete_file_name = file_name + "." + file_extension
            data = SimpleUploadedFile(
                name=complete_file_name,
                content=decoded_file,
                content_type=file_mime_type,
            )

        return super().to_internal_value(data)
