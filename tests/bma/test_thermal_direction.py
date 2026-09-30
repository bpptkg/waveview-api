import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

from waveview.contrib.bma.thermal_direction.bulletin import (
    ThermalBulletinError,
    push_bulletin_direction,
)
from waveview.contrib.bma.thermal_direction.classifier import (
    ThermalSample,
    classify,
    is_rf_or_apg,
    upsert_thermal_note,
)
from waveview.contrib.bma.thermal_direction.client import ThermalAxisClient


EVENT = datetime(2026, 9, 23, 10, 0, tzinfo=timezone.utc)


def sample(river: str, minutes: float, temperature: float) -> ThermalSample:
    return ThermalSample(
        river=river,
        time=EVENT + timedelta(minutes=minutes),
        temperature=temperature,
    )


class ClassifyThermalDirectionTest(unittest.TestCase):
    def test_earliest_spike_on_left_river(self) -> None:
        samples = [
            sample("Krasak", -5, 20),
            sample("Krasak", -1, 22),
            sample("Krasak", 1, 27),
            sample("Bebeng", -5, 18),
            sample("Bebeng", -1, 18),
            sample("Bebeng", 2, 40),
        ]
        result = classify(EVENT, samples)
        self.assertEqual(result.hasil_akhir, "Krasak")
        self.assertEqual(result.arah, "Kiri")
        self.assertEqual(result.winner, "Krasak")

    def test_right_river_wins_when_it_spikes_first(self) -> None:
        samples = [
            sample("putih", -4, 10),
            sample("putih", 1, 16),
            sample("Sat", -4, 30),
            sample("Sat", 3, 40),
        ]
        result = classify(EVENT, samples)
        self.assertEqual(result.hasil_akhir, "Putih")
        self.assertEqual(result.arah, "Kanan")
        self.assertEqual(result.winner, "Putih")

    def test_no_samples_is_tidak_terdeteksi(self) -> None:
        result = classify(EVENT, [])
        self.assertEqual(result.hasil_akhir, "Tidak terdeteksi")
        self.assertEqual(result.arah, "Tidak terdeteksi")
        self.assertIsNone(result.winner)

    def test_samples_below_threshold_are_tidak_terdeteksi(self) -> None:
        samples = [
            sample("Boyong", -3, 20),
            sample("Boyong", -1, 22),
            sample("Boyong", 1, 25),
        ]
        result = classify(EVENT, samples)
        self.assertEqual(result.hasil_akhir, "Tidak terdeteksi")
        self.assertEqual(result.arah, "Tidak terdeteksi")
        self.assertIsNone(result.winner)

    def test_unmapped_river_keeps_name_and_unknown_direction(self) -> None:
        samples = [
            sample("Gendol", -2, 15),
            sample("Gendol", 1, 21),
            sample("Kuning", -2, 15),
            sample("Kuning", 2, 30),
        ]
        result = classify(EVENT, samples)
        self.assertEqual(result.hasil_akhir, "Gendol")
        self.assertEqual(result.arah, "Tidak terdeteksi")
        self.assertEqual(result.winner, "Gendol")

    def test_spike_is_first_sample_at_least_five_degrees_above_median(self) -> None:
        samples = [
            sample("Lamat", -6, 10),
            sample("Lamat", -2, 14),
            sample("Lamat", 1, 16),
            sample("Lamat", 2, 17),
            sample("Lamat", 3, 40),
        ]
        result = classify(EVENT, samples)
        self.assertEqual(result.hasil_akhir, "Lamat")
        self.assertEqual(result.arah, "Kanan")
        self.assertEqual(result.spike_time, EVENT + timedelta(minutes=2))

    def test_note_block_replaces_previous_thermal_direction_block(self) -> None:
        classified_at = datetime(2026, 9, 23, 10, 2, tzinfo=timezone.utc)
        existing = (
            "catatan operator\n\n"
            "[thermal-direction]\n"
            "hasil_akhir: Putih\n"
            "arah: Kanan\n"
            "winner: Putih\n"
            "classified_at: 2020-01-01T00:00:00+00:00\n"
            "[/thermal-direction]\n"
        )
        result = classify(
            EVENT,
            [sample("Krasak", -1, 10), sample("Krasak", 1, 20)],
        )
        updated = upsert_thermal_note(existing, result, classified_at)
        self.assertIn("catatan operator", updated)
        self.assertIn("hasil_akhir: Krasak", updated)
        self.assertIn("arah: Kiri", updated)
        self.assertNotIn("Putih", updated)
        self.assertEqual(updated.count("[thermal-direction]"), 1)
        self.assertEqual(updated.count("[/thermal-direction]"), 1)

    def test_is_rf_or_apg_matches_code_or_name_case_insensitively(self) -> None:
        self.assertTrue(is_rf_or_apg("RF", "Rockfall"))
        self.assertTrue(is_rf_or_apg("apg", None))
        self.assertTrue(is_rf_or_apg(None, " APG "))
        self.assertFalse(is_rf_or_apg("ROCKFALL", "Rockfall"))
        self.assertFalse(is_rf_or_apg("AWANPANAS", "Awan Panas"))
        self.assertFalse(is_rf_or_apg("VTA", None))
        self.assertFalse(is_rf_or_apg(None, None))


