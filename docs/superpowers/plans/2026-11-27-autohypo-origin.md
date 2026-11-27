# Autohypo Origin Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Copy BMA `bulletin.autohypo` onto one `nlloc` origin for each matching verified VEPS event.

**Architecture:** `apply_autohypo` decides one bulletin row and writes the origin. `sync_autohypo` fetches the public bulletin list and applies every row. `sync_autohypo_origins` resolves the organization, volcano, default catalog, and time window, then calls `sync_autohypo`.

**Tech Stack:** Django, pytest, `requests` through the existing `BulletinImporter`.

**Spec:** `docs/superpowers/specs/2026-11-27-autohypo-origin-design.md`

## Global Constraints

- Match `eventid` as a UUID primary key in the volcano's default catalog. Do not look up `refid`. A 32-character hex id is valid.
- Write only when `evaluation_mode` is `manual` and `evaluation_status` is `confirmed`, `reviewed`, or `final`.
- Accept only bulletin `eventtype` `VTA` or `VTB`, compared case-insensitively.
- Copy finite numeric `lat`, `lon`, and `z` unchanged into `latitude`, `longitude`, and `depth`.
- Keep one `nlloc` write per event: update the preferred `nlloc` origin when one of several is preferred, otherwise the oldest. Do not insert another, and do not delete extras.
- Set `is_preferred` when no other origin is preferred. Do not clear `is_preferred` on the `nlloc` row or on any other origin.
- On create, leave `author` and `earth_model` empty. On update, leave both as they are. Set `time` to the event time, `evaluation_mode` to `automatic`, and `evaluation_status` to `preliminary` on every write.
- Do not create events, call `notify_event_observer`, change autohypo, or change bulletin upsert.
- `--dry-run` writes nothing.
- A skipped row does not stop the batch. A missing organization, volcano, or default catalog writes to stderr and returns, as `sync_bma_events` does. An HTTP or network failure propagates and writes no origins.
- No database migration.

## Files and responsibilities

- `waveview/contrib/bma/bulletin/autohypo.py`: unwrap the bulletin body, apply one row, and sync a time range.
- `waveview/event/management/commands/sync_autohypo_origins.py`: parse arguments and call `sync_autohypo`.
- `tests/autoclass/test_autohypo_origin.py`: row rules, fetch behavior, and the command. The `event` fixture in `tests/autoclass/conftest.py` supplies the Merapi default catalog.

---

### Task 1: Apply one autohypo row

**Files:**
- Create: `waveview/contrib/bma/bulletin/autohypo.py`
- Test: `tests/autoclass/test_autohypo_origin.py`

**Interfaces:**
- Consumes: `Catalog`, `Event`, and `Origin`.
- Produces: `ApplyResult` and `apply_autohypo(catalog: Catalog, row: dict, dry_run: bool = False) -> ApplyResult`.

- [ ] **Step 1: Write the failing tests**

Create `tests/autoclass/test_autohypo_origin.py`:

```python
import math
from datetime import timedelta

import pytest
from django.utils import timezone

from waveview.contrib.bma.bulletin.autohypo import apply_autohypo
from waveview.event.models import Catalog, Event, Origin
from waveview.volcano.models import Volcano

pytestmark = pytest.mark.django_db


def verify(event, status="confirmed"):
    event.evaluation_mode = "manual"
    event.evaluation_status = status
    event.save(update_fields=["evaluation_mode", "evaluation_status"])
    return event


def row(event, eventtype="VTA", eventid=None, autohypo=None):
    payload = {"lat": -7.5, "lon": 110.4, "z": -1.25}
    if autohypo is not None:
        payload = autohypo
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
```

- [ ] **Step 2: Run the tests and confirm they fail**

Run:

```bash
SECRET_KEY=test DATABASE_NAME=waveview_test DATABASE_USER=postgres DATABASE_PASSWORD=test DATABASE_HOST=127.0.0.1 DATABASE_PORT=16440 poetry run pytest -q tests/autoclass/test_autohypo_origin.py
```

Expected: FAIL because `waveview.contrib.bma.bulletin.autohypo` does not exist.

- [ ] **Step 3: Write the implementation**

Create `waveview/contrib/bma/bulletin/autohypo.py`:

