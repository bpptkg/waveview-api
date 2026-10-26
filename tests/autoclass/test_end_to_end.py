"""Real local HTTP transports and PostgreSQL; no production model or endpoints."""

import json
import os
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from types import SimpleNamespace

import pytest

from waveview.appconfig.models import EventObserverConfig
from waveview.contrib.autoclass import task
from waveview.contrib.sinoas.context import SinoasContext
from waveview.contrib.sinoas.detector import DetectedEvent, Detector
from waveview.event.models import Event, EventType
from waveview.event.serializers.event import EventPayloadSerializer
from .conftest import result_for

pytestmark = [
    pytest.mark.django_db,
    pytest.mark.skipif(
        not os.getenv("AUTOCLASS_CHECKOUT"),
        reason="Set AUTOCLASS_CHECKOUT to the integration autoclass checkout for real HTTP transport testing",
    ),
]


def test_detector_to_api_to_manual_validation_to_bma(event, monkeypatch, settings):
    root = Path(os.environ["AUTOCLASS_CHECKOUT"])
    monkeypatch.syspath_prepend(
        str(root / "vendor" / "autoclass-0.3.0-py3-none-any.whl")
    )
    monkeypatch.syspath_prepend(str(root))
    from worker.api import make_server

    context = SinoasContext(
        organization=event.catalog.volcano.organization,
        volcano=event.catalog.volcano,
        user=event.author,
    )
    Detector(context=context).create_event(DetectedEvent(event.time, 35, 4000))
    detected = Event.objects.exclude(pk=event.pk).get()

    class Predictor:
        clf = SimpleNamespace(name="model_merapi_v6_m1353")

        def predict_waktu(self, when, **options):
            assert when == detected.time.isoformat().replace("+00:00", "Z")
            assert options["simpan"] is False and options["tunggu"] is False
            return result_for(detected)

    api = make_server(Predictor(), "test-token", "127.0.0.1", 0)
    api_thread = threading.Thread(target=api.serve_forever, daemon=True)
    api_thread.start()
    settings.AUTOCLASS_URL = f"http://127.0.0.1:{api.server_port}"
    writes = []

    class Bma(BaseHTTPRequestHandler):
        def do_POST(self):
            writes.append(
                (
                    self.path,
                    json.loads(self.rfile.read(int(self.headers["Content-Length"]))),
                )
            )
            self.send_response(200)
            self.end_headers()

        do_PATCH = do_POST

        def log_message(self, *args):
            pass

    bma = ThreadingHTTPServer(("127.0.0.1", 0), Bma)
    bma_thread = threading.Thread(target=bma.serve_forever, daemon=True)
    bma_thread.start()
    settings.BMA_URL = f"http://127.0.0.1:{bma.server_port}"
    settings.BMA_API_KEY = "test-only"
    EventObserverConfig.objects.create(
        volcano=event.catalog.volcano,
        name="bma.bulletin",
        data={"server_url": settings.BMA_URL, "token": "test-only"},
    )
    try:
        task.classify_event(str(detected.pk))
        detected.refresh_from_db()
        assert detected.type.code == "VTB"
        assert detected.evaluation_status == "preliminary"
        task.sync_event(str(detected.pk))
        assert writes == []
        kind = EventType.objects.get(
            organization=event.catalog.volcano.organization, code="MP"
        )
        serializer = EventPayloadSerializer(
            detected,
            data={
                "type_id": str(kind.pk),
                "evaluation_mode": "manual",
                "evaluation_status": "confirmed",
                "method": "veps",
            },
            partial=True,
            context={"request": SimpleNamespace(user=event.author)},
        )
        assert serializer.is_valid(), serializer.errors
        serializer.save()
        task.sync_event(str(detected.pk))
        detected.refresh_from_db()
        assert detected.autoclass["sync"]["state"] == "synced"
        assert detected.autoclass["result"]["jenis"] == "VTB"
        assert writes[0][1]["eventid"] == detected.id.hex
        assert writes[0][1]["eventtype"] == "MP"
        assert writes[1][1]["autoclass"]["jenis"] == "VTB"
    finally:
        for server, thread in ((api, api_thread), (bma, bma_thread)):
            server.shutdown()
            server.server_close()
            thread.join()