class ThermalAxisClientTest(unittest.TestCase):
    def test_fetch_sends_api_key_window_and_rivers(self) -> None:
        session = MagicMock()
        response = MagicMock()
        response.ok = True
        response.json.return_value = [
            {
                "river": "Krasak",
                "datetime": "2026-09-23T09:55:00Z",
                "temperature": 21.5,
            },
            {
                "sungai": "Bebeng",
                "time": "2026-09-23T10:01:00+00:00",
                "suhu": "30",
            },
        ]
        session.get.return_value = response
        client = ThermalAxisClient(
            "https://bma.example/base",
            "test-key",
            session=session,
        )

        samples = client.fetch(EVENT)

        session.get.assert_called_once()
        url = session.get.call_args.args[0]
        kwargs = session.get.call_args.kwargs
        self.assertEqual(
            url, "https://bma.example/base/api/v1/thermal-axis-jrg/"
        )
        self.assertEqual(kwargs["headers"]["Authorization"], "Api-Key test-key")
        self.assertNotIn("test-key", url)
        params = kwargs["params"]
        self.assertIn(("eventdate", "2026-09-23T10:00:00Z"), params)
        self.assertIn(("datetime_before", "2026-09-23T09:50:00Z"), params)
        self.assertIn(("datetime_after", "2026-09-23T10:02:00Z"), params)
        for river in ("Sat", "Bebeng", "Krasak", "Putih", "Boyong", "Kuning", "Gendol"):
            self.assertIn(("river", river), params)
        self.assertEqual(samples[0].river, "Krasak")
        self.assertEqual(samples[0].temperature, 21.5)
        self.assertEqual(samples[1].river, "Bebeng")
        self.assertEqual(samples[1].temperature, 30.0)
        self.assertEqual(samples[1].time, datetime(2026, 9, 23, 10, 1, tzinfo=timezone.utc))

    def test_fetch_parses_rivers_grouped_by_name(self) -> None:
        session = MagicMock()
        response = MagicMock()
        response.ok = True
        response.json.return_value = {
            "results": {
                "Sat": [{"datetime": "2026-09-23T09:58:00Z", "temp": 12}],
            }
        }
        session.get.return_value = response
        client = ThermalAxisClient("https://bma.example", "test-key", session=session)
        samples = client.fetch(EVENT)
        self.assertEqual(len(samples), 1)
        self.assertEqual(samples[0].river, "Sat")
        self.assertEqual(samples[0].temperature, 12)

    def test_http_error_does_not_include_api_key(self) -> None:
        session = MagicMock()
        response = MagicMock()
        response.ok = False
        response.status_code = 403
        response.text = "nope secret-key"
        session.get.return_value = response
        client = ThermalAxisClient("https://bma.example", "secret-key", session=session)
        with self.assertRaises(Exception) as raised:
            client.fetch(EVENT)
        self.assertNotIn("secret-key", str(raised.exception))


