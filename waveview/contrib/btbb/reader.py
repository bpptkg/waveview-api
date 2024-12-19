from itertools import zip_longest
from typing import Iterable, Iterator, Optional, TypedDict, TypeVar

T = TypeVar("T")

HEADER_KEYS = {
    "X": {"type": float},
    "Y": {"type": float},
    "Z": {"type": float},
    "MaxStack": {"type": float},
    "Ntraces": {"type": int},
    "BEG": {"type": float},
    "END": {"type": float},
    "LAT": {"type": float},
    "LON": {"type": float},
    "T_ORIG": {"type": str},
    "RMS-P": {"type": float},
}

PHASE_KEYS = {
    "sta": {"type": str},
    "Ph": {"type": str},
    "TT": {"type": float},
    "PT": {"type": float},
}

HeaderType = TypedDict(
    "HeaderType",
    {
        "TS": str,
        "X": float,
        "Y": float,
        "Z": float,
        "MaxStack": float,
        "Ntraces": int,
        "BEG": float,
        "END": float,
        "LAT": float,
        "LON": float,
        "T_ORIG": str,
        "RMS-P": float,
    },
)

PhaseType = TypedDict("PhaseType", {"sta": str, "Ph": str, "TT": float, "PT": float})


class ResultType(TypedDict):
    header: HeaderType
    phases: PhaseType


def grouper(
    iterable: Iterable[T], n: int, fillvalue: Optional[T] = None
) -> Iterator[tuple[Optional[T], ...]]:
    "Collect data into fixed-length chunks or blocks"
    args = [iter(iterable)] * n
    return zip_longest(*args, fillvalue=fillvalue)


class ResultReader:
    """
    Parse and read BackTrackBB result file.
    """

    @staticmethod
    def parse_header(line: str) -> dict:
        header = []
        line = line.strip().split()
        header.append(("TS", line[0]))
        for item in grouper(line[1:], 2):
            key = item[0]
            valuestr = item[1]
            config = HEADER_KEYS.get(key)
            if config is None:
                value = None
            else:
                try:
                    value = config["type"](valuestr)
                except ValueError:
                    value = None
            header.append((key, value))
        return dict(header)

    @staticmethod
    def parse_phase(line: str) -> dict:
        phases = []
        line = line.strip().split()
        for item in grouper(line, 2):
            key = item[0]
            valuestr = item[1]
            config = PHASE_KEYS.get(key)
            if config is None:
                value = None
            else:
                try:
                    value = config["type"](valuestr)
                except ValueError:
                    value = None
            phases.append((key, value))
        return dict(phases)

    @staticmethod
    def is_header(line: str) -> bool:
        """
        Determine that current line is header or not. Example header:

            20201202_0450A X -0.4 Y -0.2 Z -0.8 MaxStack 0.925 Ntraces 9 BEG 9.0 END 13.0  LAT -7.53881 LON 110.44537 T_ORIG 2020-12-02T04:50:15.542912Z RMS-P 0.39

        """
        line = line.strip().split()
        return len(line) == 23 and line[0] != "sta"

    def read(self, path: str) -> list[ResultType]:
        results = []
        with open(path, "r") as f:
            while True:
                line = f.readline()
                if not line:
                    break
                row = line.strip()
                if self.is_header(row):
                    item = {"header": None, "phases": []}
                    # Parse header line.
                    header = self.parse_header(row)
                    item["header"] = header

                    # Parse phase lines.
                    for _ in range(header["Ntraces"]):
                        row = f.readline().strip()
                        phase = self.parse_phase(row)
                        item["phases"].append(phase)

                    results.append(item)
        return results
