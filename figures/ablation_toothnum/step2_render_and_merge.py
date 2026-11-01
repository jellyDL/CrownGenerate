#!/usr/bin/env python3
"""Render each child folder's gt.stl / ablation.stl / our.stl.

Run with the project's trellis2 Python; no graphical desktop is required.
Distances use original coordinates (assumed mm), with no ICP alignment.
Five columns: GT, Without TP geometry, With TP geometry, then their two
prediction-to-GT point/triangle distance maps. Geometry panels share shading;
all five panels share the same camera and physical scale.
"""
from pathlib import Path
import argparse
import gc
import json
import sys

ROOT = Path(__file__).resolve().parents[2]
for candidate in (ROOT, Path('/Users/jelly/Desktop/crown_generate_codex')):
    if candidate.is_dir() and str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

# Edit rows here as: (case folder name, color minimum in mm, maximum).
# Only these configured cases are rendered, in this order.
ROW_CONFIG = [
    ('00a2ecc9-4ae7-593a-9751-6247fcab4438', 0.0, 0.48),
    # ('020293a4-cf3d-54e2-8dc3-c581226e32f0', 0.0, 0.6),
    ('00bac203-b5f6-57ef-af2b-d7a0675ce1ef', 0.0, 0.5),
    ('00f91d4b-b911-5c65-9e33-51735ba0b4cd', 0.0, 0.35),
    ('017a7aea-8548-5593-b6e9-abe8e4cdaa03', 0.0, 0.68),
]
import numpy as np
import trimesh
from matplotlib.colors import Normalize
from matplotlib.cm import ScalarMappable

try:
    from scripts.ablation2.report_plot_style import plt
    from scripts.ablation2.plot_matched_surfaces import raster
except ModuleNotFoundError:
    # The plotting helpers live in a separate research checkout in the
    # original environment. Keep this script runnable from this repository.
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    def raster(points, colors, half, size=500):
        """Orthographically rasterize colored points with a simple z-buffer."""
        points = np.asarray(points)
        colors = np.asarray(colors)
        if points.ndim != 2 or points.shape[1] < 3:
            raise ValueError('points must have shape (N, 3)')
        if colors.ndim == 1:
            colors = np.repeat(colors[:, None], 3, axis=1)
        image = np.ones((int(size), int(size), 3), dtype=np.float32)
        if not len(points) or half <= 0:
            return image
        xy = np.rint((points[:, :2] + half) / (2 * half) * (size - 1)).astype(int)
        valid = ((xy >= 0) & (xy < size)).all(axis=1)
        xy, depth, colors = xy[valid], points[valid, 2], colors[valid, :3]
        # Sorting puts the largest depth at the visible pixel.
        order = np.argsort(depth)
        image[xy[order, 1], xy[order, 0]] = np.clip(colors[order], 0, 1)
        return image