```python
import math
from dataclasses import dataclass
from uuid import UUID

from django.db import transaction

from waveview.event.header import EvaluationMode, EvaluationStatus
from waveview.event.models import Catalog, Event, Origin

VERIFIED = {
    EvaluationStatus.CONFIRMED,
    EvaluationStatus.REVIEWED,
    EvaluationStatus.FINAL,
}
EVENT_TYPES = {"VTA", "VTB"}


@dataclass(frozen=True)
class ApplyResult:
    status: str
    reason: str
    event_id: str | None = None
    preferred: bool | None = None
    latitude: float | None = None
    longitude: float | None = None
    depth: float | None = None


def _finite(value: object) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    number = float(value)
    if not math.isfinite(number):
        return None
    return number


def _event_id(value: object) -> UUID | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        return UUID(value)
    except ValueError:
        return None


def _select_nlloc(event: Event) -> Origin | None:
    rows = list(event.origins.filter(method="nlloc").order_by("created_at", "id"))
    for origin in rows:
        if origin.is_preferred:
            return origin
    return rows[0] if rows else None


def _preferred(event: Event, origin: Origin | None) -> bool:
    others = event.origins.filter(is_preferred=True)
    if origin is not None:
        others = others.exclude(pk=origin.pk)
    if others.exists():
        return bool(origin and origin.is_preferred)
    return True


def apply_autohypo(catalog: Catalog, row: dict, dry_run: bool = False) -> ApplyResult:
    eventtype = str(row.get("eventtype") or "").upper()
    if eventtype not in EVENT_TYPES:
        return ApplyResult("skipped", "type")
    autohypo = row.get("autohypo")
    if not isinstance(autohypo, dict):
        return ApplyResult("skipped", "autohypo")
    latitude = _finite(autohypo.get("lat"))
    longitude = _finite(autohypo.get("lon"))
    depth = _finite(autohypo.get("z"))
    if latitude is None or longitude is None or depth is None:
        return ApplyResult("skipped", "autohypo")
    raw_id = row.get("eventid")
    event_id = _event_id(raw_id)
    if event_id is None:
        return ApplyResult("skipped", "eventid", event_id=None if raw_id is None else str(raw_id))
    event = Event.objects.filter(catalog=catalog, pk=event_id).first()
    if event is None:
        return ApplyResult("skipped", "event", event_id=str(event_id))
    if event.evaluation_mode != EvaluationMode.MANUAL or event.evaluation_status not in VERIFIED:
        return ApplyResult("skipped", "status", event_id=str(event.pk))
    origin = _select_nlloc(event)
    preferred = _preferred(event, origin)
    result = ApplyResult(
        "dry_run" if dry_run else "written",
        "",
        event_id=str(event.pk),
        preferred=preferred,
        latitude=latitude,
        longitude=longitude,
        depth=depth,
    )
    if dry_run:
        return result
    with transaction.atomic():
        event = Event.objects.select_for_update().get(pk=event.pk, catalog=catalog)
        origin = _select_nlloc(event)
        preferred = _preferred(event, origin)
        if origin is None:
            Origin.objects.create(
                event=event,
                time=event.time,
                latitude=latitude,
                longitude=longitude,
                depth=depth,
                method="nlloc",
                evaluation_mode=EvaluationMode.AUTOMATIC,
                evaluation_status=EvaluationStatus.PRELIMINARY,
                is_preferred=preferred,
            )
        else:
            origin.time = event.time
            origin.latitude = latitude
            origin.longitude = longitude
            origin.depth = depth
            origin.evaluation_mode = EvaluationMode.AUTOMATIC
            origin.evaluation_status = EvaluationStatus.PRELIMINARY
            if preferred and not origin.is_preferred:
                origin.is_preferred = True
            origin.save()
    return ApplyResult(
        "written",
        "",
        event_id=str(event.pk),
        preferred=preferred,
        latitude=latitude,
        longitude=longitude,
        depth=depth,
    )
```

- [ ] **Step 4: Run the tests and confirm they pass**

Run the same pytest command as Step 2.

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add waveview/contrib/bma/bulletin/autohypo.py tests/autoclass/test_autohypo_origin.py
git commit -m "$(cat <<'EOF'
Add autohypo origin writes for verified events.

EOF
)"
```

---

### Task 2: Fetch bulletin rows and add the command

**Files:**
- Modify: `waveview/contrib/bma/bulletin/autohypo.py`
- Create: `waveview/event/management/commands/sync_autohypo_origins.py`
- Test: `tests/autoclass/test_autohypo_origin.py`

**Interfaces:**
- Consumes: `apply_autohypo` and `ApplyResult` from Task 1. `BulletinImporter.fetch(start, end)` already sends `nolimit=true`.
- Produces: `bulletin_rows(payload: object) -> list[dict]` and `sync_autohypo(catalog: Catalog, start: datetime, end: datetime, dry_run: bool = False, importer: BulletinImporter | None = None) -> list[ApplyResult]`. The command name is `sync_autohypo_origins`.

- [ ] **Step 1: Add the failing fetch and command tests**

Append to `tests/autoclass/test_autohypo_origin.py`:

```python
from unittest.mock import Mock

