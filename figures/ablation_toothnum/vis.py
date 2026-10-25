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

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import numpy as np
import trimesh
from matplotlib.colors import Normalize
from matplotlib.cm import ScalarMappable
from scripts.ablation2.report_plot_style import plt
from scripts.ablation2.plot_matched_surfaces import raster
from pixal3d.evaluation.metrics import _sample_surface, _closest_point_chunked


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', type=Path, default=Path(__file__).resolve().parent)
    p.add_argument('--output', type=Path, default=None)
    p.add_argument('--vmax', type=float, default=.5)
    p.add_argument('--samples', type=int, default=600000)
    p.add_argument('--page-rows', type=int, default=6)
    p.add_argument('--view', choices=['occlusal', 'oblique'], default='occlusal')
    p.add_argument('--combined', action='store_true', help='Compatibility flag; five-column output is now the default')
    p.add_argument('--limit', type=int, default=None, help='Use first N folders in sorted order for a layout preview')
    a = p.parse_args()
    if a.vmax <= 0 or a.samples < 1 or a.page_rows < 1:
        p.error('vmax, samples and page-rows must be positive')
    out = (a.output or a.root/'figures') / a.view / 'combined'
    out.mkdir(parents=True, exist_ok=True)
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
        cases.append(dict(id=folder.name, paths=paths, origin=origin, axes=axes, frame=frame))
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
        fig = plt.figure(figsize=(14.8, 2.7*len(items)+.4), layout='constrained')
        grid = fig.add_gridspec(len(items), 6, width_ratios=[1,1,1,1,1,.055],
                               wspace=.025, hspace=.035)
        axs = np.empty((len(items), len(labels)), dtype=object)
        for i, (case_id, images) in enumerate(items):
            for j, img in enumerate(images):
                ax = axs[i,j] = fig.add_subplot(grid[i,j])
                ax.imshow(img, extent=(-half,half,-half,half), interpolation='nearest')
                ax.set_aspect('equal', adjustable='box')
                ax.set_xticks([]); ax.set_yticks([])
                for spine in ax.spines.values():
                    spine.set_visible(False)
                # One scale bar per row applies to all five equal-size panels.
                if j == 0:
                    bar_mm = 2. if half >= 2. else half/2
                    x, y = -.85*half, -.85*half
                    ax.plot([x,x+bar_mm], [y,y], color='black', lw=2)
                    ax.text(x+bar_mm/2,y+.07*half,f'{bar_mm:g} mm',ha='center',fontsize=8)
            axs[i,0].set_ylabel(case_id[:8],fontsize=9)
        for j,label in enumerate(labels):
            axs[0,j].set_title(label,fontsize=10,pad=10)
        bar_parent = fig.add_subplot(grid[:,5])
        bar_parent.set_axis_off()
        bar_fraction = min(.85, 2.8/(2.7*len(items)))
        cax = bar_parent.inset_axes([0,(1-bar_fraction)/2,.8,bar_fraction])
        fig.colorbar(ScalarMappable(norm=norm,cmap=cmap), cax=cax, extend='max',
                     label='Prediction-to-GT distance (mm)')
        fig.savefig(out/(name+'.png'),dpi=300,bbox_inches='tight')
        fig.savefig(out/(name+'.pdf'),bbox_inches='tight')
        plt.close(fig)

    for k,case in enumerate(cases):
        meshes = [trimesh.load(f,force='mesh',process=True) for f in case['paths']]
        images, stats, geometries = [], [], []
        opts = dict(backend='warp',allow_cpu_fallback=False,warp_cache={})
        for j,m in enumerate(meshes):
            points,normals,_ = _sample_surface(m,a.samples,2026+j)
            n = normals@case['axes']@rotation
            lighting = .6+.4*np.abs(n@np.array([.25,-.35,.9027735]))
            gray = np.clip(lighting[:,None]*[.72,.75,.78],0,1)
            local = (points-case['origin'])@case['axes']@rotation
            geometries.append(raster(local,gray,half,size=500).astype(np.float32))
            if j == 0:
                colors = gray
            else:
                d = _closest_point_chunked(meshes[0],points,**opts)[1]
                colors = cmap(norm(d))
                stats.append(dict(mesh=str(case['paths'][j]),mean_distance_mm=float(d.mean()),
                                  fraction_above_color_limit=float((d>a.vmax).mean())))
            local = (points-case['origin'])@case['axes']@rotation
            images.append(raster(local,colors,half,size=500).astype(np.float32))
        images = geometries + images[1:]
        rows.append((case['id'],images))
        metadata.append(dict(case_id=case['id'],files=[str(f.resolve()) for f in case['paths']],
                             frame=case['frame'],distances=stats))
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
    (out/'README.txt').write_text('Columns: ' + ', '.join(label.replace('\n',' ') for label in labels) + '\n' +
        'Preview selection uses the first N sorted folder IDs when --limit is supplied.\n'
        'All rows share camera orientation in their recorded frame, physical scale, and color range.\n'
        'Distances are computed in original coordinates, with no ICP or per-method alignment.\n'
        'Units assume STL coordinates are mm. Colors are one-way sampled point-to-triangle distances, not CD.\n'
        'GT is a geometric reference, not a measured error map. Full case IDs are in manifest.json.\n'
        'The TP comparison uses unequal training budgets and does not isolate TP causality.\n')
    print('Saved:',out,flush=True)


if __name__ == '__main__':
    main()
