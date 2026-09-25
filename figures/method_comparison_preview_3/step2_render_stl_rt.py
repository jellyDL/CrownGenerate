#!/usr/bin/env python3
from __future__ import annotations
"""Render an STL after applying the rigid transform stored in an rt JSON."""

"""
Example usage:
python step2_render_stl_rt.py \
    26-preparation.stl \
    --gt gt.stl \
    --output heatmap.png
"""  

import argparse, json
from pathlib import Path
import numpy as np
import pyvista as pv

# GT_COLOR = '#9a9a9a'
GT_COLOR = '#d4d4d4'
WINDOW_SIZE = (600, 800)

def _load_transform(path: Path) -> np.ndarray:
    data = json.loads(path.read_text())
    T = np.asarray(data['transform'], float)
    if T.shape != (4, 4):
        raise ValueError(f'transform in {path} must be 4x4')
    return T


def _render(stl: Path, T: np.ndarray, output: Path, jaw_paths=(), camera_data=None,
            primary_color=(199, 146, 88), primary_is_jaw=False,
            reference_stl=None, clim=5.0) -> None:
    primary = pv.read(stl)
    pts = np.c_[np.asarray(primary.points), np.ones(primary.n_points)]
    primary.points = (pts @ T.T)[:, :3]
    primary['display_rgb'] = np.tile(
        (167, 167, 167) if primary_is_jaw else primary_color,
        (primary.n_points, 1),
    ).astype(np.uint8)
    if reference_stl is not None:
        from scipy.spatial import cKDTree
        reference = pv.read(reference_stl)
        ref_pts = np.c_[np.asarray(reference.points), np.ones(reference.n_points)]
        reference.points = (ref_pts @ T.T)[:, :3]
        primary['error_mm'] = cKDTree(np.asarray(reference.points)).query(
            np.asarray(primary.points), k=1
        )[0]
    parts = []
    for jaw_path in jaw_paths:
        jaw = pv.read(jaw_path)
        jaw_pts = np.c_[np.asarray(jaw.points), np.ones(jaw.n_points)]
        jaw.points = (jaw_pts @ T.T)[:, :3]
        jaw['display_rgb'] = np.tile([167, 167, 167], (jaw.n_points, 1)).astype(np.uint8)
        parts.append(jaw)
    parts.append(primary)
    mesh = pv.merge(parts, merge_points=False)
    # Match the interactive editor's viewport exactly.
    pl = pv.Plotter(off_screen=True, window_size=WINDOW_SIZE)
    pl.set_background('#f4f7f4')
    if reference_stl is None:
        pl.add_mesh(mesh, scalars='display_rgb', rgb=True,
                    smooth_shading=True, show_edges=False)
    else:
        # Keep the jaw gray while coloring only the crown by the GT distance,
        # matching the existing our_diff.png visualization.
        for jaw in parts[:-1]:
            pl.add_mesh(jaw, scalars='display_rgb', rgb=True,
                        smooth_shading=True, show_edges=False)
        pl.add_mesh(primary, scalars='error_mm', cmap='turbo',
                    clim=(-abs(clim), abs(clim)), smooth_shading=True,
                    show_scalar_bar=False)
    if camera_data:
        pl.camera.position = camera_data['position']
        pl.camera.focal_point = camera_data['focal_point']
        pl.camera.up = camera_data['viewup']
        pl.camera.parallel_scale = camera_data['parallel_scale']
        pl.camera.parallel_projection = camera_data.get('parallel_projection', False)
        if 'view_angle' in camera_data:
            pl.camera.view_angle = camera_data['view_angle']
        if 'clipping_range' in camera_data:
            pl.camera.clipping_range = camera_data['clipping_range']
    pl.show(screenshot=str(output), auto_close=True)
    print(output)


