from datetime import timedelta
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from django.utils import timezone

from waveview.contrib.autoclass import task
from waveview.contrib.autoclass.client import PredictionError, predict
from waveview.contrib.autoclass.task import _dispatch
from waveview.event.models import Event, EventType
from waveview.event.serializers.event import EventPayloadSerializer

from .conftest import result_for

pytestmark = pytest.mark.django_db


def run_prediction(event, monkeypatch, **result):
    task.enqueue_event(event)
    monkeypatch.setattr(task, "predict", lambda e: result_for(e, **result))
    task.classify_event(str(event.id))
    event.refresh_from_db()
    return event


def test_disabled_catalog_has_no_work(event, settings):
    settings.AUTOCLASS_CATALOG_IDS = []
    task.enqueue_event(event)
    event.refresh_from_db()
    assert event.autoclass is None


def test_schedule_uses_event_time_and_survives_broker_failure(event, monkeypatch):
    event.time = timezone.now()
    event.save(update_fields=["time"])
    task.enqueue_event(event)
    event.refresh_from_db()
    assert event.autoclass["state"] == "pending"
    assert timezone.datetime.fromisoformat(
        event.autoclass["due_at"]
    ) == event.time + timedelta(seconds=150)
    task.classify_event(str(event.id))
    event.refresh_from_db()
    assert event.autoclass["attempts"] == 0


@pytest.mark.parametrize(
    "kind,code",
    [
        ("VTA", "VTA"),
        ("VTB", "VTB"),
        ("MP", "MP"),
        ("LF", "LF"),
        ("TECT", "TECT"),
        ("DG", "GASBURST"),
        ("RF", "ROCKFALL"),
        ("APG", "AWANPANAS"),
    ],
)
def test_prediction_maps_type_without_validation(event, monkeypatch, kind, code):
    run_prediction(
        event,
        monkeypatch,
        jenis=kind,
        kelas="APRF_1" if kind in ("RF", "APG") else kind,
    )
    assert event.type.code == code
    assert (event.evaluation_mode, event.evaluation_status) == (
        "automatic",
        "preliminary",
    )
    assert event.method == "stelte"
    assert event.autoclass["state"] == "succeeded"
    assert event.autoclass["result"]["jenis"] == kind


def test_manual_veps_prediction_keeps_operator_type(event, monkeypatch):
    event.type = EventType.objects.get(
        organization=event.catalog.volcano.organization, code="MP"
    )
    event.method = "veps"
    event.evaluation_mode = "manual"
    event.evaluation_status = "confirmed"
    event.save()

    run_prediction(event, monkeypatch)

    assert event.type.code == "MP"
    assert event.evaluation_status == "confirmed"
    assert event.autoclass["result"]["jenis"] == "VTB"
    assert event.autoclass["applied"] is False


def test_manual_veps_event_creation_enqueues_prediction(event):
    event_type = EventType.objects.get(
        organization=event.catalog.volcano.organization, code="MP"
    )
    serializer = EventPayloadSerializer(
        context={
            "request": SimpleNamespace(user=event.author),
            "catalog_id": event.catalog_id,
        }
    )

    created = serializer.create(
        {
            "station_of_first_arrival_id": None,
            "time": event.time,
            "duration": 35,
            "type_id": event_type.id,
            "note": "manual event",
            "attachment_ids": [],
            "method": "veps",
            "evaluation_mode": "manual",
            "evaluation_status": "confirmed",
            "observation": None,
            "amplitude_manual_inputs": [],
        }
    )

    assert created.autoclass["state"] == "pending"
    assert created.type.code == "MP"


