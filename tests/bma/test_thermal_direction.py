import unittest
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import patch

import requests

from waveview.contrib.bma.thermal_direction.bulletin import (
    BulletinDirectionClient,
    BulletinUpdateError,
    apply_direction_fields,
    closest_bulletin_id,
)
from waveview.contrib.bma.thermal_direction.classifier import (
    ARAH_KANAN,
    ARAH_KIRI,
    TIDAK_TERDETEKSI,
    ThermalSample,
    classify,
)
from waveview.contrib.bma.thermal_direction.client import ThermalAxisClient
from waveview.contrib.bma.thermal_direction.events import is_rf_or_apg
from waveview.contrib.bma.thermal_direction.note import (
    render_thermal_note,
    upsert_event_note,
)

EVENT = datetime(2026, 9, 23, 2, 0, tzinfo=timezone.utc)


def sample(river: str, minutes: float, temperature: float) -> ThermalSample:
    return ThermalSample(
        river=river,
        time=EVENT + timedelta(minutes=minutes),
        temperature=temperature,
    )


class FakeResponse:
    def __init__(self, payload, status=200, text=""):
        self._payload = payload
        self.status_code = status
        self.ok = 200 <= status < 300
        self.text = text or ""

    def json(self):
        if isinstance(self._payload, Exception):
            raise self._payload
        return self._payload


class ClassifyTest(unittest.TestCase):
    def test_left_river_wins_when_it_spikes_first(self) -> None:
        result = classify(
            [
                sample("Krasak", -5, 20),
                sample("Krasak", -1, 22),
                sample("Krasak", 1, 28),
                sample("Bebeng", -5, 19),
                sample("Bebeng", 2, 40),
            ],
            EVENT,
        )
        self.assertEqual(result.hasil_akhir, "Krasak")
        self.assertEqual(result.arah, ARAH_KIRI)
        self.assertEqual(result.winner, "Krasak")
        self.assertEqual(result.spike_time, EVENT + timedelta(minutes=1))

    def test_right_river_and_case_insensitive_name(self) -> None:
        result = classify(
            [
                sample("putih", -4, 10),
                sample("Kali Putih", 1, 16),
                sample("boyong", -4, 10),
                sample("boyong", 3, 30),
            ],
            EVENT,
        )
        self.assertEqual(result.hasil_akhir, "Putih")
        self.assertEqual(result.arah, ARAH_KANAN)

    def test_spike_uses_first_sample_at_threshold_not_the_hottest(self) -> None:
        result = classify(
            [
                sample("Sat", -8, 20),
                sample("Sat", -2, 20),
                sample("Sat", 0, 24),
                sample("Sat", 1, 25),
                sample("Sat", 2, 40),
            ],
            EVENT,
        )
        self.assertEqual(result.winner, "Sat")
        self.assertEqual(result.arah, ARAH_KIRI)
        self.assertEqual(result.spike_time, EVENT + timedelta(minutes=1))
        self.assertEqual(result.baseline, 20)

    def test_even_baseline_uses_median(self) -> None:
        result = classify(
            [
                sample("Lamat", -6, 20),
                sample("Lamat", -2, 30),
                sample("Lamat", 1, 29.9),
                sample("Lamat", 2, 30),
            ],
            EVENT,
        )
        self.assertEqual(result.baseline, 25)
        self.assertEqual(result.winner, "Lamat")
        self.assertEqual(result.arah, ARAH_KANAN)
        self.assertEqual(result.spike_time, EVENT + timedelta(minutes=2))

    def test_unmapped_river_keeps_name_and_unknown_direction(self) -> None:
        result = classify(
            [
                sample("Gendol", -3, 15),
                sample("gendol", 1, 21),
                sample("Kuning", -3, 15),
                sample("Kuning", 2, 30),
            ],
            EVENT,
        )
        self.assertEqual(result.hasil_akhir, "Gendol")
        self.assertEqual(result.arah, TIDAK_TERDETEKSI)
        self.assertEqual(result.winner, "Gendol")

    def test_no_samples_is_tidak_terdeteksi(self) -> None:
        result = classify([], EVENT)
        self.assertEqual(result.hasil_akhir, TIDAK_TERDETEKSI)
        self.assertEqual(result.arah, TIDAK_TERDETEKSI)
        self.assertIsNone(result.winner)

    def test_no_baseline_is_tidak_terdeteksi(self) -> None:
        result = classify([sample("Krasak", 1, 50)], EVENT)
        self.assertEqual(result.hasil_akhir, TIDAK_TERDETEKSI)
        self.assertEqual(result.arah, TIDAK_TERDETEKSI)

    def test_tie_breaks_alphabetically(self) -> None:
        result = classify(
            [
                sample("Boyong", -2, 10),
                sample("Boyong", 1, 20),
                sample("Bebeng", -2, 10),
                sample("Bebeng", 1, 20),
            ],
            EVENT,
        )
        self.assertEqual(result.winner, "Bebeng")
        self.assertEqual(result.arah, ARAH_KANAN)


