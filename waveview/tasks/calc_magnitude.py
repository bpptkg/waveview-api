import logging

from waveview.celery import app
from waveview.contrib.magnitude.base import registry

logger = logging.getLogger(__name__)


@app.task(
    name="waveview.tasks.calc_magnitude",
    default_retry_delay=60 * 5,
    max_retries=None,
)
def calc_magnitude(
    organization_id: str, volcano_id: str, event_id: str, author_id: str
) -> None:
    for calculator in registry.get_all().values():
        calculator.calc_magnitude(organization_id, volcano_id, event_id, author_id)
