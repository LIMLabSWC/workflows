"""
Shared visual styling constants for brainreg visualisation scripts.

Used by `brainreg_viewer.py` and `probes_to_html.py` for probes, atlas
regions, and custom OBJ meshes. Atlas region styling in presets uses
``ViewConfig`` fields (`REGION_ALPHA`, `ROOT_ALPHA`).
"""

REGION_ALPHA = 0.2         # main highlighted atlas regions
ROOT_ALPHA = 0.2           # whole-brain outline
ROOT_COLOR = "grey"

CUSTOM_REGION_COLOR = "orangered"
CUSTOM_REGION_ALPHA = 0.4

PROBE_COLOR = "chartreuse"
PROBE_RADIUS = 50

