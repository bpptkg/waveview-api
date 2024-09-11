import logging

from waveview.appconfig.models import MagnitudeConfig
from waveview.celery import app
from waveview.event.magnitude import MagnitudeEstimatorData, registry

logger = logging.getLogger(__name__)


@app.task(
    name="waveview.tasks.calc_magnitude",
    default_retry_delay=60 * 5,
    max_retries=None,
)
def calc_magnitude(
    organization_id: str, volcano_id: str, event_id: str, author_id: str
) -> None:
    configs = MagnitudeConfig.objects.filter(
        organization_id=organization_id,
        volcano_id=volcano_id,
        is_enabled=True,
    ).all()
    for config in configs:
        klass = registry.get(config.method)
        if klass is None:
            logger.error(
                f"Magnitude estimator for method {config.method} is not registered."
            )
            continue
        calculator = klass(config)
        data = MagnitudeEstimatorData(
            organization_id=organization_id,
            volcano_id=volcano_id,
            event_id=event_id,
            author_id=author_id,
        )
        calculator.calc_magnitude(data)