def test_time_change_requeues_prediction_but_other_edits_do_not(event, monkeypatch):
    event.autoclass = {
        "state": "succeeded",
        "source": "veps",
        "input_time": event.time.isoformat(),
        "revision": "merapi-v6-test",
        "attempts": 1,
        "attempt_id": "old-attempt",
        "result": result_for(event),
        "applied": False,
        "validation": {"type": "MP", "status": "confirmed"},
    }
    event.type = EventType.objects.get(
        organization=event.catalog.volcano.organization, code="MP"
    )
    event.method = "veps"
    event.evaluation_mode = "manual"
    event.evaluation_status = "confirmed"
    event.save()
    serializer = EventPayloadSerializer(
        context={"request": SimpleNamespace(user=event.author)}
    )

    new_time = event.time + timedelta(seconds=5)
    serializer.update(event, {"time": new_time})
    event.refresh_from_db()
    assert event.autoclass["state"] == "pending"
    assert event.autoclass["input_time"] == new_time.isoformat()
    assert event.autoclass["attempts"] == 0
    assert "attempt_id" not in event.autoclass
    assert event.autoclass["result"] is None
    assert event.autoclass["validation"]["type"] == "MP"
    assert event.autoclass["validation"]["status"] == "confirmed"
    assert event.autoclass["validation"]["actor_id"] == str(event.author_id)
    assert event.type.code == "MP"

    monkeypatch.setattr(
        task, "predict", lambda e: result_for(e, jenis="RF", kelas="RF")
    )
    task.classify_event(str(event.id))
    event.refresh_from_db()
    assert event.autoclass["result"]["jenis"] == "RF"
    assert event.type.code == "MP"
    assert event.evaluation_status == "confirmed"

    task._dispatch.reset_mock()
    serializer.update(event, {"note": "updated note"})
    serializer.update(
        event,
        {
            "type_id": EventType.objects.get(
                organization=event.catalog.volcano.organization, code="LF"
            ).id
        },
    )
    assert not any(
        call.args[0] == task.classify_event for call in task._dispatch.call_args_list
    )


def test_old_time_prediction_cannot_replace_requeued_prediction(event, monkeypatch):
    task.enqueue_event(event)
    serializer = EventPayloadSerializer(
        context={"request": SimpleNamespace(user=event.author)}
    )

    def inference(running_event):
        serializer.update(
            running_event, {"time": running_event.time + timedelta(seconds=5)}
        )
        return result_for(running_event)

    monkeypatch.setattr(task, "predict", inference)
    task.classify_event(str(event.id))

    event.refresh_from_db()
    assert event.autoclass["state"] == "pending"
    assert event.autoclass["input_time"] == event.time.isoformat()
    assert event.autoclass["result"] is None
    assert event.type.code == "AUTO"


def test_reclassification_updates_automatic_type_when_time_changes(event, monkeypatch):
    run_prediction(event, monkeypatch)
    serializer = EventPayloadSerializer(
        context={"request": SimpleNamespace(user=event.author)}
    )
    serializer.update(event, {"time": event.time + timedelta(seconds=5)})
    monkeypatch.setattr(
        task, "predict", lambda e: result_for(e, jenis="MP", kelas="MP")
    )

    task.classify_event(str(event.id))

    event.refresh_from_db()
    assert event.autoclass["result"]["jenis"] == "MP"
    assert event.autoclass["applied"] is True
    assert event.type.code == "MP"


def test_inference_deduplicates_success(event, monkeypatch):
    run_prediction(event, monkeypatch)
    fail = Mock(side_effect=AssertionError("must not infer twice"))
    monkeypatch.setattr(task, "predict", fail)
    task.classify_event(str(event.id))
    event.refresh_from_db()
    assert event.autoclass["attempts"] == 1


def test_manual_edit_while_predicting_wins(event, monkeypatch):
    task.enqueue_event(event)

    def inference(e):
        Event.objects.filter(id=e.id).update(
            evaluation_mode="manual",
            evaluation_status="confirmed",
            note="operator note",
            type=EventType.objects.get(
                organization=event.catalog.volcano.organization, code="MP"
            ),
        )
        return result_for(e)

    monkeypatch.setattr(task, "predict", inference)
    task.classify_event(str(event.id))
    event.refresh_from_db()
    assert (event.type.code, event.evaluation_status, event.note) == (
        "MP",
        "confirmed",
        "operator note",
    )
    assert event.autoclass["result"]["jenis"] == "VTB"
    assert event.autoclass["applied"] is False


