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

import argparse, json, re
from pathlib import Path
import numpy as np
import pyvista as pv

def _load_transform(path: Path) -> np.ndarray:
    data = json.loads(path.read_text())
    T = np.asarray(data['transform'], float)
    if T.shape != (4, 4):
        raise ValueError(f'transform in {path} must be 4x4')
    return T


def _apply_transform(mesh: pv.DataSet, T: np.ndarray) -> pv.DataSet:
    mesh = mesh.copy()
    pts = np.c_[np.asarray(mesh.points), np.ones(mesh.n_points)]
    mesh.points = (pts @ T.T)[:, :3]
    return mesh


def _render_meshes(paths: list[Path], T: np.ndarray, output: Path,
                   colors: list[str], zoom: float = 1.35) -> None:
    pl = pv.Plotter(off_screen=True, window_size=(900, 900))
    pl.set_background('#f4f7f4')
    for path, color in zip(paths, colors):
        mesh = _apply_transform(pv.read(path), T)
        pl.add_mesh(mesh, color=color, smooth_shading=True, ambient=0.25,
                    diffuse=0.72, specular=0.58, specular_power=40)
    pl.add_axes()
    pl.camera_position = 'iso'
    pl.camera.zoom(zoom)
    pl.show(screenshot=str(output), auto_close=True)
    print(output)


def main():
    p=argparse.ArgumentParser()
    p.add_argument('input_path',type=Path,help='STL file or a folder containing an STL and its pose JSON')
    p.add_argument('-o','--output',type=Path,default=None)
    p.add_argument('--gt',type=Path,default=None,help='ground-truth STL for distance heatmap')
    p.add_argument('--jaw-zoom', type=float, default=2.5,
                   help='zoom for gt_jaw.png and our_jaw.png (default: 2.0; larger means closer)')
    p.add_argument(
        '--clim',
        type=float,
        default=4.0,
        help='symmetric heatmap range in mm (default: -2 to 2)',
    )
    args=p.parse_args();
    if not np.isfinite(args.jaw_zoom) or args.jaw_zoom <= 0:
        p.error('--jaw-zoom must be a positive finite number')
    if args.input_path.is_dir():
        folder=args.input_path
        gt_stl = folder / 'gt.stl'
        our_stl = folder / 'our.stl'
        gt_rt = folder / 'gt_rt.json'
        if not gt_rt.is_file():
            raise FileNotFoundError(f'gt_rt.json not found in {folder}')
        if not gt_stl.is_file() or not our_stl.is_file():
            raise FileNotFoundError(f'folder must contain gt.stl and our.stl: {folder}')
        payload = json.loads(gt_rt.read_text())
        T = np.asarray(payload['transform'], float)
        if T.shape != (4, 4):
            raise ValueError(f'transform in {gt_rt} must be 4x4')

        # Prefer the jaw recorded by step1.  For older JSON files, infer the
        # arch from the FDI number in the unique *-margin.xyz filename.
        jaw_source = payload.get('jaw_source')
        jaw = Path(jaw_source) if jaw_source else None
        if jaw is not None and not jaw.is_absolute():
            jaw = folder / jaw
        if jaw is None or not jaw.is_file():
            margins = sorted(folder.glob('*-margin.xyz'))
            if len(margins) != 1:
                raise ValueError(f'expected one *-margin.xyz in {folder}, found {len(margins)}')
            match = re.fullmatch(r'([1-8][1-8])-margin\.xyz', margins[0].name)
            if match is None:
                raise ValueError(f'invalid FDI margin filename: {margins[0].name}')
            fdi = int(match.group(1))
            arch = 'upperjaw' if fdi // 10 in (1, 2, 5, 6) else 'lowerjaw'
            candidates = [folder / f'{arch}{suffix}' for suffix in ('.ply', '.stl')]
            jaw = next((path for path in candidates if path.is_file()), None)
        if jaw is None or not jaw.is_file():
            raise FileNotFoundError(f'corresponding upper/lower jaw mesh not found in {folder}')

        # Four consistent views: GT with/without the arch, and prediction
        # with/without the same arch.  All meshes use the pose from gt_rt.json.
        _render_meshes([gt_stl, jaw], T, folder / 'gt_jaw.png', ['#c79258', '#9a9a9a'], zoom=args.jaw_zoom)
        _render_meshes([gt_stl], T, folder / 'gt_only.png', ['#c79258'])
        _render_meshes([our_stl, jaw], T, folder / 'our_jaw.png', ['#d4d4d4', '#9a9a9a'], zoom=args.jaw_zoom)
        _render_meshes([our_stl], T, folder / 'our_only.png', ['#d4d4d4'])
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
