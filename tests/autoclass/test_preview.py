from datetime import timedelta
from unittest.mock import Mock

import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from waveview.contrib.autoclass import task
from waveview.contrib.autoclass.client import PredictionError

from .conftest import result_for

pytestmark = pytest.mark.django_db


@pytest.fixture
def local_cache(settings):
    settings.CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "autoclass-preview-tests",
        }
    }


@pytest.fixture
def run_inline(monkeypatch):
    monkeypatch.setattr(
        task.preview_event,
        "apply_async",
        lambda args: task.preview_event(*args),
    )


def test_preview_returns_result_without_writing_event(
    event, local_cache, run_inline, monkeypatch
):
    before = event.autoclass
    monkeypatch.setattr(task, "predict_at", lambda eventid, when: result_for(event))
    when = event.time + timedelta(seconds=30)

    state = task.request_preview(event.catalog, when)

    assert state["state"] == "ok"
    assert state["result"]["type_code"] == "VTB"
    event.refresh_from_db()
    assert event.autoclass == before


def test_repeated_request_dispatches_once_per_whole_second(
    event, local_cache, monkeypatch
):
    dispatch = Mock()
    monkeypatch.setattr(task.preview_event, "apply_async", dispatch)
    when = event.time + timedelta(seconds=30)

    first = task.request_preview(event.catalog, when)
    second = task.request_preview(event.catalog, when.replace(microsecond=400000))

    assert first == {"state": "pending"}
    assert second == {"state": "pending"}
    assert dispatch.call_count == 1


def test_disabled_catalog_is_not_predicted(event, local_cache, settings, monkeypatch):
    settings.AUTOCLASS_CATALOG_IDS = []
    dispatch = Mock()
    monkeypatch.setattr(task.preview_event, "apply_async", dispatch)

    state = task.request_preview(event.catalog, event.time)

    assert state == {"state": "disabled"}
    dispatch.assert_not_called()


@pytest.mark.parametrize(
    "error,state",
    [
        (PredictionError("data_unavailable", True), "data_unavailable"),
        (RuntimeError("boom"), "unavailable"),
    ],
)
def test_failures_are_reported_as_state(
    event, local_cache, run_inline, monkeypatch, error, state
):
    def fail(eventid, when):
        raise error

    monkeypatch.setattr(task, "predict_at", fail)

    result = task.request_preview(event.catalog, event.time)

    assert result == {"state": state}


def test_api_rejects_future_time(event, local_cache):
    client = APIClient()
    client.force_authenticate(user=event.author)
    url = reverse(
        "waveview-api-1-catalog-autoclass-preview",
        kwargs={
            "organization_id": event.catalog.volcano.organization_id,
            "volcano_id": event.catalog.volcano_id,
            "catalog_id": event.catalog_id,
        },
    )

    response = client.post(
        url, {"time": (timezone.now() + timedelta(hours=1)).isoformat()}, format="json"
    )

    assert response.status_code == 400
