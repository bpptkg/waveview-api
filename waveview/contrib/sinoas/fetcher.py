from io import StringIO

import pandas as pd
import requests
from django.conf import settings


def build_rsam_url(code: str) -> str:
    return f"{settings.SINOAS_WINSTON_URL}/rsam/?code={code}&t1=-0.0006&rsamP=1&csv=1"


class Fetcher:
    def __init__(self, timeout: int = 5) -> None:
        self.timeout = timeout

    def process_csv(self, csv: str) -> pd.DataFrame:
        buf = StringIO(csv)
        df = pd.read_csv(buf, names=["time", "rsam", "comment"], usecols=[0, 1])
        df["time"] = pd.to_datetime(df["time"], utc=True)
        df["rsam"] = df["rsam"].abs()
        return df.iloc[:-1]

    def fetch(self, url: str) -> pd.DataFrame:
        response = requests.get(url, timeout=self.timeout)
        response.raise_for_status()
        return self.process_csv(response.text)
