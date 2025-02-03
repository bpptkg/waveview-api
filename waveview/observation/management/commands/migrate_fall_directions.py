from typing import Any

from django.core.management.base import BaseCommand
from django.db import transaction

from waveview.observation.models import PyroclasticFlow, Rockfall


class Command(BaseCommand):
    help = "Migrate fall direction foreign key to many to many."

    def handle(self, *args: Any, **options: Any) -> None:
        with transaction.atomic():
            for pyroclastic_flow in PyroclasticFlow.objects.all():
                if pyroclastic_flow.fall_direction is not None:
                    pyroclastic_flow.fall_directions.add(
                        pyroclastic_flow.fall_direction
                    )

            for rockfall in Rockfall.objects.all():
                if rockfall.fall_direction is not None:
                    rockfall.fall_directions.add(rockfall.fall_direction)
