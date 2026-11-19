from unittest.mock import Mock

import pytest

from waveview.contrib.autoclass import task, webhook

from .conftest import result_for

pytestmark = pytest.mark.django_db


@pytest.fixture
def sent(settings, monkeypatch):
    settings.SINOAS_WEBHOOK_URL = "http://sinoas/api/veps-event"
    settings.SINOAS_WEBHOOK_TOKEN = "secret"
    delay = Mock()
    monkeypatch.setattr(webhook.send_sinoas_webhook, "delay", delay)
    return delay


def test_created_payload_has_no_autoclass(
    event, sent, django_capture_on_commit_callbacks
):
    # on_commit callbacks never fire inside the test transaction unless captured.
    with django_capture_on_commit_callbacks(execute=True):
        webhook.notify_sinoas("created", event)
    body = sent.call_args.args[0]
    assert body["kind"] == "created"
    assert body["event_id"] == str(event.id)
    assert body["type"] == "AUTO"
    assert body["autoclass"] is None


def test_disabled_without_url(event, settings, monkeypatch):
    settings.SINOAS_WEBHOOK_URL = ""
    delay = Mock()
    monkeypatch.setattr(webhook.send_sinoas_webhook, "delay", delay)
    webhook.notify_sinoas("created", event)
    delay.assert_not_called()


def test_classified_sent_after_success(
    event, sent, monkeypatch, django_capture_on_commit_callbacks
):
    task.enqueue_event(event)
    monkeypatch.setattr(task, "predict", lambda e: result_for(e))
    with django_capture_on_commit_callbacks(execute=True):
        task.classify_event(str(event.id))
    body = sent.call_args.args[0]
    assert body["kind"] == "classified"
    assert body["autoclass"]["jenis"] == "VTB"
    assert body["autoclass"]["prob_jenis"] == 0.93
    assert body["autoclass"]["applied"] is True


def test_broker_failure_is_swallowed(event, sent, django_capture_on_commit_callbacks):
    sent.side_effect = RuntimeError("broker down")
    with django_capture_on_commit_callbacks(execute=True):
        webhook.notify_sinoas("created", event)
    sent.assert_called_once()


def test_post_sends_token(settings, monkeypatch):
    settings.SINOAS_WEBHOOK_URL = "http://sinoas/api/veps-event"
    settings.SINOAS_WEBHOOK_TOKEN = "secret"
    post = Mock()
    monkeypatch.setattr(webhook.requests, "post", post)
    webhook.send_sinoas_webhook({"kind": "created"})
    assert post.call_args.kwargs["headers"] == {"X-Token": "secret"}
