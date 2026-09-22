"""Run with MPLBACKEND=Agg python teaching/check_dsp.py."""

from pathlib import Path
import runpy
from tempfile import TemporaryDirectory
from unittest.mock import patch
import xml.etree.ElementTree as ET

from matplotlib.figure import Figure
import numpy as np


savefig = Figure.savefig
exports = []


def check_export(fig, filename, **kwargs):
    np.testing.assert_allclose(fig.axes[0].get_position().bounds, [0.092, 0.13, 0.793, 0.855])
    target = Path(temp_dir) / Path(filename).name
    savefig(fig, target, **kwargs)
    root = ET.parse(target).getroot()
    assert root.attrib["viewBox"] == "0 0 864 432"
    assert root.findall(".//{http://www.w3.org/2000/svg}path")
    exports.append(target.name)


with TemporaryDirectory() as temp_dir, patch.object(Figure, "savefig", check_export):
    plot = runpy.run_path(str(Path(__file__).with_name("dsp.py")))
assert len(exports) == len(plot["COMBINATIONS"])
assert len(set(exports)) == len(exports)

n = plot["n_levels"]
samples = plot["sampled_signal"]
codes = plot["quantized_codes"]
quantized = plot["quantized_signal"]
np.testing.assert_allclose(np.diff(plot["bin_edges"]), 1 / n)
np.testing.assert_allclose(quantized, (codes + 0.5) / n)
assert np.all((codes >= 0) & (codes < n))
assert np.all(np.abs(quantized - samples) <= 0.5 / n + 1e-12)
# The default sine repeatedly hits 0, 0.5 and 1; ties must be consistent.
for value, expected in [(0, 0), (0.5, n // 2), (1, n - 1)]:
    at_boundary = np.isclose(samples, value, rtol=0, atol=1e-14)
    assert at_boundary.any(), f"Demo no longer samples {value}"
    assert np.all(codes[at_boundary] == expected)

plot["fig"].canvas.draw()
# Changing slide labels must not move or resize the data area.
ax = plot["ax"]
np.testing.assert_allclose(ax.get_position().bounds, [0.092, 0.13, 0.793, 0.855])
renderer = plot["fig"].canvas.get_renderer()
figure_bounds = plot["fig"].bbox
for artist in [ax, ax.get_legend()]:
    bounds = artist.get_tightbbox(renderer)
    assert bounds.x0 >= 0 and bounds.y0 >= 0
    assert bounds.x1 <= figure_bounds.width and bounds.y1 <= figure_bounds.height
for artist in [ax.title, ax.get_legend()]:
    bounds = artist.get_window_extent(renderer)
    axes_bounds = ax.get_window_extent()
    assert bounds.x0 >= axes_bounds.x0 and bounds.y0 >= axes_bounds.y0
    assert bounds.x1 <= axes_bounds.x1 and bounds.y1 <= axes_bounds.y1
original_bounds = ax.get_window_extent().bounds
ax.set_title("Sampling only")
plot["code_axis"].set_visible(False)
ax.get_legend().set_visible(False)
plot["fig"].canvas.draw()
np.testing.assert_allclose(ax.get_window_extent().bounds, original_bounds)
print("Quantization and figure checks passed.")
