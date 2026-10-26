from types import SimpleNamespace

import pytest

from waveview.event.models import Event, EventType
from waveview.event.serializers.event import EventPayloadSerializer
from .test_pipeline import run_prediction

pytestmark = pytest.mark.django_db


def test_seismic_validation_keeps_current_prediction_and_needs_no_visual(
    event, monkeypatch
):
    run_prediction(event, monkeypatch)
    # Simulate an editor instance fetched before a later result was saved.
    stale = Event.objects.get(pk=event.pk)
    newer = dict(event.autoclass, attempts=3)
    Event.objects.filter(pk=event.pk).update(autoclass=newer)
    kind = EventType.objects.get(
        organization=event.catalog.volcano.organization, code="AWANPANAS"
    )
    kind.observation_type = "pyroclastic_flow"
    kind.save()
    serializer = EventPayloadSerializer(
        stale,
        data={
            "type_id": str(kind.id),
            "evaluation_mode": "manual",
            "evaluation_status": "confirmed",
            "method": "veps",
            "note": "operator checked",
            "observation": None,
            "autoclass": {"state": "fake"},
        },
        partial=True,
        context={"request": SimpleNamespace(user=event.author)},
    )
    assert serializer.is_valid(), serializer.errors
    saved = serializer.save()
    assert saved.type_id == kind.id
    assert saved.autoclass["attempts"] == 3
    assert saved.autoclass["result"]["jenis"] == "VTB"
    assert saved.autoclass["sync"]["state"] == "pending"
    assert not hasattr(saved, "pyroclastic_flow")


def test_existing_visual_is_preserved_on_seismic_save(event, monkeypatch):
    from waveview.observation.models import Rockfall

    run_prediction(event, monkeypatch, jenis="RF")
    event.type.observation_type = "rockfall"
    event.type.save()
    visual = Rockfall.objects.create(event=event, note="actual observation")
    serializer = EventPayloadSerializer(
        event,
        data={"note": "seismic note", "observation": None},
        partial=True,
        context={"request": SimpleNamespace(user=event.author)},
    )
    assert serializer.is_valid(), serializer.errors
    serializer.save()
    visual.refresh_from_db()
    assert visual.note == "actual observation"


def test_manual_type_and_prediction_are_separate(event, monkeypatch):
    run_prediction(event, monkeypatch)
    kind = EventType.objects.get(
        organization=event.catalog.volcano.organization, code="MP"
    )
    serializer = EventPayloadSerializer(
        event,
        data={
            "type_id": str(kind.id),
            "evaluation_mode": "manual",
            "evaluation_status": "confirmed",
        },
        partial=True,
        context={"request": SimpleNamespace(user=event.author)},
    )
    assert serializer.is_valid(), serializer.errors
    result = serializer.save()
    assert result.type_id == kind.id
    assert result.autoclass["result"]["jenis"] == "VTB"


def test_response_has_no_placeholder_visual_for_seismic_only_event(event, monkeypatch):
    from waveview.event.serializers.event import EventDetailSerializer

    run_prediction(event, monkeypatch, jenis="APG")
    event.type.observation_type = "pyroclastic_flow"
    event.type.save()
    assert EventDetailSerializer(event).data["observation"] is None
