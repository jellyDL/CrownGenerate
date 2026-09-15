#!/usr/bin/env python3
from __future__ import annotations
"""Render an STL after applying the rigid transform stored in an rt JSON."""

"""
Example usage:
python step2_render_stl_rt.py \
    26-preparation.stl \
    26-preparation_rt.json \ 
    --gt gt.stl \
    --output heatmap.png
"""  

import argparse, json
from pathlib import Path
import numpy as np
import pyvista as pv

def main():
    p=argparse.ArgumentParser()
    p.add_argument('stl',type=Path); 
    # p.add_argument('rt_json',type=Path)
    p.add_argument('rt_json',type=Path)
    p.add_argument('-o','--output',type=Path,default=None)
    p.add_argument('--gt',type=Path,default=None,help='ground-truth STL for distance heatmap')
    p.add_argument('--clim',type=float,default=None,help='maximum heatmap distance')
    args=p.parse_args(); 
    out=args.output or args.stl.with_name(args.stl.stem+'_render.png')
    data=json.loads(args.rt_json.read_text()); 
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
        vmax=args.clim or float(np.percentile(scalars,99)) or 1.0
        pl.add_mesh(mesh,scalars='error_mm',cmap='turbo',clim=(0,vmax),smooth_shading=True,show_scalar_bar=True,scalar_bar_args={'title':'Distance (mm)'})
    pl.add_axes(); 
    pl.camera_position='iso'; 
    pl.camera.zoom(1.35)
    pl.show(screenshot=str(out),auto_close=True)
    print(out)
if __name__=='__main__': main()
