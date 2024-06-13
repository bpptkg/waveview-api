import time

import cairo
import numpy as np
from obspy import Trace

from waveview.signal.packet import get_data
from waveview.ssr.axis import Axis
from waveview.ssr.types import ContextData, TrackData


class Renderer:
    def __init__(self, data: ContextData) -> None:
        self.data = data

    def get_trace(self, start: float, end: float) -> Trace:
        return get_data(start, end)

    def calc_norm_factor(self, tracks: list[TrackData]) -> float:
        factor = np.Infinity
        for track in tracks:
            start, end = track.xaxis_extent
            tr = get_data(start, end)
            minmax = np.max(tr.data) - np.min(tr.data)
            factor = np.min([factor, minmax])

        return factor

    def render(self) -> bytes:
        data = self.data
        width = int(data.width)
        height = int(data.height)
        rect = data.rect
        xaxis = Axis(extent=data.xaxis_extent, rect=rect, orientation="horizontal")

        surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
        ctx = cairo.Context(surface)

        norm_factor = self.calc_norm_factor(data.tracks)

        for track in data.tracks:
            yaxis = Axis(
                extent=track.yaxis_extent, rect=track.rect, orientation="vertical"
            )
            start, end = track.xaxis_extent
            tr = get_data(start, end)

            x = np.linspace(xaxis.min, xaxis.max, num=len(tr.data))
            y = tr.data / norm_factor

            self.draw_line(ctx, xaxis, yaxis, x, y)

        buffer = surface.get_data().tobytes()
        return buffer

    def draw_line(
        self,
        ctx: cairo.Context,
        xaxis: Axis,
        yaxis: Axis,
        x: np.ndarray,
        y: np.ndarray,
    ) -> None:
        it = np.nditer([x, y], flags=["c_index"])
        first = True

        while not it.finished:
            x, y = it[0], it[1]
            cx = xaxis.invert(x)
            cy = yaxis.invert(y)
            if first:
                ctx.move_to(cx, cy)
                first = False
            else:
                ctx.line_to(cx, cy)
            it.iternext()

        ctx.set_source_rgb(0, 0, 0)
        ctx.set_line_width(0.5)
        ctx.stroke()
