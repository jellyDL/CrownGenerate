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
    p.add_argument('--vmax', type=float, default=.5)
    p.add_argument('--samples', type=int, default=600000)
    p.add_argument('--page-rows', type=int, default=6)
    p.add_argument('--view', choices=['occlusal', 'oblique'], default='occlusal')
    p.add_argument('--combined', action='store_true', help='Compatibility flag; five-column output is now the default')
    p.add_argument('--limit', type=int, default=None, help='Use first N folders in sorted order for a layout preview')
    p.add_argument('--wspace', type=float, default=.005,
                   help='Horizontal spacing between subplots (default: .005)')
    p.add_argument('--hspace', type=float, default=.035,
                   help='Vertical spacing between rows (default: .035)')
    a = p.parse_args()
    if a.vmax <= 0 or a.samples < 1 or a.page_rows < 1 or a.wspace < 0 or a.hspace < 0:
        p.error('vmax, samples and page-rows must be positive; wspace and hspace must be non-negative')
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
    norm = Normalize(0, a.vmax, clip=True)
    cmap = plt.get_cmap('viridis')
    rows, metadata = [], []

    labels = ['GT', 'Without TP', 'With TP', 'Without TP → GT\nDistance map', 'With TP → GT\nDistance map']

    def draw(items, name):
        # Reserve a separate colorbar column; attaching it only to the error
        # panels would shrink those panels relative to the three geometries.
        fig = plt.figure(figsize=(14.8, 2.7*len(items)+.4), layout=None)
        fig.subplots_adjust(left=.01, right=.995, bottom=.01, top=.93,
                            wspace=a.wspace, hspace=a.hspace)
        grid = fig.add_gridspec(len(items), 6, width_ratios=[1,1,1,1,1,.055],
                               wspace=a.wspace, hspace=a.hspace)
        axs = np.empty((len(items), len(labels)), dtype=object)
        for i, (case_id, images) in enumerate(items):
            for j, img in enumerate(images):
                ax = axs[i,j] = fig.add_subplot(grid[i,j])
                ax.imshow(img, extent=(-half,half,-half,half), interpolation='nearest')
                ax.set_aspect('equal', adjustable='box')
                ax.set_xticks([]); ax.set_yticks([])
                for spine in ax.spines.values():
                    spine.set_visible(False)
        for j,label in enumerate(labels):
            axs[0,j].set_title(label,fontsize=10,pad=10)
        bar_parent = fig.add_subplot(grid[:,5])
        bar_parent.set_axis_off()
        bar_fraction = min(.85, 2.8/(2.7*len(items)))
        cax = bar_parent.inset_axes([0,(1-bar_fraction)/2,.8,bar_fraction])
        fig.colorbar(ScalarMappable(norm=norm,cmap=cmap), cax=cax, extend='max',
                     label='Prediction-to-GT distance (mm)')
        # fig.savefig((name+'.png'), dpi=300, bbox_inches='tight')
        # PDF is reserved for the final all-case composition; intermediate
        # single-case and page renders are useful as PNG previews only.
        if name == 'comparison_all':
            fig.savefig('comparison_all.pdf', bbox_inches='tight')
        plt.close(fig)

    for k,case in enumerate(cases):
        meshes = [trimesh.load(f,force='mesh',process=True) for f in case['paths']]
        images, stats, geometries = [], [], []
        # Warp is optional; CPU proximity keeps the script usable in a plain
        # Python environment and the external Warp backend remains selectable
        # by changing this one option for high-throughput runs.
        opts = dict(backend='trimesh', allow_cpu_fallback=True, warp_cache={})
        for j,m in enumerate(meshes):
            points,normals,_ = _sample_surface(m,a.samples,2026+j)
            n = normals@case['axes']@rotation
            lighting = .6+.4*np.abs(n@np.array([.25,-.35,.9027735]))
            gray = np.clip(lighting[:,None]*[.72,.75,.78],0,1)
            local = (points-case['origin'])@case['axes']@rotation
            projected = _project_points(points, case['camera'], local)
            if case['camera'] is not None:
                projected[:, :2] *= half
            geometries.append(raster(projected,gray,half,size=500).astype(np.float32))
            if j == 0:
                colors = gray
            else:
                d = _closest_point_portable(meshes[0], points, **opts)[1]
                colors = cmap(norm(d))
                stats.append(dict(mesh=str(case['paths'][j]),mean_distance_mm=float(d.mean()),
                                  fraction_above_color_limit=float((d>a.vmax).mean())))
            local = (points-case['origin'])@case['axes']@rotation
            projected = _project_points(points, case['camera'], local)
            if case['camera'] is not None:
                projected[:, :2] *= half
            images.append(raster(projected,colors,half,size=500).astype(np.float32))
        images = geometries + images[1:]
        rows.append((case['id'],images))
        metadata.append(dict(case_id=case['id'],files=[str(f.resolve()) for f in case['paths']],
                             frame=case['frame'],camera_file=case['camera_file'],
                             distances=stats))
        draw([rows[-1]],case['id'])
        print(f'[{k+1}/{len(cases)}] {case["id"]}',flush=True)
        del meshes,opts
        gc.collect()
    for start in range(0,len(rows),a.page_rows):
        draw(rows[start:start+a.page_rows],f'comparison_page_{start//a.page_rows+1:02d}')
    draw(rows,'comparison_all')
    (out/'manifest.json').write_text(json.dumps(dict(cases=metadata,skipped=skipped,half_extent_mm=half,
        color_max_mm=a.vmax,surface_samples=a.samples,view=a.view,
        columns=[label.replace('\n',' ') for label in labels],layout='five_columns',dpi=300),indent=2))
    print('Saved:',out,flush=True)


if __name__ == '__main__':
    main()