def main():
    p=argparse.ArgumentParser()
    p.add_argument('input_path',type=Path,help='STL file or a folder containing an STL and its pose JSON')
    p.add_argument('-o','--output',type=Path,default=None)
    p.add_argument('--gt',type=Path,default=None,help='ground-truth STL for distance heatmap')
    p.add_argument(
        '--clim',
        type=float,
        default=1.0,
        help='symmetric heatmap range in mm (default: -2 to 2)',
    )
    args=p.parse_args();
    if args.clim == 0:
        p.error('--clim must be non-zero')
    jaw_paths = []
    if args.input_path.is_dir():
        folder=args.input_path
        gt_stl = folder / 'gt.stl'
        our_stl = folder / 'our.stl'
        sample1_stl = folder / 'sample1_match.stl'
        sample2_stl = folder / 'sample2_match.stl'
        sample3_stl = folder / 'sample3_match.stl'
        rt_for_folder = folder / 'gt_singlejaw_rt.json'
        if not rt_for_folder.is_file():
            raise FileNotFoundError(f'missing required pose JSON: {rt_for_folder}')
        if not gt_stl.is_file() or not our_stl.is_file() or not sample1_stl.is_file():
            raise FileNotFoundError(f'{folder} must contain gt.stl, our.stl, and sample1_match.stl')
        T = _load_transform(rt_for_folder)
        pose_data = json.loads(rt_for_folder.read_text())
        camera_data = pose_data.get('camera')
        candidates = [folder / name for name in
                      ('upperjaw.ply', 'lowerjaw.ply', 'upperjaw.stl', 'lowerjaw.stl')
                      if (folder / name).is_file()]
        if not candidates:
            raise FileNotFoundError(f'no upper/lower jaw mesh found in {folder}')
        # Pick the jaw whose bounding box is nearest to the crown centroid.
        crown_center = np.asarray(pv.read(gt_stl).points).mean(axis=0)
        def bbox_distance(path: Path) -> float:
            points = np.asarray(pv.read(path).points)
            lower, upper = points.min(axis=0), points.max(axis=0)
            delta = np.maximum(np.maximum(lower - crown_center, 0), crown_center - upper)
            return float(np.linalg.norm(delta))
        jaw_path = min(candidates, key=bbox_distance)
        jaw_paths = [jaw_path]
        # All three views use the same gt_singlejaw pose and the same selected
        # single-jaw mesh for directly comparable framing.
        _render(jaw_path, T, folder / 'singlejaw.png', camera_data=camera_data,
                primary_is_jaw=True)
        # Match the ground-truth crown colour used by the existing gt.png
        # renderer (#d4d4d4); keep the jaw colour unchanged.
        _render(gt_stl, T, folder / 'gt_singlejaw.png', jaw_paths, camera_data,
                primary_color=(212, 212, 212))
        _render(our_stl, T, folder / 'our_singlejaw.png', jaw_paths, camera_data,
                reference_stl=gt_stl, clim=abs(args.clim))
        _render(sample1_stl, T, folder / 'sample1_match_singlejaw.png', jaw_paths, camera_data,
                reference_stl=gt_stl, clim=abs(args.clim))
        _render(sample2_stl, T, folder / 'sample2_match_singlejaw.png', jaw_paths, camera_data,
                reference_stl=gt_stl, clim=abs(args.clim))
        _render(sample3_stl, T, folder / 'sample3_match_singlejaw.png', jaw_paths, camera_data,
                reference_stl=gt_stl, clim=abs(args.clim))
        return
        json_files=[]
        for candidate in sorted(folder.glob('*.json')):
            try:
                payload=json.loads(candidate.read_text())
            except (OSError, json.JSONDecodeError):
                continue
            if isinstance(payload, dict) and 'transform' in payload:
                json_files.append((candidate, payload))
        if not json_files:
            raise FileNotFoundError(f'no pose JSON containing transform found in {folder}')
        preferred = folder / 'gt_singlejaw_rt.json'
        if rt_for_folder.is_file():
            rt_json = rt_for_folder
            data = json.loads(rt_json.read_text())
            # The difference render compares the transformed prediction to
            # the transformed ground truth; the all-mesh pose is shared by
            # both meshes and by the jaw reference meshes.
            stl = our_stl
        else:
            rt_json, data = json_files[0]
            source = data.get('source')
            stl = Path(source) if source else folder / rt_json.name.removesuffix('_rt.json')
            if source and not stl.is_absolute():
                stl = folder / stl
        if not stl.exists():
            stem = rt_json.stem.removesuffix('_rt')
            matches = sorted(folder.glob(stem + '.stl')) or sorted(folder.glob('*.stl'))
            matches = [path for path in matches if path.name.lower() != 'gt.stl']
            if not matches:
                raise FileNotFoundError(f'no STL found in {folder}')
            stl = matches[0]
        default_gt = folder / 'gt.stl'
    else:
        stl = args.input_path
        rt_json=stl.with_name(stl.stem+'_rt.json')
        data = json.loads(rt_json.read_text())
        default_gt = stl.with_name('gt.stl')
    args.stl = stl
    if args.gt is None and default_gt.exists():
        args.gt = default_gt
    out=args.output or stl.with_name('our_diff_all.png' if args.gt else stl.stem+'_render.png')
    T=np.asarray(data['transform'],float)
    if T.shape != (4,4): 
        raise ValueError('transform must be 4x4')
    mesh=pv.read(args.stl); 
    pts=np.c_[np.asarray(mesh.points),np.ones(mesh.n_points)]
    mesh.points=(pts@T.T)[:,:3]
    scalars=None
    if args.gt:
        from scipy.spatial import cKDTree
        gt=pv.read(args.gt)
        # Compare in the same transformed coordinate system.  This is
        # essential when T is the saved whole-mesh gt_all pose.
        gt_pts=np.c_[np.asarray(gt.points),np.ones(gt.n_points)]
        gt.points=(gt_pts@T.T)[:,:3]
        scalars=cKDTree(np.asarray(gt.points)).query(np.asarray(mesh.points),k=1)[0]
        mesh['error_mm']=scalars
    pl=pv.Plotter(off_screen=True,window_size=WINDOW_SIZE)
    pl.set_background('#f4f7f4')
    for jaw_path in jaw_paths:
        jaw = pv.read(jaw_path)
        jaw_pts = np.c_[np.asarray(jaw.points), np.ones(jaw.n_points)]
        jaw.points = (jaw_pts @ T.T)[:, :3]
        pl.add_mesh(jaw, color='#a7a7a7', smooth_shading=True, opacity=1.0,
                    show_edges=False, backface_culling=True)
    if scalars is None:
        pl.add_mesh(mesh,color=GT_COLOR,smooth_shading=True,ambient=0.25,diffuse=0.75,specular=0.15,
                    opacity=1.0, backface_culling=True)
    else:
        # Keep the colour scale fixed and symmetric so that renders are
        # directly comparable across samples.  The current error values are
        # non-negative distances, but the symmetric range is intentional.
        half_range=abs(args.clim)
        if half_range == 0:
            raise ValueError('--clim must be non-zero')
        pl.add_mesh(mesh,scalars='error_mm',cmap='turbo',clim=(-half_range,half_range),
                    smooth_shading=True,show_scalar_bar=False,opacity=1.0,
                    backface_culling=True)
    # Keep the comparison image clean; the coordinate triad is not needed in
    # ``our_diff_all.png`` and otherwise appears in the lower-left corner.
    pl.show(screenshot=str(out),auto_close=True)
    print(out)
if __name__=='__main__': main()
