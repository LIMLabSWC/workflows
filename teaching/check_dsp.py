"""Run with MPLBACKEND=Agg python teaching/check_dsp.py."""

from pathlib import Path
import runpy
from unittest.mock import patch

import numpy as np


with patch("matplotlib.pyplot.show"):
    plot = runpy.run_path(str(Path(__file__).with_name("dsp.py")))

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
print("Quantization and figure checks passed.")