class ThermalClientTest(unittest.TestCase):
    def test_fetch_sends_api_key_and_jakarta_window(self) -> None:
        payload = {
            "Krasak": [
                {"datetime": "2026-09-23 08:50:00", "temperature": "20"},
                {"datetime": "2026-09-23 09:01:00", "temperature": 26},
            ],
            "Bebeng": [
                {"datetime": "2026-09-23 08:50:00", "temperature": 20},
                {"datetime": "2026-09-23 09:03:00", "temperature": 40},
            ],
        }
        response = FakeResponse(payload)
        with patch(
            "waveview.contrib.bma.thermal_direction.client.requests.get",
            return_value=response,
        ) as get:
            client = ThermalAxisClient("https://bma.example", "secret-from-env")
            samples = client.fetch(EVENT)

        get.assert_called_once()
        args, kwargs = get.call_args
        self.assertEqual(args[0], "https://bma.example/api/v1/thermal-axis-jrg/")
        self.assertEqual(kwargs["headers"]["Authorization"], "Api-Key secret-from-env")
        self.assertEqual(kwargs["params"]["eventdate"], "2026-09-23 09:00:00")
        self.assertEqual(kwargs["params"]["datetime_before"], "2026-09-23 08:50:00")
        self.assertEqual(kwargs["params"]["datetime_after"], "2026-09-23 09:02:00")
        self.assertIn("Krasak", kwargs["params"]["rivers"])
        self.assertNotIn("secret", args[0])

        result = classify(samples, EVENT)
        self.assertEqual(result.hasil_akhir, "Krasak")
        self.assertEqual(result.arah, ARAH_KIRI)

    def test_list_payload_and_offset_timestamp(self) -> None:
        payload = [
            {
                "river": "Sat",
                "timestamp": "2026-09-23T01:55:00+00:00",
                "suhu": 11,
            },
            {
                "river": "Sat",
                "timestamp": "2026-09-23T02:01:00Z",
                "suhu": 17,
            },
        ]
        with patch(
            "waveview.contrib.bma.thermal_direction.client.requests.get",
            return_value=FakeResponse(payload),
        ):
            samples = ThermalAxisClient("https://bma.example", "k").fetch(EVENT)
        result = classify(samples, EVENT)
        self.assertEqual(result.winner, "Sat")
        self.assertEqual(result.arah, ARAH_KIRI)

    def test_empty_key_does_not_call_http(self) -> None:
        with patch(
            "waveview.contrib.bma.thermal_direction.client.requests.get"
        ) as get:
            with self.assertRaises(Exception) as caught:
                ThermalAxisClient("https://bma.example", "").fetch(EVENT)
        get.assert_not_called()
        self.assertFalse(caught.exception.retryable)

    def test_rejected_key_is_not_retryable(self) -> None:
        with patch(
            "waveview.contrib.bma.thermal_direction.client.requests.get",
            return_value=FakeResponse({}, status=401, text="unauthorized"),
        ):
            with self.assertRaises(Exception) as caught:
                ThermalAxisClient("https://bma.example", "k").fetch(EVENT)
        self.assertFalse(caught.exception.retryable)

    def test_server_error_is_retryable(self) -> None:
        with patch(
            "waveview.contrib.bma.thermal_direction.client.requests.get",
            return_value=FakeResponse({}, status=503, text="down"),
        ):
            with self.assertRaises(Exception) as caught:
                ThermalAxisClient("https://bma.example", "k").fetch(EVENT)
        self.assertTrue(caught.exception.retryable)

    def test_network_error_is_retryable(self) -> None:
        with patch(
            "waveview.contrib.bma.thermal_direction.client.requests.get",
            side_effect=requests.ConnectionError("reset"),
        ):
            with self.assertRaises(Exception) as caught:
                ThermalAxisClient("https://bma.example", "k").fetch(EVENT)
        self.assertTrue(caught.exception.retryable)