class PushArahKubahTest(unittest.TestCase):
    def test_patch_sends_hasil_akhir_not_kiri_kanan(self) -> None:
        session = MagicMock()
        response = MagicMock()
        response.ok = True
        session.patch.return_value = response
        result = classify(
            EVENT,
            [sample("Krasak", -1, 10), sample("Krasak", 1, 20)],
        )
        self.assertEqual(result.arah, "Kiri")

        push_bulletin_direction(
            base_url="https://bma.example/base/",
            api_key="test-key",
            bulletin_id="evt-1",
            result=result,
            session=session,
        )

        session.get.assert_not_called()
        session.put.assert_not_called()
        session.patch.assert_called_once()
        url = session.patch.call_args.args[0]
        kwargs = session.patch.call_args.kwargs
        self.assertEqual(
            url,
            "https://bma.example/base/api/v1/crud/bulletin/evt-1/arah_kubah/",
        )
        self.assertEqual(kwargs["json"], {"arah_kubah": "Krasak"})
        self.assertEqual(kwargs["headers"]["Authorization"], "Api-Key test-key")
        self.assertNotIn("Kiri", str(kwargs["json"]))

    def test_patch_sends_tidak_terdeteksi_river_name(self) -> None:
        session = MagicMock()
        response = MagicMock()
        response.ok = True
        session.patch.return_value = response
        result = classify(EVENT, [])
        self.assertEqual(result.hasil_akhir, "Tidak terdeteksi")

        push_bulletin_direction(
            base_url="https://bma.example",
            api_key="test-key",
            bulletin_id="evt-2",
            result=result,
            session=session,
        )

        self.assertEqual(
            session.patch.call_args.kwargs["json"],
            {"arah_kubah": "Tidak terdeteksi"},
        )

    def test_missing_refid_looks_up_bulletin_then_patches_winner(self) -> None:
        session = MagicMock()
        listed = MagicMock()
        listed.ok = True
        listed.status_code = 200
        listed.json.return_value = {
            "results": [
                {"eventid": "bma-9", "eventdate": "2026-09-23 17:00:00"},
            ]
        }
        patched = MagicMock()
        patched.ok = True
        session.get.return_value = listed
        session.patch.return_value = patched
        result = classify(
            EVENT,
            [sample("Bebeng", -2, 10), sample("Bebeng", 1, 20)],
        )
        self.assertEqual(result.arah, "Kanan")

        push_bulletin_direction(
            base_url="https://bma.example",
            api_key="test-key",
            bulletin_id=None,
            result=result,
            event_time=EVENT,
            session=session,
        )

        self.assertEqual(
            session.get.call_args.args[0],
            "https://bma.example/api/v1/bulletin/",
        )
        self.assertEqual(
            session.get.call_args.kwargs["headers"]["Authorization"],
            "Api-Key test-key",
        )
        self.assertEqual(
            session.patch.call_args.args[0],
            "https://bma.example/api/v1/crud/bulletin/bma-9/arah_kubah/",
        )
        self.assertEqual(
            session.patch.call_args.kwargs["json"],
            {"arah_kubah": "Bebeng"},
        )
        session.put.assert_not_called()

    def test_patch_failure_raises_without_detail_put(self) -> None:
        session = MagicMock()
        response = MagicMock()
        response.ok = False
        response.status_code = 404
        session.patch.return_value = response
        result = classify(
            EVENT,
            [sample("Boyong", -1, 10), sample("Boyong", 1, 20)],
        )

        with self.assertRaises(ThermalBulletinError):
            push_bulletin_direction(
                base_url="https://bma.example",
                api_key="test-key",
                bulletin_id="evt-3",
                result=result,
                session=session,
            )

        self.assertEqual(
            session.patch.call_args.args[0],
            "https://bma.example/api/v1/crud/bulletin/evt-3/arah_kubah/",
        )
        session.put.assert_not_called()


class ThermalDirectionObserverTest(unittest.TestCase):
    @patch(
        "waveview.contrib.bma.thermal_direction.task.classify_thermal_direction.apply_async"
    )
    def test_create_schedules_task_after_120_seconds(self, apply_async: MagicMock) -> None:
        from waveview.contrib.bma.thermal_direction.observer import (
            ThermalDirectionObserver,
        )

        ThermalDirectionObserver().create("event-1", {})
        apply_async.assert_called_once_with(args=["event-1"], countdown=120)

    @patch(
        "waveview.contrib.bma.thermal_direction.task.classify_thermal_direction.apply_async"
    )
    def test_update_schedules_task(self, apply_async: MagicMock) -> None:
        from waveview.contrib.bma.thermal_direction.observer import (
            ThermalDirectionObserver,
        )

        ThermalDirectionObserver().update("event-1", {"delay": 30})
        apply_async.assert_called_once_with(args=["event-1"], countdown=30)

    @patch(
        "waveview.contrib.bma.thermal_direction.task.classify_thermal_direction.apply_async"
    )
    def test_delete_does_not_schedule(self, apply_async: MagicMock) -> None:
        from waveview.contrib.bma.thermal_direction.observer import (
            ThermalDirectionObserver,
        )

        ThermalDirectionObserver().delete("event-1", {})
        apply_async.assert_not_called()
