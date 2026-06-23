import numpy as np
import matplotlib.pyplot as plt

FONT_SIZE = 20

# ============================================================
# Parameters
# ============================================================

signal_frequency = 5    # true signal frequency in Hz
sampling_rate = 10       # number of measurements per second
bit_depth = 2           # 1 bit = 2 levels, 2 bits = 4 levels, etc.
duration = 1            # seconds

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

# ADC codes: round each sample to an integer level 0 … (n_levels - 1)
quantized_codes = np.round(sampled_signal * (n_levels - 1))
# Rescale codes back to [0, 1] for plotting
quantized_signal = quantized_codes / (n_levels - 1)

# ============================================================
# Plot
# ============================================================

fig, ax = plt.subplots(figsize=(12, 6))

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

# Allowed levels at this bit depth (quantized values snap here)
for level in np.linspace(0, 1, n_levels):
    ax.axhline(
        level,
        linestyle=":",
        color="C1",
        alpha=0.4,
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

# Orange dots — stored values after rounding to bit_depth levels
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
    fontsize=FONT_SIZE,
)

ax.set_xlabel("Time (s)", fontsize=FONT_SIZE)
ax.set_ylabel("Signal Amplitude", fontsize=FONT_SIZE)
ax.tick_params(axis="both", labelsize=FONT_SIZE)

ax.set_xlim(0, duration)
ax.set_ylim(-0.05, 1.05)

ax.legend(fontsize=FONT_SIZE)
ax.grid(False)

plt.tight_layout()
plt.show()