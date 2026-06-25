"""
Shared defaults for atlas visualization scripts.

Colours, alphas, atlas name, and shader defaults used by ``interactive_render``,
``batch_render``, ``probes_to_html``, and ``ViewConfig`` preset parsing.
"""

from __future__ import annotations

from typing import Literal

# --- Atlas ---
DEFAULT_ATLAS_NAME = "viktors_tweaked_warp_swc_female_rat_25um"

# --- Batch preset defaults (when keys are omitted from viewer_presets.json) ---
BATCH_REGION_ALPHA = 0.2
BATCH_ROOT_ALPHA = 0.2
BATCH_SHADER_STYLE: Literal["plastic", "cartoon"] = "plastic"

# --- Interactive render defaults (interactive_render.py config block) ---
INTERACTIVE_ROOT_ALPHA = 0.8
INTERACTIVE_REGION_ALPHA = 1.0
INTERACTIVE_SHADER_STYLE: Literal["plastic", "cartoon"] = "cartoon"

# --- Colours ---
ROOT_COLOR = "grey"
CUSTOM_REGION_COLOR = "orangered"
CUSTOM_REGION_ALPHA = 0.4
PROBE_COLOR = "chartreuse"
PROBE_RADIUS = 50
CELLS_COLOR = "palegoldenrod"
CELLS_RADIUS = 45

# Backward-compatible aliases (batch region highlight alpha)
REGION_ALPHA = BATCH_REGION_ALPHA
ROOT_ALPHA = BATCH_ROOT_ALPHA
