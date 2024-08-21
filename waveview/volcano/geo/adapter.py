from waveview.volcano.geo.surfer import SurferGridReader
from waveview.volcano.geo.types import XYZGrid
from waveview.volcano.header import DEMFileFormat


class DEMDataReader:
    def __init__(self, file_format: str):
        self.file_format = file_format
        if self.file_format == DEMFileFormat.SURFER_GRID:
            self.reader = SurferGridReader()
        else:
            raise ValueError("Unsupported DEM file format.")

    def read(self, file_path: str) -> XYZGrid:
        return self.reader.read(file_path)
