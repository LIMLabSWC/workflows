from __future__ import annotations

from typing import Dict, Tuple

# Batch presets and probes_to_html assume this frontal azimuth when omitted.
DEFAULT_BATCH_BASE_FRONTAL_AZIMUTH_DEG = 180.0


def _center_and_extent(
    bounds: Tuple[float, float, float, float, float, float],
) -> Tuple[Tuple[float, float, float], float]:
    """
    Given vtk-style bounds (xmin, xmax, ymin, ymax, zmin, zmax),
    return (center_x, center_y, center_z) and the maximum extent.
    """
    xmin, xmax, ymin, ymax, zmin, zmax = bounds
    # Midpoint of the axis-aligned bounding box — orbit and look-at target.
    cx = 0.5 * (xmin + xmax)
    cy = 0.5 * (ymin + ymax)
    cz = 0.5 * (zmin + zmax)
    ex = xmax - xmin
    ey = ymax - ymin
    ez = zmax - zmin
    # Largest edge length: a single scale for "how big is this brain?" so
    # distance_factor means the same thing regardless of which axis is longest.
    max_extent = max(ex, ey, ez)
    return (cx, cy, cz), max_extent


def make_camera_from_angles(
    bounds: Tuple[float, float, float, float, float, float],
    distance_factor: float,
    azimuth_deg: float,
    elevation_deg: float,
    up: Tuple[float, float, float] = (0.0, -1.0, 0.0),
) -> Dict:
    """
    Create a camera dict from atlas bounds and spherical angles.

    - bounds: six floats (xmin, xmax, ymin, ymax, zmin, zmax), e.g. from
      ``scene.root.bounds()`` or a union of actor bounds
    - distance_factor: how many times the max atlas extent to stand back
    - azimuth_deg: rotation around the "vertical" axis (y)
    - elevation_deg: tilt up/down
    - up: view-up vector; defaults to brainrender's convention (0, -1, 0)
    """
    import math

    center, max_extent = _center_and_extent(bounds)
    cx, cy, cz = center
    # Camera orbits on a sphere of this radius around ``center``.
    distance = distance_factor * max_extent

    az = math.radians(azimuth_deg)
    el = math.radians(elevation_deg)

    # Unit direction from centre toward the camera, in spherical coordinates.
    #
    # Picture standing on the xz "floor", y pointing up (superior):
    #   azimuth   — walk around the brain on a horizontal circle (0° = +x)
    #   elevation — tilt along atlas +y / −y (see scripts/README.md § Atlas coordinates)
    #
    #   dx = cos(el) cos(az)   horizontal part along x
    #   dy = sin(el)           vertical lift (0 when el = 0, on the xz ring)
    #   dz = cos(el) sin(az)   horizontal part along z
    #
    # cos(el) shrinks the horizontal ring as you tilt toward the poles.
    dx = math.cos(el) * math.cos(az)
    dy = math.sin(el)
    dz = math.cos(el) * math.sin(az)

    # Camera position = centre + distance × unit direction (not the other way:
    # we place the eye on the sphere, then look back at the centre).
    pos = (cx + distance * dx, cy + distance * dy, cz + distance * dz)

    return dict(
        pos=pos,
        focal_point=center,  # always stare at the atlas centre
        viewup=up,  # which way is "up" on screen (brainrender: −y)
        roll=0.0,
        distance=distance,  # nominal orbit radius (vedo/brainrender metadata)
        # Near/far clip planes scaled to distance so the mesh stays in view.
        clipping_range=(0.1 * distance, 3.0 * distance),
    )


def create_camera(
    bounds: Tuple[float, float, float, float, float, float],
    distance_factor: float,
    base_frontal_azimuth_deg: float,
    rotation_deg: float,
    elevation_deg: float,
) -> Dict:
    """
    Create a single atlas-aware camera from intuitive parameters.

    - bounds: six floats (xmin, xmax, ymin, ymax, zmin, zmax), e.g. from
      ``scene.root.bounds()`` or a union of actor bounds
    - distance_factor: how many times the max atlas extent to stand back
    - base_frontal_azimuth_deg: azimuth that corresponds to a frontal view
    - rotation_deg: extra rotation around the brain (left/right) added
      to the frontal azimuth
    - elevation_deg: tilt up/down
    """
    # Two-layer azimuth: a fixed "where is frontal for this atlas?" offset,
    # plus a user knob for left/right orbit.  Elevation is independent (tilt).
    azimuth = base_frontal_azimuth_deg + rotation_deg
    return make_camera_from_angles(
        bounds,
        distance_factor=distance_factor,
        azimuth_deg=azimuth,
        elevation_deg=elevation_deg,
    )
