import os

from django.conf import settings

from celery import Celery

__all__ = ("app",)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "waveview.settings")
app = Celery("waveview")

app.config_from_object("django.conf:settings")
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)
