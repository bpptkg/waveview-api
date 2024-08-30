from waveview.contrib.bpptkg.magnitude import MagnitudeCalculator
from waveview.contrib.magnitude.base import register_magnitude_calculator

register_magnitude_calculator("bpptkg", MagnitudeCalculator)