def test_changed_time_and_deleted_event_do_not_apply(event, monkeypatch):
    task.enqueue_event(event)

    def inference(e):
        Event.objects.filter(id=e.id).update(time=e.time + timedelta(seconds=2))
        return result_for(e)

    monkeypatch.setattr(task, "predict", inference)
    task.classify_event(str(event.id))
    event.refresh_from_db()
    assert event.type.code == "AUTO"
    assert event.autoclass["state"] == "stale"
    identity = str(event.id)
    event.delete()
    task.classify_event(identity)


def test_retry_exhausts_and_recovery_reclaims_lease(event, monkeypatch):
    task.enqueue_event(event)
    monkeypatch.setattr(
        task, "predict", Mock(side_effect=PredictionError("data_unavailable", True))
    )
    for attempt in range(4):
        task.classify_event(str(event.id))
        event.refresh_from_db()
        assert event.autoclass["attempts"] == attempt + 1
        if attempt < 3:
            assert event.autoclass["state"] == "retrying"
            event.autoclass["due_at"] = (
                timezone.now() - timedelta(seconds=1)
            ).isoformat()
            event.save(update_fields=["autoclass"])
    assert event.autoclass["state"] == "failed"


@pytest.mark.parametrize(
    "change",
    [
        {"status": "gagal"},
        {"jenis": "NOISE"},
        {"prob_jenis": True},
        {"prob_jenis": float("nan")},
        {"prob_jenis": 1.1},
        {"model": "different"},
        {"versi": "9"},
        {"waktu_utc": "2020-01-01 00:00:00"},
        {"eventid": "wrong"},
        {"top3": [{"kelas": "BAD", "p": 1}]},
        {"kelas": 42},
        {"kelas_10": {"unexpected": "object"}},
        {"saran": 42},
        {"saran": [{"unexpected": "object"}]},
        {"catatan": {"unexpected": "object"}},
        {"cek_tektonik": "unexpected"},
        {"cek_tektonik": {"saran": {"unexpected": "object"}}},
        {"arah_sumber": {"unexpected": "object"}},
        {"tanda_awan_panas": {"unexpected": "object"}},
        {"diproses_utc": {"unexpected": "object"}},
        {"cek_tektonik": {"snr": float("inf")}},
    ],
)
def test_client_rejects_wrong_prediction_contract(event, monkeypatch, change):
    response = Mock(status_code=200, json=lambda: result_for(event, **change))
    monkeypatch.setattr(
        "waveview.contrib.autoclass.client.requests.post", lambda *a, **k: response
    )
    with pytest.raises(PredictionError):
        predict(event)


def test_client_preserves_fractional_utc_and_disables_sinks(event, monkeypatch):
    def post(url, **kwargs):
        assert url == "http://autoclass:8765/predict"
        assert kwargs["json"]["waktu"] == event.time.isoformat().replace("+00:00", "Z")
        assert kwargs["json"]["simpan"] is False
        assert kwargs["json"]["tunggu"] is False
        assert kwargs["headers"]["X-Token"] == "test-token"
        assert kwargs["allow_redirects"] is False
        return Mock(
            status_code=200,
            json=lambda: result_for(event, diproses_utc="2026-10-26 03:02:35"),
        )

    monkeypatch.setattr("waveview.contrib.autoclass.client.requests.post", post)
    result = predict(event)
    assert result["jenis"] == "VTB"
    assert result["diproses_utc"] == "2026-10-26 03:02:35"


def test_recovery_reclaims_expired_work_and_late_attempt_cannot_apply(
    event, monkeypatch
):
    task.enqueue_event(event)
    event.refresh_from_db()
    event.autoclass.update(
        state="running",
        attempts=1,
        attempt_id="old",
        started_at=(timezone.now() - timedelta(seconds=601)).isoformat(),
    )
    event.save(update_fields=["autoclass"])
    monkeypatch.setattr(task, "predict", lambda e: result_for(e))
    monkeypatch.setattr(task, "_dispatch", lambda job, identity, delay=0: job(identity))
    task.recover_events()
    event.refresh_from_db()
    assert event.autoclass["state"] == "succeeded"
    assert event.autoclass["attempts"] == 2


