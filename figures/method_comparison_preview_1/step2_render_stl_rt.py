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

def _load_transform(path: Path) -> np.ndarray:
    data = json.loads(path.read_text())
    T = np.asarray(data['transform'], float)
    if T.shape != (4, 4):
        raise ValueError(f'transform in {path} must be 4x4')
    return T


def _render(stl: Path, T: np.ndarray, output: Path) -> None:
    mesh = pv.read(stl)
    pts = np.c_[np.asarray(mesh.points), np.ones(mesh.n_points)]
    mesh.points = (pts @ T.T)[:, :3]
    pl = pv.Plotter(off_screen=True, window_size=(900, 900))
    pl.set_background('#f4f7f4')
    # Neutral dental-stone gray with Phong highlights, matching the glossy
    # reference rendering while retaining visible surface relief.
    pl.add_mesh(mesh, color='#9a9a9a', smooth_shading=True, ambient=0.25,
                diffuse=0.68, specular=0.52, specular_power=35)
    pl.camera_position = 'iso'
    pl.camera.zoom(1.35)
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
        default=4.0,
        help='symmetric heatmap range in mm (default: -2 to 2)',
    )
    args=p.parse_args();
    if args.input_path.is_dir():
        folder=args.input_path
        gt_stl = folder / 'gt.stl'
        our_stl = folder / 'our.stl'
        gt_rt = folder / 'gt_rt.json'
        if gt_rt.is_file() and gt_stl.is_file() and our_stl.is_file():
            T = _load_transform(gt_rt)
            _render(gt_stl, T, folder / 'gt.png')
            _render(our_stl, T, folder / 'our.png')
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
    out=args.output or stl.with_name('our_diff.png' if args.gt else stl.stem+'_render.png')
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
    if scalars is None:
        pl.add_mesh(mesh,color='#c9a77d',smooth_shading=True,ambient=0.25,diffuse=0.75,specular=0.15)
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
    pl.camera.zoom(1.35)
    pl.show(screenshot=str(out),auto_close=True)
    print(out)
if __name__=='__main__': main()
