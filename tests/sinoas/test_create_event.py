import unittest

import pytest
from django.utils import timezone

from waveview.contrib.sinoas.context import SinoasContext
from waveview.contrib.sinoas.detector import DetectedEvent, Detector
from waveview.event.models import Event
from waveview.organization.models import Organization
from waveview.users.models import User
from waveview.volcano.models import Volcano


@pytest.mark.django_db
class CreateEventTest(unittest.TestCase):
    def test_create_event(self) -> None:
        user, __ = User.objects.get_or_create(username="test")
        organization, __ = Organization.objects.get_or_create(
            slug="test", name="Test Organization"
        )
        volcano, __ = Volcano.objects.get_or_create(
            organization=organization, slug="test", name="Test Volcano"
        )
        context = SinoasContext(organization=organization, volcano=volcano, user=user)
        detected_event = DetectedEvent(
            time=timezone.now(),
            duration=10,
            mepas_rsam=1000,
        )
        detector = Detector(context=context)
        detector.create_event(detected_event)

        events = Event.objects.all()
        self.assertTrue(events.exists())


if __name__ == "__main__":
    unittest.main()