def test_time_cleared_after_schedule_is_stale(event):
    task.enqueue_event(event)
    Event.objects.filter(pk=event.pk).update(time=None)
    task.classify_event(str(event.id))
    event.refresh_from_db()
    assert event.autoclass["state"] == "stale"


def test_crash_retries_are_bounded(event, monkeypatch):
    task.enqueue_event(event)
    event.refresh_from_db()
    event.autoclass.update(
        state="running",
        attempts=4,
        attempt_id="old",
        started_at=(timezone.now() - timedelta(seconds=601)).isoformat(),
    )
    event.save(update_fields=["autoclass"])
    monkeypatch.setattr(
        task, "predict", Mock(side_effect=AssertionError("retries exhausted"))
    )
    task.classify_event(str(event.id))
    event.refresh_from_db()
    assert event.autoclass["state"] == "failed"
    assert event.autoclass["attempts"] == 4


def test_rolled_back_detector_work_is_not_persisted(event):
    from django.db import transaction

    with pytest.raises(RuntimeError), transaction.atomic():
        task.enqueue_event(event)
        raise RuntimeError("rollback")
    event.refresh_from_db()
    assert event.autoclass is None


def test_sinoas_creates_durable_work(event):
    from waveview.contrib.sinoas.context import SinoasContext
    from waveview.contrib.sinoas.detector import DetectedEvent, Detector

    context = SinoasContext(
        organization=event.catalog.volcano.organization,
        volcano=event.catalog.volcano,
        user=event.author,
    )
    Detector(context=context).create_event(DetectedEvent(event.time, 35, 4000))
    detected = Event.objects.exclude(pk=event.pk).get()
    assert detected.autoclass["state"] == "pending"
    assert detected.autoclass["source"] == "sinoas"


def test_autopicker_creates_durable_work(event, monkeypatch):
    from waveview.contrib.autopicker.task import create_event

    monkeypatch.setattr(
        "waveview.contrib.autopicker.task.notify_event.delay", lambda *args: None
    )
    create_event(
        {
            "t_on": event.time.isoformat(),
            "t_off": (event.time + timedelta(seconds=35)).isoformat(),
            "picks": [
                {
                    "stream_id": "VG.MEPAC.00.HHZ",
                    "t_pick": event.time.isoformat(),
                    "offset": 0,
                }
            ],
        }
    )
    detected = Event.objects.exclude(pk=event.pk).get()
    assert detected.autoclass["state"] == "pending"
    assert detected.autoclass["source"] == "stelte"


@pytest.mark.django_db(transaction=True)
def test_autopicker_event_survives_notification_broker_failure(event, monkeypatch):
    from waveview.contrib.autopicker.task import create_event

    def unavailable(*args):
        raise ConnectionError("broker down")

    monkeypatch.setattr(
        "waveview.contrib.autopicker.task.notify_event.delay", unavailable
    )
    create_event(
        {
            "t_on": event.time.isoformat(),
            "t_off": (event.time + timedelta(seconds=35)).isoformat(),
            "picks": [
                {
                    "stream_id": "VG.MEPAC.00.HHZ",
                    "t_pick": event.time.isoformat(),
                    "offset": 0,
                }
            ],
        }
    )
    detected = Event.objects.exclude(pk=event.pk).get()
    assert detected.autoclass["state"] == "pending"


