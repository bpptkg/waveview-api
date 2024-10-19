from pathlib import Path

from obspy import Stream, read

SAMPLE_DIR = Path(__file__).resolve().parent


def get_sample_file_path(filename: str) -> Path:
    return SAMPLE_DIR / filename


def get_sample_waveform() -> Stream:
    """
    Returns an ObsPy Stream object from the sample.mseed file.
    """
    return read(get_sample_file_path("sample.mseed"))
