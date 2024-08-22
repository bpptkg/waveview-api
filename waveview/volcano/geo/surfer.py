from io import StringIO

import numpy as np

from waveview.volcano.geo.types import XYZGrid


class SurferGridReader:
    """
    Read Surfer Grid file format (GRD).
    """

    def read(self, file: str) -> XYZGrid:
        with open(file, "r") as f:
            grid = self._read_grid(f)

        return grid

    def _read_grid(self, f: StringIO) -> XYZGrid:
        name = f.readline()

        size = f.readline().split()
        ncols = int(size[0])
        nrows = int(size[1])

        xlo = f.readline().split()
        xmin = float(xlo[0])
        xmax = float(xlo[1])

        ylo = f.readline().split()
        ymin = float(ylo[0])
        ymax = float(ylo[1])

        zlo = f.readline().split()
        zmin = float(zlo[0])
        zmax = float(zlo[1])

        result = []
        for __ in range(nrows):
            arr = []
            while True:
                string = f.readline().split()
                if string:
                    arr += [float(s) for s in string]
                else:
                    break
            result.append(arr)

        longitude = np.linspace(xmin, xmax, ncols)
        latitude = np.linspace(ymin, ymax, nrows)
        elev = np.array(result)

        xyz = []
        for i in range(nrows):
            for j in range(ncols):
                xyz.append((longitude[j], latitude[i], elev[i][j]))

        return XYZGrid(
            name=name,
            nx=ncols,
            ny=nrows,
            x_min=xmin,
            x_max=xmax,
            y_min=ymin,
            y_max=ymax,
            z_min=zmin,
            z_max=zmax,
            xyz=xyz,
        )