@pytest.mark.parametrize(
    "transition",
    [
        "disabled",
        "stale",
        "manual_change",
        "retries_exhausted",
        "stale_during_prediction",
    ],
)
def test_terminal_transition_notifies_only_after_commit(
    event, monkeypatch, settings, django_capture_on_commit_callbacks, transition
):
    task.enqueue_event(event)
    event.refresh_from_db()
    notices = []
    monkeypatch.setattr(
        task.notify_event, "delay", lambda operation, payload: notices.append(payload)
    )
    if transition == "disabled":
        settings.AUTOCLASS_CATALOG_IDS = []
    elif transition == "stale":
        Event.objects.filter(pk=event.pk).update(time=None)
    elif transition == "manual_change":
        Event.objects.filter(pk=event.pk).update(evaluation_mode="manual")
    elif transition == "retries_exhausted":
        event.autoclass.update(
            state="running",
            attempts=4,
            started_at=(timezone.now() - timedelta(seconds=601)).isoformat(),
        )
        event.save(update_fields=["autoclass"])
    else:

        def prediction(e):
            Event.objects.filter(pk=e.pk).update(time=None)
            return result_for(e)

        monkeypatch.setattr(task, "predict", prediction)
    with django_capture_on_commit_callbacks(execute=True):
        task.classify_event(str(event.pk))
        assert notices == []
    event.refresh_from_db()
    assert event.autoclass["state"] in ("failed", "skipped", "stale")
    assert notices
    assert notices[-1]["event_id"] == str(event.pk)


def test_future_time_is_held_without_dispatch(event, monkeypatch):
    event.time = timezone.now() + timedelta(hours=1)
    event.save(update_fields=["time"])
    dispatched = Mock()
    monkeypatch.setattr(task, "_dispatch", dispatched)
    task.enqueue_event(event)
    event.refresh_from_db()
    assert event.autoclass["state"] == "failed"
    assert event.autoclass["error"] == "invalid_time"
    assert event.autoclass["attempts"] == 0
    dispatched.assert_not_called()


def test_missing_mapping_preserves_auto_and_original_result(event, monkeypatch):
    EventType.objects.filter(
        organization=event.catalog.volcano.organization, code="VTB"
    ).delete()
    run_prediction(event, monkeypatch)
    assert event.type.code == "AUTO"
    assert event.autoclass["error"] == "mapping_missing"
    assert event.autoclass["result"]["jenis"] == "VTB"
    assert event.autoclass["applied"] is False


def test_disabling_pilot_during_inference_keeps_auto(event, monkeypatch, settings):
    task.enqueue_event(event)

    def prediction(e):
        settings.AUTOCLASS_CATALOG_IDS = []
        return result_for(e)

    monkeypatch.setattr(task, "predict", prediction)
    task.classify_event(str(event.pk))
    event.refresh_from_db()
    assert event.type.code == "AUTO"
    assert event.autoclass["state"] == "skipped"
    assert event.autoclass["error"] == "disabled"


def test_expired_attempt_response_cannot_replace_newer_prediction(event, monkeypatch):
    task.enqueue_event(event)
    calls = []

    def prediction(e):
        calls.append(e.autoclass["attempt_id"])
        if len(calls) == 1:
            current = Event.objects.get(pk=e.pk)
            current.autoclass["started_at"] = (
                timezone.now() - timedelta(seconds=601)
            ).isoformat()
            current.save(update_fields=["autoclass"])
            task.classify_event(str(e.pk))
            return result_for(e, jenis="VTB")
        return result_for(e, jenis="MP")

    monkeypatch.setattr(task, "predict", prediction)
    task.classify_event(str(event.pk))
    event.refresh_from_db()
    assert len(set(calls)) == 2
    assert event.type.code == "MP"
    assert event.autoclass["result"]["jenis"] == "MP"
    assert event.autoclass["attempts"] == 2


def test_failed_task_publish_is_durable_and_recovered(
    event, monkeypatch, django_capture_on_commit_callbacks
):
    monkeypatch.setattr(task, "_dispatch", _dispatch)
    monkeypatch.setattr(
        task.classify_event,
        "apply_async",
        Mock(side_effect=ConnectionError("broker down")),
    )
    with django_capture_on_commit_callbacks(execute=True):
        task.enqueue_event(event)
    event.refresh_from_db()
    assert event.autoclass["state"] == "pending"
    assert event.autoclass["attempts"] == 0
    published = []
    monkeypatch.setattr(
        task.classify_event,
        "apply_async",
        lambda **kwargs: published.append(kwargs["args"]),
    )
    task.recover_events()
    assert published == [[str(event.pk)]]
