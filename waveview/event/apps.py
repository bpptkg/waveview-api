from django.apps import AppConfig


class EventConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "waveview.event"
    verbose_name = "Event"

    def ready(self) -> None:
        import waveview.event.signals  # noqa
