from django.apps import AppConfig


class OrganizationConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "waveview.organization"

    def ready(self) -> None:
        import waveview.organization.signals  # noqa