class NoteTest(unittest.TestCase):
    def test_replaces_previous_block_only(self) -> None:
        result = classify(
            [sample("Boyong", -2, 10), sample("Boyong", 1, 20)],
            EVENT,
        )
        block = render_thermal_note(result, datetime(2026, 9, 23, 2, 5, tzinfo=timezone.utc))
        note = upsert_event_note("Operator note", block)
        again = upsert_event_note(note, block)
        self.assertEqual(again.count("[thermal-direction]"), 1)
        self.assertIn("Operator note", again)
        self.assertIn("hasil_akhir: Boyong", again)
        self.assertIn("arah: Kiri", again)
        self.assertIn("winner: Boyong", again)
        self.assertIn("classified_at: 2026-09-23T02:05:00+00:00", again)


class BulletinFieldsTest(unittest.TestCase):
    def test_merge_sets_direction_and_replaces_remark(self) -> None:
        result = classify(
            [sample("Senowo", -1, 5), sample("Senowo", 1, 12)],
            EVENT,
        )
        merged = apply_direction_fields(
            {"eventid": "abc", "remark": "Arah termal: Kiri; Hasil akhir: Sat\nkeep"},
            result,
        )
        self.assertEqual(merged["eventid"], "abc")
        self.assertEqual(merged["arah"], ARAH_KANAN)
        self.assertEqual(merged["hasil_akhir"], "Senowo")
        self.assertEqual(merged["arah_sumber"], ARAH_KANAN)
        self.assertIn("Arah termal: Kanan; Hasil akhir: Senowo", merged["remark"])
        self.assertIn("keep", merged["remark"])
        self.assertEqual(merged["remark"].count("Arah termal:"), 1)

    def test_closest_bulletin_prefers_event_type(self) -> None:
        rows = [
            {
                "eventid": "other",
                "eventdate": "2026-09-23 09:00:00",
                "eventtype": "VT",
            },
            {
                "eventid": "rf-1",
                "eventdate": "2026-09-23 09:00:30",
                "eventtype": "RF",
            },
        ]
        self.assertEqual(closest_bulletin_id(rows, EVENT, event_type="RF"), "rf-1")