def raster_triangles(vertices, faces, colors, half, size=500):
    """Rasterize STL triangles with barycentric coverage and a depth buffer."""
    vertices = np.asarray(vertices, dtype=float)
    faces = np.asarray(faces, dtype=np.int64)
    colors = np.asarray(colors, dtype=float)
    image = np.ones((int(size), int(size), 3), dtype=np.float32)
    depth_buffer = np.full((int(size), int(size)), -np.inf, dtype=float)
    if half <= 0 or len(faces) == 0:
        return image
    if colors.ndim == 1:
        colors = np.repeat(colors[:, None], 3, axis=1)
    if len(colors) != len(faces):
        raise ValueError('colors must contain one RGB value per triangle')

    xy = (vertices[:, :2] + half) / (2.0 * half) * (size - 1)
    triangles = xy[faces]
    depths = vertices[faces, 2]
    valid = np.isfinite(triangles).all(axis=(1, 2)) & np.isfinite(depths).all(axis=1)
    valid &= np.abs(
        (triangles[:, 1, 0] - triangles[:, 0, 0]) *
        (triangles[:, 2, 1] - triangles[:, 0, 1]) -
        (triangles[:, 1, 1] - triangles[:, 0, 1]) *
        (triangles[:, 2, 0] - triangles[:, 0, 0])
    ) > 1e-8

    for face_index in np.flatnonzero(valid):
        tri = triangles[face_index]
        z = depths[face_index]
        min_x = max(0, int(np.floor(tri[:, 0].min())))
        max_x = min(size - 1, int(np.ceil(tri[:, 0].max())))
        min_y = max(0, int(np.floor(tri[:, 1].min())))
        max_y = min(size - 1, int(np.ceil(tri[:, 1].max())))
        if min_x > max_x or min_y > max_y:
            continue
        grid_x, grid_y = np.meshgrid(
            np.arange(min_x, max_x + 1, dtype=float),
            np.arange(min_y, max_y + 1, dtype=float),
        )
        x0, y0 = tri[0]
        x1, y1 = tri[1]
        x2, y2 = tri[2]
        denominator = (y1 - y2) * (x0 - x2) + (x2 - x1) * (y0 - y2)
        w0 = ((y1 - y2) * (grid_x - x2) + (x2 - x1) * (grid_y - y2)) / denominator
        w1 = ((y2 - y0) * (grid_x - x2) + (x0 - x2) * (grid_y - y2)) / denominator
        w2 = 1.0 - w0 - w1
        inside = (w0 >= -1e-6) & (w1 >= -1e-6) & (w2 >= -1e-6)
        if not inside.any():
            continue
        local_depth = w0 * z[0] + w1 * z[1] + w2 * z[2]
        target_depth = depth_buffer[min_y:max_y + 1, min_x:max_x + 1]
        update = inside & (local_depth > target_depth)
        if update.any():
            target_depth[update] = local_depth[update]
            target_image = image[min_y:max_y + 1, min_x:max_x + 1]
            target_image[update] = np.clip(colors[face_index, :3], 0, 1)
    return image

try:
    from pixal3d.evaluation.metrics import _sample_surface, _closest_point_chunked
except ModuleNotFoundError:
    def _sample_surface(mesh, count, seed):
        state = np.random.get_state()
        np.random.seed(seed)
        try:
            points, face_ids = trimesh.sample.sample_surface(mesh, count)
        finally:
            np.random.set_state(state)
        return points, np.asarray(mesh.face_normals)[face_ids], face_ids

    def _closest_point_chunked(mesh, points, chunk_size=5000, **_kwargs):
        closest_parts, distance_parts, triangle_parts = [], [], []
        for start in range(0, len(points), int(chunk_size)):
            closest, distance, triangles = trimesh.proximity.closest_point(
                mesh, points[start:start + int(chunk_size)])
            closest_parts.append(closest)
            distance_parts.append(distance)
            triangle_parts.append(triangles)
        return (np.concatenate(closest_parts), np.concatenate(distance_parts),
                np.concatenate(triangle_parts))


def _closest_point_portable(mesh, points, **kwargs):
    """Use the project metric, with a vertex-tree fallback when rtree is absent."""
    try:
        return _closest_point_chunked(mesh, points, **kwargs)
    except ModuleNotFoundError as exc:
        if exc.name != 'rtree':
            raise
        from scipy.spatial import cKDTree
        vertices = np.asarray(mesh.vertices, dtype=np.float64)
        distance, indices = cKDTree(vertices).query(np.asarray(points), workers=-1)
        return vertices[indices], distance, np.zeros(len(indices), dtype=np.int64)


def _load_camera(path):
    """Load and validate a VTK-style camera description from JSON."""
    if not path.is_file():
        return None
    try:
        camera = json.loads(path.read_text()).get('camera', {})
        position = np.asarray(camera['position'], dtype=float)
        focal = np.asarray(camera['focal_point'], dtype=float)
        viewup = np.asarray(camera['viewup'], dtype=float)
        if position.shape != (3,) or focal.shape != (3,) or viewup.shape != (3,):
            raise ValueError('camera vectors must have length 3')
        forward = focal - position
        forward /= np.linalg.norm(forward)
        viewup /= np.linalg.norm(viewup)
        right = np.cross(forward, viewup)
        right /= np.linalg.norm(right)
        up = np.cross(right, forward)
        up /= np.linalg.norm(up)
        return dict(
            position=position,
            focal_point=focal,
            right=right,
            up=up,
            forward=forward,
            parallel_projection=bool(camera.get('parallel_projection', False)),
            parallel_scale=float(camera.get('parallel_scale', 1.0)),
            view_angle=float(camera.get('view_angle', 30.0)),
        )
    except (KeyError, TypeError, ValueError, ZeroDivisionError) as exc:
        print(f'Ignoring invalid camera file {path}: {exc}', flush=True)
        return None


