from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt

FONT_SIZE = 20

# Edit this list: (signal frequency Hz, sampling rate Hz, bit depth, duration s).
COMBINATIONS = [
    (5, 8, 1, 1),
    (5, 11, 1, 1),
    (5, 11, 2, 1),
    (5, 11, 4, 1),
    (5, 11, 5, 1),
]
OUTPUT_DIR = Path(__file__).resolve().parent / "figures"

# Validate the whole batch before writing any figures. The fixed layout fits
# one- through five-bit labels; higher bit depths need more label space.
for signal_frequency, sampling_rate, bit_depth, duration in COMBINATIONS:
    if not all(np.isfinite([signal_frequency, sampling_rate, duration])):
        raise ValueError("Frequencies and duration must be finite.")
    if signal_frequency < 0 or sampling_rate <= 0 or duration <= 0:
        raise ValueError("Signal frequency must be nonnegative; rate and duration positive.")
    if not isinstance(bit_depth, int) or isinstance(bit_depth, bool) or not 1 <= bit_depth <= 5:
        raise ValueError("This teaching layout supports integer bit depths from 1 to 5.")

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

for signal_frequency, sampling_rate, bit_depth, duration in COMBINATIONS:
    # ============================================================
    # Continuous signal (high resolution)
    # ============================================================

    continuous_time = np.linspace(0, duration, 5000)

    # Sine wave: sin(2π f t) oscillates between -1 and +1.
    #   2π f t  — angle in radians; f cycles per second, t in seconds
    #   0.5 * … — scale amplitude to ±0.5
    #   + 0.5   — shift up so the wave sits between 0 and 1
    #             (for the plot and quantization)
    continuous_signal = (
        0.5 * np.sin(2 * np.pi * signal_frequency * continuous_time) + 0.5
    )

    # ============================================================
    # Sampled signal
    # ============================================================

    # Sample times: 0, 1/sampling_rate, 2/sampling_rate, …
    sample_times = np.arange(0, duration, 1 / sampling_rate)

    # Same sine formula, evaluated only at sample_times
    sampled_signal = (
        0.5 * np.sin(2 * np.pi * signal_frequency * sample_times) + 0.5
    )

    # ============================================================
    # Aliased signal
    # ============================================================

    # Aliasing: sines at signal_frequency and at signal_frequency ± N×sampling_rate
    # (N any integer) share the same height at every sample time — infinitely
    # many frequencies fit the same dots.
    #
    # alias_frequency folds signal_frequency to the slowest alias near 0 Hz.
    # Below Nyquist (sampling_rate / 2) it equals signal_frequency; above
    # Nyquist it differs. Only one sign matches: the same rate with the
    # opposite sign is a mirror image and misses the sample points.
    alias_frequency = (
        signal_frequency
        - round(signal_frequency / sampling_rate) * sampling_rate
    )

    # Gray curve at alias_frequency — same sample points as the true signal
    # (overlaps the blue curve when there is no aliasing)
    alias_signal = (
        0.5 * np.sin(2 * np.pi * alias_frequency * continuous_time) + 0.5
    )

    # ============================================================
    # Quantization (bit depth)
    # ============================================================

    # bit_depth bits → 2^bit_depth discrete levels between 0 and 1
    n_levels = 2 ** bit_depth

    bin_edges = np.linspace(0, 1, n_levels + 1)
    levels = (np.arange(n_levels) + 0.5) / n_levels

    # Each code represents a bin's midpoint. At an internal boundary, both
    # neighbouring midpoints are equally close; we choose the upper bin.
    # For 2 bits: [0, 0.25) -> 00, [0.25, 0.5) -> 01, etc.
    # Thus exactly 0.25 maps to code 01, plotted at its midpoint 0.375.
    #
    # Sine evaluation can produce 0.4999999999999999 or 0.5000000000000001
    # where mathematically both samples are 0.5. Round away this numerical
    # noise before choosing a bin, so those samples receive the same code.
    # The previous np.round(sample * (n_levels - 1)) was deterministic too,
    # but these tiny differences put samples on opposite sides of a boundary.
    # At exact ties, np.round uses ties-to-even, not an always-upper rule.
    # ponytail: rounding at 12 decimal places in code units suppresses sine
    # evaluation noise for this demo, but also merges real differences that
    # small; use an ADC's specified thresholds for data.
    scaled_samples = np.round(sampled_signal * n_levels, decimals=12)
    # floor selects the bin (an integer boundary selects the upper bin).
    # Clipping keeps amplitude 1 in the last bin rather than nonexistent code n_levels.
    quantized_codes = np.clip(np.floor(scaled_samples), 0, n_levels - 1).astype(int)
    quantized_signal = levels[quantized_codes]

    # ============================================================
    # Plot
    # ============================================================

    fig, ax = plt.subplots(figsize=(12, 6), layout="none")
    # Fixed margins keep data coordinates aligned across teaching figures,
    # even when titles, binary labels or the legend change. Do not use tight_layout.
    # Space is reserved for up to five-bit labels at FONT_SIZE=20, with a small
    # fixed outer padding. Keep these margins identical for the whole slide set.
    # When saving, omit bbox_inches="tight": it would crop each figure differently.
    fig.subplots_adjust(left=0.092, right=0.885, bottom=0.13, top=0.985)

    # True signal (blue) — what actually happened between sample times
    ax.plot(
        continuous_time,
        continuous_signal,
        linewidth=3,
        label=f"True continuous signal ({signal_frequency} Hz)"
    )

    # Alias (gray) — another frequency that fits the same sample values
    ax.plot(
        continuous_time,
        alias_signal,
        linewidth=3,
        linestyle="--",
        color="gray",
        alpha=0.5,
        label=f"Possible alias curve ({alias_frequency} Hz)",
    )

    # Vertical lines — when samples are taken (sampling_rate)
    for sample_time in sample_times:
        ax.axvline(
            sample_time,
            linestyle="--",
            alpha=0.35
        )

    # Input regions and their representative output levels.
    for code, level in enumerate(levels):
        ax.axhspan(
            bin_edges[code], bin_edges[code + 1],
            color="C1", alpha=0.05 if code % 2 == 0 else 0.13, zorder=0,
        )
        ax.axhline(
            level,
            linestyle=":",
            color="C1",
            alpha=0.4,
        )
    for boundary in bin_edges:
        ax.axhline(boundary, color="gray", linewidth=0.6, alpha=0.35)

    ax.vlines(
        sample_times, sampled_signal, quantized_signal,
        color="C1", linewidth=1.5, label="Quantization error",
    )

    # Blue dots — exact height of the true signal at each sample time
    ax.scatter(
        sample_times,
        sampled_signal,
        s=80,
        zorder=10,
        color="C0",
        edgecolors="white",
        linewidths=0.5,
        label="Exact signal values at sample times",
    )

    # Orange dots represent stored codes using the bin midpoints.
    ax.scatter(
        sample_times,
        quantized_signal,
        s=80,
        zorder=11,
        color="C1",
        edgecolors="white",
        label="Quantized signal values at sample times",
    )

    # ============================================================
    # Formatting
    # ============================================================

    nyquist_frequency = sampling_rate / 2

    ax.set_title(
        f"Sampling, aliasing, and quantization\n"
        f"Sampling rate = {sampling_rate} Hz | "
        f"Nyquist frequency = {nyquist_frequency} Hz | "
        f"True signal = {signal_frequency} Hz | "
        f"Bit depth = {bit_depth}",
        fontsize=12,
        y=0.98, pad=0, va="top",
        bbox=dict(facecolor="white", edgecolor="none", alpha=0.9, pad=3),
    )

    ax.set_xlabel("Time (s)", fontsize=FONT_SIZE)
    ax.set_ylabel("Signal Amplitude", fontsize=FONT_SIZE)
    ax.tick_params(axis="both", labelsize=FONT_SIZE)

    ax.set_xlim(0, duration)
    ax.set_ylim(-0.05, 1.05)

    code_axis = ax.secondary_yaxis("right")
    # Keep labels readable when demonstrating higher bit depths.
    label_stride = max(1, int(np.ceil(n_levels / 8)))
    label_codes = np.arange(0, n_levels, label_stride)
    code_axis.set_yticks(levels[label_codes])
    code_axis.set_yticklabels([format(code, f"0{bit_depth}b") for code in label_codes])
    code_axis.set_ylabel("ADC code (binary)", fontsize=FONT_SIZE)
    code_axis.tick_params(labelsize=FONT_SIZE)

    ax.legend(fontsize=10, loc="lower center", ncol=2, framealpha=0.9)
    ax.grid(False)

    # SVG preserves vector lines and text; fixed canvas size preserves alignment.
    # Re-running the same combination replaces its previous file.
    output_path = OUTPUT_DIR / (
        f"dsp_signal-{signal_frequency:g}Hz_sampling-{sampling_rate:g}Hz_"
        f"{bit_depth}bit_{duration:g}s.svg"
    )
    with plt.rc_context({"savefig.bbox": None}):
        fig.savefig(output_path, format="svg")
    plt.close(fig)
    print(f"Saved {output_path}")
