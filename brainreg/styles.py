"""
Shared visual styling constants for brainreg visualisation scripts.

Used by `brainreg_viewer.py` and `probes_to_html.py` for probes, atlas
regions, and custom OBJ meshes. `render_atlas.py` does not import this
module (it uses its own REGION_ALPHA for a full-atlas view).
"""

REGION_ALPHA = 0.2         # main highlighted atlas regions
ROOT_ALPHA = 0.2           # whole-brain outline
ROOT_COLOR = "grey"

CUSTOM_REGION_COLOR = "orangered"
CUSTOM_REGION_ALPHA = 0.4

PROBE_COLOR = "chartreuse"
PROBE_RADIUS = 50