class BulletinClientTest(unittest.TestCase):
    def _client(self) -> BulletinDirectionClient:
        return BulletinDirectionClient("https://bma.example", "secret-from-env")

    def _result(self):
        return classify(
            [sample("Krasak", -2, 10), sample("Krasak", 1, 20)],
            EVENT,
        )

    def test_patch_uses_refid_and_api_key(self) -> None:
        response = FakeResponse({})
        with patch(
            "waveview.contrib.bma.thermal_direction.bulletin.requests.request",
            return_value=response,
        ) as request:
            self._client().push(refid="bulletin-1", event_time=EVENT, result=self._result())
        request.assert_called_once()
        args, kwargs = request.call_args
        self.assertEqual(args[0], "patch")
        self.assertIn("/api/v1/crud/bulletin/bulletin-1/", args[1])
        self.assertEqual(kwargs["headers"]["Authorization"], "Api-Key secret-from-env")
        self.assertEqual(kwargs["json"]["arah"], ARAH_KIRI)
        self.assertEqual(kwargs["json"]["hasil_akhir"], "Krasak")
        self.assertNotIn("secret-from-env", args[1])

    def test_missing_refid_searches_by_event_time(self) -> None:
        search = FakeResponse(
            [
                {
                    "eventid": "found",
                    "eventdate": "2026-09-23 09:00:00",
                    "eventtype": "APG",
                }
            ]
        )
        patched = FakeResponse({})
        with patch(
            "waveview.contrib.bma.thermal_direction.bulletin.requests.request",
            side_effect=[search, patched],
        ) as request:
            self._client().push(
                refid=None,
                event_time=EVENT,
                result=self._result(),
                event_type="APG",
            )
        self.assertEqual(request.call_count, 2)
        search_args, search_kwargs = request.call_args_list[0]
        self.assertEqual(search_args[0], "get")
        self.assertTrue(search_args[1].endswith("/api/v1/bulletin/"))
        self.assertEqual(search_kwargs["params"]["eventdate__gte"], "2026-09-23 08:59:00")
        patch_args, _patch_kwargs = request.call_args_list[1]
        self.assertEqual(patch_args[0], "patch")
        self.assertIn("/bulletin/found/", patch_args[1])

    def test_rejected_patch_falls_back_to_put(self) -> None:
        rejected = FakeResponse({}, status=405, text="method")
        current = FakeResponse({"eventid": "bulletin-1", "remark": "hello"})
        updated = FakeResponse({})
        with patch(
            "waveview.contrib.bma.thermal_direction.bulletin.requests.request",
            side_effect=[rejected, current, updated],
        ) as request:
            self._client().push(refid="bulletin-1", event_time=EVENT, result=self._result())
        methods = [call.args[0] for call in request.call_args_list]
        self.assertEqual(methods, ["patch", "get", "put"])
        put_body = request.call_args_list[2].kwargs["json"]
        self.assertEqual(put_body["eventid"], "bulletin-1")
        self.assertEqual(put_body["hasil_akhir"], "Krasak")
        self.assertIn("hello", put_body["remark"])

    def test_missing_bulletin_does_not_raise(self) -> None:
        with patch(
            "waveview.contrib.bma.thermal_direction.bulletin.requests.request",
            return_value=FakeResponse({}, status=404, text="missing"),
        ):
            self._client().push(refid="gone", event_time=EVENT, result=self._result())

    def test_server_error_raises(self) -> None:
        with patch(
            "waveview.contrib.bma.thermal_direction.bulletin.requests.request",
            return_value=FakeResponse({}, status=503, text="down"),
        ):
            with self.assertRaises(BulletinUpdateError):
                self._client().push(refid="bulletin-1", event_time=EVENT, result=self._result())


class EventTypeFilterTest(unittest.TestCase):
    def test_code_or_name(self) -> None:
        rf = SimpleNamespace(type=SimpleNamespace(code="rf", name="Rockfall"))
        apg = SimpleNamespace(type=SimpleNamespace(code="APG", name=None))
        named = SimpleNamespace(type=SimpleNamespace(code="OTHER", name="apg"))
        other = SimpleNamespace(type=SimpleNamespace(code="VT", name="Volcanic"))
        self.assertTrue(is_rf_or_apg(rf))
        self.assertTrue(is_rf_or_apg(apg))
        self.assertTrue(is_rf_or_apg(named))
        self.assertFalse(is_rf_or_apg(other))
        self.assertFalse(is_rf_or_apg(SimpleNamespace(type=None)))


if __name__ == "__main__":
    unittest.main()
