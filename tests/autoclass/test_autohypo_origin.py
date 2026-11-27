import math
from datetime import timedelta

import pytest
from django.utils import timezone

from waveview.contrib.bma.bulletin.autohypo import apply_autohypo
from waveview.event.models import Catalog, Event, Origin
from waveview.volcano.models import Volcano

pytestmark = pytest.mark.django_db

DEFAULT_AUTOHYPO = object()


def verify(event: Event, status="confirmed"):
    event.evaluation_mode = "manual"
    event.evaluation_status = status
    event.save(update_fields=["evaluation_mode", "evaluation_status"])
    return event


def row(event, eventtype="VTA", eventid=None, autohypo=DEFAULT_AUTOHYPO):
    payload = (
        {"lat": -7.5, "lon": 110.4, "z": -1.25}
        if autohypo is DEFAULT_AUTOHYPO
        else autohypo
    )
    return {
        "eventid": event.id.hex if eventid is None else eventid,
        "eventtype": eventtype,
        "autohypo": payload,
    }


def test_verified_event_without_origin_becomes_preferred_nlloc(event):
    verify(event)
    result = apply_autohypo(event.catalog, row(event))
    origin = Origin.objects.get(event=event, method="nlloc")
    assert result.status == "written"
    assert result.preferred is True
    assert origin.latitude == -7.5
    assert origin.longitude == 110.4
    assert origin.depth == -1.25
    assert origin.time == event.time
    assert origin.evaluation_mode == "automatic"
    assert origin.evaluation_status == "preliminary"
    assert origin.is_preferred is True
    assert origin.author_id is None
    assert origin.earth_model in (None, "")


@pytest.mark.parametrize("status", ["confirmed", "reviewed", "final"])
def test_verified_statuses_are_written(event, status):
    verify(event, status)
    assert apply_autohypo(event.catalog, row(event, eventtype="vtb")).status == "written"


def test_existing_preferred_origin_stays_preferred(event):
    verify(event)
    operator = Origin.objects.create(
        event=event,
        time=event.time,
        latitude=1,
        longitude=2,
        depth=3,
        method="operator",
        is_preferred=True,
    )
    result = apply_autohypo(event.catalog, row(event))
    nlloc = Origin.objects.get(event=event, method="nlloc")
    operator.refresh_from_db()
    assert result.preferred is False
    assert nlloc.is_preferred is False
    assert operator.is_preferred is True


def test_second_run_updates_the_same_origin(event):
    verify(event)
    apply_autohypo(event.catalog, row(event))
    apply_autohypo(event.catalog, row(event, autohypo={"lat": -7.6, "lon": 110.5, "z": -2}))
    origin = Origin.objects.get(event=event, method="nlloc")
    assert Origin.objects.filter(event=event, method="nlloc").count() == 1
    assert origin.depth == -2
    assert origin.is_preferred is True


def test_update_keeps_author_and_earth_model(event):
    verify(event)
    apply_autohypo(event.catalog, row(event))
    origin = Origin.objects.get(event=event, method="nlloc")
    origin.author = event.author
    origin.earth_model = "merapi"
    origin.save(update_fields=["author", "earth_model"])
    apply_autohypo(event.catalog, row(event, autohypo={"lat": -7.6, "lon": 110.5, "z": 4}))
    origin.refresh_from_db()
    assert origin.author_id == event.author_id
    assert origin.earth_model == "merapi"
    assert origin.depth == 4
    assert origin.evaluation_mode == "automatic"


def test_preferred_nlloc_among_duplicates_is_updated(event):
    verify(event)
    older = Origin.objects.create(
        event=event, time=event.time, latitude=0, longitude=0, depth=0, method="nlloc"
    )
    newer = Origin.objects.create(
        event=event,
        time=event.time,
        latitude=9,
        longitude=9,
        depth=9,
        method="nlloc",
        is_preferred=True,
    )
    Origin.objects.filter(pk=older.pk).update(created_at=timezone.now() - timedelta(minutes=2))
    Origin.objects.filter(pk=newer.pk).update(created_at=timezone.now() - timedelta(minutes=1))
    apply_autohypo(event.catalog, row(event, autohypo={"lat": -7.6, "lon": 110.5, "z": 4}))
    older.refresh_from_db()
    newer.refresh_from_db()
    assert Origin.objects.filter(event=event, method="nlloc").count() == 2
    assert newer.latitude == -7.6
    assert older.latitude == 0
    assert newer.is_preferred is True