import requests
from django.core.management import call_command

from waveview.contrib.bma.bulletin.autohypo import sync_autohypo


def test_sync_unwraps_data_and_continues_after_a_skipped_row(event):
    verify(event)
    importer = Mock()
    importer.fetch.return_value = {
        "data": [
            row(event, eventtype="ROCKFALL"),
            row(event),
        ]
    }
    results = sync_autohypo(
        event.catalog,
        timezone.now() - timedelta(hours=1),
        timezone.now(),
        importer=importer,
    )
    assert [item.status for item in results] == ["skipped", "written"]
    assert Origin.objects.filter(event=event, method="nlloc").count() == 1


def test_sync_empty_list_writes_nothing(event):
    verify(event)
    importer = Mock()
    importer.fetch.return_value = []
    assert (
        sync_autohypo(
            event.catalog,
            timezone.now() - timedelta(hours=1),
            timezone.now(),
            importer=importer,
        )
        == []
    )
    assert Origin.objects.filter(method="nlloc").count() == 0


def test_sync_http_error_writes_nothing(event):
    verify(event)
    importer = Mock()
    importer.fetch.side_effect = requests.HTTPError("bulletin down")
    with pytest.raises(requests.HTTPError):
        sync_autohypo(
            event.catalog,
            timezone.now() - timedelta(hours=1),
            timezone.now(),
            importer=importer,
        )
    assert Origin.objects.filter(method="nlloc").count() == 0


def test_command_requires_org(capsys):
    call_command("sync_autohypo_origins")
    assert "Organization slug is required." in capsys.readouterr().err


def test_command_unknown_org(capsys):
    call_command("sync_autohypo_origins", org="missing", volcano="merapi")
    assert "does not exist" in capsys.readouterr().err


def test_command_missing_volcano(event, capsys):
    call_command("sync_autohypo_origins", org="test", volcano="missing")
    assert "does not exist" in capsys.readouterr().err


def test_command_missing_catalog(event, capsys):
    Catalog.objects.filter(pk=event.catalog_id).delete()
    call_command("sync_autohypo_origins", org="test", volcano="merapi")
    assert "does not exist" in capsys.readouterr().err


def test_command_hours_override_and_dry_run(event, monkeypatch):
    seen = {}

    def fake_sync(catalog, start, end, dry_run=False, importer=None):
        seen["catalog"] = catalog.pk
        seen["start"] = start
        seen["end"] = end
        seen["dry_run"] = dry_run
        return []

    monkeypatch.setattr(
        "waveview.event.management.commands.sync_autohypo_origins.sync_autohypo",
        fake_sync,
    )
    call_command(
        "sync_autohypo_origins",
        org="test",
        volcano="merapi",
        hours=6,
        dry_run=True,
    )
    assert seen["catalog"] == event.catalog_id
    assert seen["dry_run"] is True
    assert seen["end"] - seen["start"] == timedelta(hours=6)


def test_command_defaults_to_one_day(event, monkeypatch):
    seen = {}

    def fake_sync(catalog, start, end, dry_run=False, importer=None):
        seen["start"] = start
        seen["end"] = end
        return []

    monkeypatch.setattr(
        "waveview.event.management.commands.sync_autohypo_origins.sync_autohypo",
        fake_sync,
    )
    call_command("sync_autohypo_origins", org="test", volcano="merapi")
    assert seen["end"] - seen["start"] == timedelta(days=1)
```

`timedelta`, `timezone`, `pytest`, `Origin`, and `Catalog` are already imported by the Task 1 tests. Do not import them again.

- [ ] **Step 2: Run the new tests and confirm they fail**

Run:

```bash
SECRET_KEY=test DATABASE_NAME=waveview_test DATABASE_USER=postgres DATABASE_PASSWORD=test DATABASE_HOST=127.0.0.1 DATABASE_PORT=16440 poetry run pytest -q tests/autoclass/test_autohypo_origin.py -k "sync or command"
```

Expected: FAIL because `sync_autohypo` and the command do not exist.

- [ ] **Step 3: Add fetch syncing**

Append to `waveview/contrib/bma/bulletin/autohypo.py`:

```python
import logging
from datetime import datetime