def _project_points(points, camera, fallback_points):
    """Project world-space points into the camera image plane.

    The returned third coordinate is negative camera depth so the rasterizer's
    largest-depth-wins z-buffer keeps the surface nearest to the camera.
    """
    if camera is None:
        return fallback_points
    delta = np.asarray(points, dtype=float) - camera['position']
    depth = delta @ camera['forward']
    x = delta @ camera['right']
    y = delta @ camera['up']
    if camera['parallel_projection']:
        # parallel_scale is the VTK viewport height in world units
        scale = max(camera['parallel_scale'], 1e-9) / 2.0
        x, y = x / scale, y / scale
    else:
        # Perspective projection, expressed in units at the focal plane.
        tan_half_fov = max(np.tan(np.deg2rad(camera['view_angle']) / 2.0), 1e-9)
        safe_depth = np.where(np.abs(depth) > 1e-9, depth, np.nan)
        # Normalize by the perspective frustum half-width at each depth.
        # Without this factor the crowns occupy only a small central patch.
        x, y = x / (safe_depth * tan_half_fov), y / (safe_depth * tan_half_fov)
        x = np.nan_to_num(x, nan=0.0, posinf=0.0, neginf=0.0)
        y = np.nan_to_num(y, nan=0.0, posinf=0.0, neginf=0.0)
    return np.column_stack((x, y, -depth))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', type=Path, default=Path(__file__).resolve().parent)
    p.add_argument('--vmin', type=float, default=0.0,
                   help='Lower bound of the distance color scale in mm (default: 0)')
    p.add_argument('--vmax', type=float, default=.5,
                   help='Upper bound of the distance color scale in mm (default: 0.5)')
    p.add_argument('--clim', nargs=2, type=float, metavar=('MIN', 'MAX'),
                   help='Set both distance color scale bounds in mm; overrides --vmin/--vmax')
    p.add_argument('--samples', type=int, default=600000)
    p.add_argument('--fast', action='store_true',
                   help='Fast preview: rasterize triangle centers and use at most 30000 faces per distance map')
    p.add_argument('--page-rows', type=int, default=6)
    p.add_argument('--view', choices=['occlusal', 'oblique'], default='occlusal')
    p.add_argument('--combined', action='store_true', help='Compatibility flag; five-column output is now the default')
    p.add_argument('--limit', type=int, default=None, help='Use first N folders in sorted order for a layout preview')
    p.add_argument('--wspace', type=float, default=.005,
                   help='Horizontal spacing between subplots (default: .005)')
    p.add_argument('--first-column-gap', '--first-col-gap', dest='first_column_gap', type=float, default=.15,
                   help='Extra gap after the first column, relative to one panel width (default: .03)')
    p.add_argument('--hspace', type=float, default=.035,
                   help='Vertical spacing between rows (default: .035)')
    p.add_argument('--font-size', '--label-font-size', dest='label_font_size', type=int, default=90,
                   help='Top label font size in pixels (default: 80)')
    p.add_argument('--colorbar-font-size', '--colorbar-fontsize', dest='colorbar_font_size',
                   type=int, default=90, help='Colorbar font size in pixels (default: 80)')
    p.add_argument('--colorbar-label-gap', '--colorbar-unit-gap', dest='colorbar_label_gap',
                   type=int, default=30, help='Gap between colorbar and its label in pixels (default: 30)')
    p.add_argument('--colorbar-length', type=int, default=1350,
                   help='Colorbar length in pixels (default: 1200)')
    p.add_argument('--colorbar-thickness', type=int, default=60,
                   help='Colorbar thickness in pixels (default: 40)')
    p.add_argument('--colorbar-gap', type=int, default=280,
                   help='Fallback gap from the right edge in pixels (default: 100)')
    p.add_argument('--colorbar-position', nargs=2, type=int, default=(4350,1860), metavar=('X', 'Y'),
                   help='Colorbar top-left position in pixels; default uses the right edge')
    a = p.parse_args()
    if a.clim is not None:
        a.vmin, a.vmax = a.clim
    if (not np.isfinite(a.vmin) or not np.isfinite(a.vmax) or a.vmin < 0 or a.vmin >= a.vmax
            or a.samples < 1 or a.page_rows < 1 or a.wspace < 0 or a.hspace < 0
            or a.first_column_gap < 0
            or a.label_font_size <= 0 or a.colorbar_font_size <= 0 or a.colorbar_label_gap < 0
            or a.colorbar_length <= 0
            or a.colorbar_thickness <= 0 or a.colorbar_gap < 0
            or (a.colorbar_position is not None and min(a.colorbar_position) < 0)):
        p.error('invalid layout or colorbar parameters')
    # Always write generated artifacts beside this script.
    out = Path(__file__).resolve().parent
    cases = []
    skipped = []
    cache_root = Path('~/projects/crown_generate_codex/outputs/detail64_surface_dataset_v3/data/cache').expanduser()
    for folder in sorted(a.root.iterdir()):
        if not folder.is_dir() or folder.name == 'figures':
            continue
        paths = [folder/n for n in ['gt.stl', 'ablation.stl', 'our.stl']]
        if not paths[1].is_file() and (folder/'ablations.stl').is_file():
            paths[1] = folder/'ablations.stl'
            print(f'Using ablations.stl alias: {folder.name}', flush=True)
        if not all(f.is_file() for f in paths):
            skipped.append(str(folder)); continue
        cache = cache_root/(folder.name+'.npz')
        if cache.exists():
            with np.load(cache) as z:
                origin, axes = z['origin'].copy(), z['axes'].copy()
            frame = 'cached input frame'
        else:
            gt = trimesh.load(paths[0], force='mesh', process=True)
            origin, axes = gt.bounds.mean(axis=0), np.eye(3)
            frame = 'world axes, GT bounding-box center (no registration)'
        camera_path = folder/'occlusion_view.json'
        cases.append(dict(id=folder.name, paths=paths, origin=origin, axes=axes,
                          frame=frame, camera=_load_camera(camera_path),
                          camera_file=str(camera_path) if camera_path.is_file() else None))
    if a.limit is not None:
        if a.limit < 1:
            p.error('limit must be positive')
        cases = cases[:a.limit]
    case_ids = {case['id'] for case in cases}
    config_ids = [entry[0] for entry in ROW_CONFIG]
    if len(set(config_ids)) != len(config_ids):
        p.error('ROW_CONFIG must contain unique existing case names')
    if a.limit is None and not set(config_ids) <= case_ids:
        p.error('ROW_CONFIG must contain unique existing case names')
    active_config = [entry for entry in ROW_CONFIG if entry[0] in case_ids]
    config_ids = [entry[0] for entry in active_config]
    ordered = {case['id']: case for case in cases}
    cases = [ordered[case_id] for case_id in config_ids]
    row_clims = {case_id: (float(vmin), float(vmax))
                 for case_id, vmin, vmax in active_config}
    default_clim = (a.vmin, a.vmax)
    for case in cases:
        case['clim'] = row_clims.get(case['id'], default_clim)
        if (not all(np.isfinite(value) for value in case['clim'])
                or case['clim'][0] < 0 or case['clim'][0] >= case['clim'][1]):
            p.error(f'invalid color scale for case {case["id"]}: expected 0 <= MIN < MAX')
    if not cases:
        p.error('No folders contain all three required STL files')
    rotation = np.eye(3) if a.view == 'occlusal' else np.array([[1,0,0],[0,2**-.5,-2**-.5],[0,2**-.5,2**-.5]])
    half = 0.
    for case in cases:
        for path in case['paths']:
            m = trimesh.load(path, force='mesh', process=True)
            local = (m.vertices-case['origin'])@case['axes']@rotation
            half = max(half, float(np.abs(local[:,:2]).max()))
    half *= 1.12
    cmap = plt.get_cmap('viridis')
    norms = {case['id']: Normalize(*case['clim'], clip=True) for case in cases}
    rows, metadata = [], []

    labels = ['GT', 'w/o TP', 'Dist. to GT\n(w/o TP)',
              'w/ TP', 'Dist. to GT\n(w/ TP)']

    def draw(items, name):
        # Reserve a separate colorbar column; attaching it only to the error
        # panels would shrink those panels relative to the three geometries.
        fig = plt.figure(figsize=(14.8, 2.7*len(items)+.4), layout=None)
        fig.subplots_adjust(left=.01, right=.995, bottom=.01, top=.93,
                            wspace=a.wspace, hspace=a.hspace)
        # Column 1, a dedicated spacer, columns 2-5, then the colorbar cell.
        grid = fig.add_gridspec(len(items), 7,
                               width_ratios=[1, max(a.first_column_gap, 1e-6), 1,1,1,1,.055],
                               wspace=a.wspace, hspace=a.hspace)
        panel_columns = (0, 2, 3, 4, 5)
        axs = np.empty((len(items), len(labels)), dtype=object)
        for i, (case_id, images) in enumerate(items):
            for j, img in enumerate(images):
                ax = axs[i,j] = fig.add_subplot(grid[i,panel_columns[j]])
                ax.imshow(img, extent=(-half,half,-half,half), interpolation='nearest')
                ax.set_aspect('equal', adjustable='box')
                ax.set_xticks([]); ax.set_yticks([])
                for spine in ax.spines.values():
                    spine.set_visible(False)
        for j,label in enumerate(labels):
            label_font_size_pt = a.label_font_size * 72.0 / 300.0
            axs[0,j].set_title(label, fontsize=label_font_size_pt, pad=10)
        if name == 'ablation_toothnum':
            # Match the pixel-based colorbar controls used by
            # ablation_occlusion/step3_merge_imgs.py. Intermediate renders do
            # not need a colorbar and may be shorter than the requested one.
                dpi = 300.
                figure_width_px = fig.get_figwidth() * dpi
                figure_height_px = fig.get_figheight() * dpi
                bar_length = min(float(a.colorbar_length), figure_height_px - 2 * a.colorbar_gap)
                if bar_length <= 1:
                    p.error('colorbar-length is too large for the current figure height')
                if a.colorbar_position is None:
                    bar_x = figure_width_px - a.colorbar_gap - a.colorbar_thickness
                    bar_top = a.colorbar_gap
                else:
                    bar_x, bar_top = a.colorbar_position
                bar_y = figure_height_px - bar_top - bar_length
                if bar_x < 0 or bar_y < 0 or bar_x + a.colorbar_thickness > figure_width_px:
                    p.error('colorbar-position or colorbar dimensions exceed the figure bounds')
                cax = fig.add_axes([bar_x / figure_width_px, bar_y / figure_height_px,
                                    a.colorbar_thickness / figure_width_px,
                                    bar_length / figure_height_px])
                display_norm = Normalize(
                    norms[items[0][0]].vmin,
                    max(float(norms[items[0][0]].vmax), 0.5),
                    clip=True,
                )
                colorbar = fig.colorbar(ScalarMappable(norm=display_norm, cmap=cmap), cax=cax)
                colorbar.set_ticks(np.linspace(display_norm.vmin, display_norm.vmax, 6))
                font_size_pt = a.colorbar_font_size * 72.0 / dpi
                label_gap_pt = a.colorbar_label_gap * 72.0 / dpi
                colorbar.set_label('Prediction-to-GT (mm)', fontsize=font_size_pt,
                                   labelpad=label_gap_pt)
                colorbar.ax.tick_params(labelsize=font_size_pt)
        # Keep PNG previews for every case and page; only the final composition
        # receives a PDF export.
        fig.savefig(out / f'{name}.png', dpi=300, bbox_inches='tight')
        # PDF is reserved for the final all-case composition; intermediate
        # single-case and page renders are useful as PNG previews only.
        if name == 'ablation_toothnum':
            fig.savefig(out / 'ablation_toothnum.pdf', bbox_inches='tight')
        plt.close(fig)

    for k,case in enumerate(cases):
        meshes = [trimesh.load(f,force='mesh',process=True) for f in case['paths']]
        images, stats, geometries = [], [], []
        # Warp is optional; CPU proximity keeps the script usable in a plain
        # Python environment and the external Warp backend remains selectable
        # by changing this one option for high-throughput runs.
        opts = dict(backend='trimesh', allow_cpu_fallback=True, warp_cache={})
        for j,m in enumerate(meshes):
            local_vertices = (m.vertices-case['origin'])@case['axes']@rotation
            projected_vertices = _project_points(m.vertices, case['camera'], local_vertices)
            if case['camera'] is not None:
                projected_vertices[:, :2] *= half
            face_normals = m.face_normals@case['axes']@rotation
            lighting = .6+.4*np.abs(face_normals@np.array([.25,-.35,.9027735]))
            gray_faces = np.clip(lighting[:,None]*[.72,.75,.78],0,1)
            if a.fast:
                centers = projected_vertices[m.faces].mean(axis=1)
                geometry_image = raster(centers, gray_faces, half, size=500).astype(np.float32)
            else:
                geometry_image = raster_triangles(
                    projected_vertices, m.faces, gray_faces, half, size=500).astype(np.float32)
            geometries.append(geometry_image)
            if j == 0:
                images.append(geometry_image)
            else:
                face_centers = np.asarray(m.triangles_center)
                face_indices = np.arange(len(face_centers), dtype=np.int64)
                if a.fast and len(face_centers) > 500000:
                    face_indices = np.linspace(0, len(face_centers) - 1, 500000, dtype=np.int64)
                    face_centers = face_centers[face_indices]
                d = _closest_point_portable(meshes[0], face_centers, **opts)[1]
                colors = cmap(norms[case['id']](d))
                stats.append(dict(mesh=str(case['paths'][j]),mean_distance_mm=float(d.mean()),
                                  fraction_above_color_limit=float((d > case['clim'][1]).mean())))
                if a.fast:
                    images.append(raster(projected_vertices[m.faces].mean(axis=1)[face_indices], colors,
                                         half, size=500).astype(np.float32))
                else:
                    images.append(raster_triangles(
                        projected_vertices, m.faces, colors, half, size=500).astype(np.float32))
        # Keep each method's geometry next to its prediction-to-GT map.
        images = [geometries[0], geometries[1], images[1],
                  geometries[2], images[2]]
        rows.append((case['id'],images))
        metadata.append(dict(case_id=case['id'], color_min_mm=case['clim'][0],
                             color_max_mm=case['clim'][1], files=[str(f.resolve()) for f in case['paths']],
                             frame=case['frame'],camera_file=case['camera_file'],
                             distances=stats))
        draw([rows[-1]],case['id'])
        print(f'[{k+1}/{len(cases)}] {case["id"]}',flush=True)
        del meshes,opts
        gc.collect()
    for start in range(0,len(rows),a.page_rows):
        draw(rows[start:start+a.page_rows],f'comparison_page_{start//a.page_rows+1:02d}')
    draw(rows,'ablation_toothnum')
    (out/'manifest.json').write_text(json.dumps(dict(cases=metadata,skipped=skipped,half_extent_mm=half,
        color_min_mm=a.vmin,color_max_mm=a.vmax,surface_samples=a.samples,view=a.view,
        columns=[label.replace('\n',' ') for label in labels],layout='five_columns',dpi=300),indent=2))
    print('Saved:',out,flush=True)


if __name__ == '__main__':
    main()