def test_oldest_nlloc_is_updated_when_none_is_preferred(event):
    verify(event)
    older = Origin.objects.create(
        event=event, time=event.time, latitude=0, longitude=0, depth=0, method="nlloc"
    )
    newer = Origin.objects.create(
        event=event, time=event.time, latitude=9, longitude=9, depth=9, method="nlloc"
    )
    Origin.objects.filter(pk=older.pk).update(created_at=timezone.now() - timedelta(minutes=2))
    Origin.objects.filter(pk=newer.pk).update(created_at=timezone.now() - timedelta(minutes=1))
    apply_autohypo(event.catalog, row(event, autohypo={"lat": -7.6, "lon": 110.5, "z": 4}))
    older.refresh_from_db()
    newer.refresh_from_db()
    assert older.latitude == -7.6
    assert newer.latitude == 9
    assert older.is_preferred is True


def test_existing_preferred_nlloc_is_not_cleared_when_another_origin_is_preferred(event):
    verify(event)
    apply_autohypo(event.catalog, row(event))
    operator = Origin.objects.create(
        event=event,
        time=event.time,
        latitude=1,
        longitude=2,
        depth=3,
        method="operator",
        is_preferred=True,
    )
    apply_autohypo(event.catalog, row(event, autohypo={"lat": -7.6, "lon": 110.5, "z": 4}))
    nlloc = Origin.objects.get(event=event, method="nlloc")
    operator.refresh_from_db()
    assert nlloc.is_preferred is True
    assert nlloc.depth == 4
    assert operator.is_preferred is True


@pytest.mark.parametrize(
    "changes",
    [
        {"evaluation_mode": "automatic", "evaluation_status": "preliminary"},
        {"evaluation_mode": "manual", "evaluation_status": "rejected"},
        {"evaluation_mode": "manual", "evaluation_status": "preliminary"},
    ],
)
def test_unverified_events_are_skipped(event, changes):
    event.evaluation_mode = changes["evaluation_mode"]
    event.evaluation_status = changes["evaluation_status"]
    event.save(update_fields=["evaluation_mode", "evaluation_status"])
    result = apply_autohypo(event.catalog, row(event))
    assert result.status == "skipped"
    assert result.reason == "status"
    assert Origin.objects.filter(method="nlloc").count() == 0


def test_non_uuid_and_unknown_event_are_skipped(event):
    verify(event)
    event.refid = "webobs-1"
    event.save(update_fields=["refid"])
    assert apply_autohypo(event.catalog, row(event, eventid="webobs-1")).reason == "eventid"
    missing = row(event, eventid="11111111-1111-1111-1111-111111111111")
    assert apply_autohypo(event.catalog, missing).reason == "event"
    other = Volcano.objects.create(
        slug="other", name="Other", organization=event.catalog.volcano.organization
    )
    other_catalog = Catalog.objects.get(volcano=other, is_default=True)
    assert apply_autohypo(other_catalog, row(event)).reason == "event"
    assert Origin.objects.filter(method="nlloc").count() == 0


def test_non_vta_vtb_and_incomplete_autohypo_are_skipped(event):
    verify(event)
    assert apply_autohypo(event.catalog, row(event, eventtype="ROCKFALL")).reason == "type"
    assert apply_autohypo(event.catalog, row(event, autohypo={})).reason == "autohypo"
    assert apply_autohypo(event.catalog, row(event, autohypo=None)).reason == "autohypo"
    partial = {"lat": -7.5, "lon": 110.4}
    assert apply_autohypo(event.catalog, row(event, autohypo=partial)).reason == "autohypo"
    text = {"lat": "-7.5", "lon": 110.4, "z": -1.25}
    assert apply_autohypo(event.catalog, row(event, autohypo=text)).reason == "autohypo"
    nan = {"lat": -7.5, "lon": 110.4, "z": math.nan}
    assert apply_autohypo(event.catalog, row(event, autohypo=nan)).reason == "autohypo"
    assert Origin.objects.filter(method="nlloc").count() == 0


def test_dry_run_writes_nothing(event):
    verify(event)
    result = apply_autohypo(event.catalog, row(event), dry_run=True)
    assert result.status == "dry_run"
    assert result.preferred is True
    assert result.depth == -1.25
    assert Origin.objects.filter(method="nlloc").count() == 0


def test_apply_does_not_notify_observers(event, monkeypatch):
    verify(event)
    called = []
    monkeypatch.setattr(
        "waveview.tasks.notify_event_observer.notify_event_observer.delay",
        lambda *args, **kwargs: called.append(args),
    )
    apply_autohypo(event.catalog, row(event))
    assert called == []
