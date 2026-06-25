from __future__ import annotations

from brainrender import Scene, settings

from bg_viz_pipeline.lib.bounds_helpers import bounds_center, union_bounds
from bg_viz_pipeline.lib.mesh_helpers import add_atlas_geometry
from bg_viz_pipeline.lib.pose_helpers import apply_subject_pose
from bg_viz_pipeline.lib.slice_helpers import apply_slice
from bg_viz_pipeline.lib.styles import ROOT_COLOR
from bg_viz_pipeline.lib.view_config import ViewConfig


def configure_brainrender(config: ViewConfig) -> None:
    """Apply per-render brainrender settings from ``config``."""
    settings.SHADER_STYLE = config.shader_style


def create_scene(
    config: ViewConfig,
    *,
    title: str,
    root: bool | None = None,
    offscreen: bool = False,
) -> Scene:
    """Create a brainrender ``Scene`` for interactive or batch rendering."""
    if root is None:
        root = config.regions_to_show is None and config.mesh_mode == "root"

    scene = Scene(
        atlas_name=config.atlas_name,
        title=title,
        root=root,
        check_latest=False,
    )
    if offscreen:
        scene.plotter.window.SetOffScreenRendering(True)
    return scene


def add_atlas_content(scene: Scene, config: ViewConfig) -> None:
    """
    Add atlas meshes: explicit region list (batch) or mesh_mode (interactive).
    """
    if config.regions_to_show is not None:
        for region in config.regions_to_show:
            scene.add_brain_region(
                region,
                alpha=config.region_alpha,
                silhouette=True,
            )
        if hasattr(scene, "root") and scene.root is not None:
            if config.show_root:
                scene.root.c(ROOT_COLOR).alpha(config.root_alpha)
            else:
                scene.root.alpha(0)
        return

    add_atlas_geometry(
        scene,
        mesh_mode=config.mesh_mode,
        region_mode=config.region_mode,
        root_alpha=config.root_alpha,
        region_alpha=config.region_alpha,
    )


def apply_view(scene: Scene, config: ViewConfig) -> dict | None:
    """
    Pose → camera → slice. Returns a camera dict or ``None`` if the scene is empty.
    """
    ub = union_bounds(scene)
    if ub is not None:
        apply_subject_pose(scene, config.subject_pose, bounds_center(ub))

    camera = None
    ub = union_bounds(scene)
    if ub is not None:
        camera = config.make_camera(ub)

    apply_slice(
        scene,
        config.subject_pose,
        config.slice_mode,
        config.plane_depth,
        config.custom_plane_normal,
        close_actors=config.close_actors,
        slice_cap_color=config.slice_cap_color,
    )
    scene.plotter.axes = config.plotter_axes
    return camera


def render_scene(
    scene: Scene,
    camera: dict | None,
    *,
    interactive: bool,
) -> None:
    """Render the scene (interactive window or offscreen)."""
    if camera is not None:
        scene.render(camera=camera, interactive=interactive)
    else:
        scene.render(interactive=interactive)
