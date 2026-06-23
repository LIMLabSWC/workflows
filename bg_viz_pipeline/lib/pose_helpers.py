"""
Rigid rotations of atlas meshes about a pivot point.

Named poses rotate actor geometry (and slice-plane normals) via the angles
in ``POSE_ROTATIONS_DEG``.
"""

from __future__ import annotations

import math
from typing import Literal, Tuple

import numpy as np

SubjectPose = Literal["on_base", "on_bulb", "on_side"]

# Euler angles (degrees), applied x → y → z about the atlas centre.
# Atlas axes: frontal +x, horizontal +y, sagittal +z. Tune signs if flipped.
POSE_ROTATIONS_DEG: dict[SubjectPose, Tuple[float, float, float]] = {
    "on_base": (0.0, 0.0, 0.0),
    "on_bulb": (0.0, 0.0, -90.0),  # olfactory bulb toward +y
    "on_side": (90.0, 0.0, 0.0),   # lateral axis toward +y
}


def _rotation_matrix_axis(axis: Tuple[float, float, float], angle_deg: float) -> np.ndarray:
    """
    3×3 rotation matrix for a right-handed turn around ``axis``.

    Rodrigues' formula: rotate vector **v** by angle θ about unit axis **k**::

        v' = v cos θ + (k × v) sin θ + k (k·v) (1 − cos θ)

    The 3×3 matrix **R** is the same operation written as ``v' = R @ v``.
    """
    x, y, z = axis
    n = math.sqrt(x * x + y * y + z * z)
    if n == 0:
        return np.eye(3)
    # Unit axis **k** — direction does not matter, only the line through the origin.
    x, y, z = x / n, y / n, z / n
    th = math.radians(angle_deg)
    c, s = math.cos(th), math.sin(th)
    t = 1 - c  # (1 − cos θ), the component along **k** that survives the rotation
    # Symmetric 3×3 layout of Rodrigues' formula (one row shown in comments):
    #   R_ij mixes dot products with **k** and cross-product terms (±s).
    return np.array(
        [
            [t * x * x + c, t * x * y - s * z, t * x * z + s * y],
            [t * x * y + s * z, t * y * y + c, t * y * z - s * x],
            [t * x * z - s * y, t * y * z + s * x, t * z * z + c],
        ]
    )


def pose_rotation_matrix(pose: SubjectPose) -> np.ndarray:
    """
    Combined rotation matrix for a named pose.

    Three separate spins about atlas x, y, z are composed as::

        R = Rz @ Ry @ Rx

    Matrix multiplication applies **rightmost first**: Rx, then Ry, then Rz.
    Intuition: each step is a small re-orientation in atlas space; the product
    is one rigid turn you can reuse for both mesh points and direction vectors.
    """
    rx, ry, rz = POSE_ROTATIONS_DEG[pose]
    return (
        _rotation_matrix_axis((0.0, 0.0, 1.0), rz)
        @ _rotation_matrix_axis((0.0, 1.0, 0.0), ry)
        @ _rotation_matrix_axis((1.0, 0.0, 0.0), rx)
    )


def rotate_vector(vector: Tuple[float, float, float], pose: SubjectPose) -> Tuple[float, float, float]:
    """
    Rotate a direction (e.g. slice plane normal) with the specimen pose.

    Directions have no position — only orientation — so we apply **R** directly:
    ``v' = R @ v``.  A plane normal must use the same **R** as the mesh so the
    cut stays anatomically meaningful after the brain is re-mounted.
    """
    v = pose_rotation_matrix(pose) @ np.asarray(vector, dtype=float)
    return (float(v[0]), float(v[1]), float(v[2]))


def rotate_mesh_about_center(
    mesh,
    center: Tuple[float, float, float],
    pose: SubjectPose,
) -> None:
    """
    Rotate a vedo mesh in place about ``center``.

    Standard "rotate about a pivot" recipe (column-vector form)::

        p' = R @ (p − c) + c

    vedo stores ``mesh.points`` as an (N, 3) array of **row** vectors, so the
    equivalent is ``(p − c) @ R.T + c`` — transpose because row @ M applies M.T
    to each point treated as a column.
    """
    if pose == "on_base":
        return
    r = pose_rotation_matrix(pose)
    c = np.asarray(center, dtype=float)
    mesh.points = (np.asarray(mesh.points, dtype=float) - c) @ r.T + c
    mesh.compute_normals()


def apply_subject_pose(
    scene,
    pose: SubjectPose,
    center: Tuple[float, float, float],
) -> None:
    """
    Apply ``pose`` to every actor in ``scene`` (including cartoon silhouettes).

    Call after meshes are added and before camera / slice setup.
    """
    for actor in scene.clean_actors:
        mesh = getattr(actor, "_mesh", None) or actor.mesh
        rotate_mesh_about_center(mesh, center, pose)
        if actor.silhouette is not None:
            rotate_mesh_about_center(actor.silhouette.mesh, center, pose)
