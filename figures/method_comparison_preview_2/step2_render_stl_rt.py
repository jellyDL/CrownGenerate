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

def _load_transform(path: Path) -> np.ndarray:
    data = json.loads(path.read_text())
    T = np.asarray(data['transform'], float)
    if T.shape != (4, 4):
        raise ValueError(f'transform in {path} must be 4x4')
    return T


def _render(stl: Path, T: np.ndarray, output: Path, jaw_paths=()) -> None:
    mesh = pv.read(stl)
    pts = np.c_[np.asarray(mesh.points), np.ones(mesh.n_points)]
    mesh.points = (pts @ T.T)[:, :3]
    pl = pv.Plotter(off_screen=True, window_size=(800, 600)) # h,w
    pl.set_background('#f4f7f4')
    for jaw_path in jaw_paths:
        jaw = pv.read(jaw_path)
        jaw_pts = np.c_[np.asarray(jaw.points), np.ones(jaw.n_points)]
        jaw.points = (jaw_pts @ T.T)[:, :3]
        pl.add_mesh(jaw, color='#a7a7a7', smooth_shading=True, opacity=0.72,
                    show_edges=False)
    # Neutral dental-stone gray with Phong highlights, matching the glossy
    # reference rendering while retaining visible surface relief.
    pl.add_mesh(mesh, color=GT_COLOR, smooth_shading=True, ambient=0.25,
                diffuse=0.68, specular=0.52, specular_power=35)
    pl.camera_position = 'iso'
    pl.camera.zoom(1.65)
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
        default=5.0,
        help='symmetric heatmap range in mm (default: -2 to 2)',
    )
    args=p.parse_args();
    jaw_paths = []
    if args.input_path.is_dir():
        folder=args.input_path
        gt_stl = folder / 'gt.stl'
        our_stl = folder / 'our.stl'
        # The all-mesh pose is the authoritative view: it was saved after
        # rotating the upper jaw, lower jaw, and crown as one rigid object.
        all_rt = folder / 'gt_all_rt.json'
        gt_rt = folder / 'gt_all_rt.json'
        rt_for_folder = all_rt if all_rt.is_file() else gt_rt
        if rt_for_folder.is_file() and gt_stl.is_file() and our_stl.is_file():
            T = _load_transform(rt_for_folder)
            jaw_paths = [folder / name for name in
                         ('upperjaw.ply', 'lowerjaw.ply', 'upperjaw.stl', 'lowerjaw.stl')
                         if (folder / name).is_file()]
            _render(gt_stl, T, folder / 'gt_all.png', jaw_paths)
            _render(our_stl, T, folder / 'our_all.png', jaw_paths)
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
        preferred = folder / 'gt_all_rt.json'
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
        scalars=cKDTree(np.asarray(gt.points)).query(np.asarray(mesh.points),k=1)[0]
        mesh['error_mm']=scalars
    pl=pv.Plotter(off_screen=True,window_size=(900,900))
    pl.set_background('#f4f7f4')
    for jaw_path in jaw_paths:
        jaw = pv.read(jaw_path)
        jaw_pts = np.c_[np.asarray(jaw.points), np.ones(jaw.n_points)]
        jaw.points = (jaw_pts @ T.T)[:, :3]
        pl.add_mesh(jaw, color='#a7a7a7', smooth_shading=True, opacity=0.72,
                    show_edges=False)
    if scalars is None:
        pl.add_mesh(mesh,color=GT_COLOR,smooth_shading=True,ambient=0.25,diffuse=0.75,specular=0.15)
    else:
        # Keep the colour scale fixed and symmetric so that renders are
        # directly comparable across samples.  The current error values are
        # non-negative distances, but the symmetric range is intentional.
        half_range=abs(args.clim)
        if half_range == 0:
            raise ValueError('--clim must be non-zero')
        pl.add_mesh(mesh,scalars='error_mm',cmap='turbo',clim=(-half_range,half_range),smooth_shading=True,show_scalar_bar=False)
    pl.add_axes(); 
    pl.camera_position='iso'; 
    pl.camera.zoom(1.65)
    pl.show(screenshot=str(out),auto_close=True)
    print(out)
if __name__=='__main__': main()
