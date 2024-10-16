from pathlib import Path

SAMPLE_DIR = Path(__file__).resolve().parent


def get_sample_file_path(filename: str) -> Path:
    return SAMPLE_DIR / filename