from django.conf import settings

from waveview.contrib.bma.bulletin.loader import BulletinImporter

logger = logging.getLogger(__name__)


def bulletin_rows(payload: object) -> list[dict]:
    if isinstance(payload, dict):
        data = payload.get("data")
        if isinstance(data, list):
            return [item for item in data if isinstance(item, dict)]
        return []
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    return []


def sync_autohypo(
    catalog: Catalog,
    start: datetime,
    end: datetime,
    dry_run: bool = False,
    importer: BulletinImporter | None = None,
) -> list[ApplyResult]:
    if importer is None:
        importer = BulletinImporter(settings.BMA_URL, settings.BMA_API_KEY)
    payload = importer.fetch(start, end)
    results = []
    for item in bulletin_rows(payload):
        result = apply_autohypo(catalog, item, dry_run=dry_run)
        logger.info(
            "autohypo %s event=%s reason=%s preferred=%s lat=%s lon=%s depth=%s",
            result.status,
            result.event_id,
            result.reason,
            result.preferred,
            result.latitude,
            result.longitude,
            result.depth,
        )
        results.append(result)
    return results
```

Place `import logging` and `from datetime import datetime` with the other imports. Do not catch `requests` errors inside `sync_autohypo`.

- [ ] **Step 4: Add the command**

Create `waveview/event/management/commands/sync_autohypo_origins.py`:

```python
import logging
from typing import Any

from dateutil.parser import parse
from django.core.management.base import BaseCommand, CommandParser
from django.utils import timezone

from waveview.contrib.bma.bulletin.autohypo import sync_autohypo
from waveview.event.models import Catalog
from waveview.organization.models import Organization
from waveview.volcano.models import Volcano

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Copy BMA autohypo locations onto verified VEPS events."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("--org", type=str, help="Organization slug.")
        parser.add_argument("--volcano", type=str, help="Volcano slug.")
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Print matches without writing origins.",
        )
        parser.add_argument("--start", type=str, help="Window start.")
        parser.add_argument("--end", type=str, help="Window end.")
        parser.add_argument(
            "--hours",
            type=int,
            help="Hours before the end time. Overrides --start.",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        org_slug = options["org"]
        if not org_slug:
            self.stderr.write("Organization slug is required.")
            return
        volcano_slug = options["volcano"]
        if not volcano_slug:
            self.stderr.write("Volcano slug is required.")
            return

        end = options["end"]
        if end is None:
            end = timezone.now()
        else:
            end = parse(end)
            if not timezone.is_aware(end):
                end = timezone.make_aware(end)

        start = options["start"]
        if start is None:
            start = end - timezone.timedelta(days=1)
        else:
            start = parse(start)
            if not timezone.is_aware(start):
                start = timezone.make_aware(start)

        hours = options["hours"]
        if hours:
            start = end - timezone.timedelta(hours=hours)

        try:
            organization = Organization.objects.get(slug=org_slug)
        except Organization.DoesNotExist:
            self.stderr.write(f"Organization with slug '{org_slug}' does not exist.")
            return
        try:
            volcano = Volcano.objects.get(organization=organization, slug=volcano_slug)
        except Volcano.DoesNotExist:
            self.stderr.write(f"Volcano with slug '{volcano_slug}' does not exist.")
            return
        try:
            catalog = Catalog.objects.get(volcano=volcano, is_default=True)
        except Catalog.DoesNotExist:
            self.stderr.write(
                f"Default catalog for volcano '{volcano.name}' does not exist."
            )
            return

        logger.info(
            "Copying autohypo origins for %s (%s) from %s to %s",
            organization,
            volcano,
            start,
            end,
        )
        sync_autohypo(catalog, start, end, dry_run=options["dry_run"])
        logger.info("Done.")
```

- [ ] **Step 5: Run the autohypo tests**

Run:

```bash
SECRET_KEY=test DATABASE_NAME=waveview_test DATABASE_USER=postgres DATABASE_PASSWORD=test DATABASE_HOST=127.0.0.1 DATABASE_PORT=16440 poetry run pytest -q tests/autoclass/test_autohypo_origin.py
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add waveview/contrib/bma/bulletin/autohypo.py waveview/event/management/commands/sync_autohypo_origins.py tests/autoclass/test_autohypo_origin.py
git commit -m "$(cat <<'EOF'
Add the command that copies autohypo locations into VEPS.

EOF
)"
```
