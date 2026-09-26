#!/usr/bin/env python3
"""Apply matrices from Meshlab ``.aln`` files to STL meshes.

python mesh_match.py <id path>
对id path下的 sample*.stl，根据 meshlab 配准输出的sample*.aln进行配准，并输出sample*_match.stl。
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pyvista as pv


def _read_alignment(path: Path, mesh_name: str) -> np.ndarray:
    lines = [line.strip() for line in path.read_text().splitlines() if line.strip()]
    block_indices = [index for index, line in enumerate(lines)
                     if index + 1 < len(lines) and lines[index + 1] == "#"]
    matching = [index for index in block_indices if lines[index] == mesh_name]
    # Some legacy alignment files contain a typo in the mesh name.  If there
    # is only one non-reference mesh block, use it as the intended source.
    if not matching:
        matching = [index for index in block_indices if lines[index] != "gt.stl"]
    for index in matching:
            if index + 5 >= len(lines) or lines[index + 1] != "#":
                raise ValueError(f"invalid alignment block for {mesh_name} in {path}")
            values = []
            for row in lines[index + 2:index + 6]:
                values.extend(float(value) for value in row.split())
            matrix = np.asarray(values, dtype=float).reshape(4, 4)
            if not np.allclose(matrix[3], [0, 0, 0, 1]):
                raise ValueError(f"alignment matrix for {mesh_name} is not homogeneous")
            return matrix
    raise FileNotFoundError(f"no alignment block for {mesh_name} in {path}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("folder", nargs="?", type=Path, default=Path("."),
                        help="sample folder containing sample*.stl and sample*.aln")
    parser.add_argument("--input", type=Path, default=None)
    parser.add_argument("--alignment", type=Path, default=None)
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()

    folder = args.folder.resolve()
    jobs = []
    if args.input or args.alignment or args.output:
        input_path = (args.input or folder / "sample1.stl").resolve()
        alignment_path = (args.alignment or folder / "sample1.aln").resolve()
        output_path = (args.output or folder / "sample1_match.stl").resolve()
        jobs.append((input_path, alignment_path, output_path))
    else:
        for alignment_path in sorted(folder.glob("sample*.aln")):
            stem = alignment_path.stem
            input_path = folder / f"{stem}.stl"
            if not input_path.is_file():
                # Accept legacy filename typos such as sampele3.stl.
                candidates = [path for path in folder.glob("*.stl")
                              if path.name.lower() != "gt.stl" and stem[-1] in path.stem]
                if len(candidates) == 1:
                    input_path = candidates[0]
            if input_path.is_file():
                jobs.append((input_path, alignment_path,
                             folder / f"{stem}_match.stl"))
            else:
                print(f"skip {stem}: no matching STL found")
    if not jobs:
        parser.error("no sample*.aln/STL pairs found")
    for input_path, alignment_path, output_path in jobs:
        mesh = pv.read(input_path)
        matrix = _read_alignment(alignment_path, input_path.name)
        points = np.c_[np.asarray(mesh.points), np.ones(mesh.n_points)]
        mesh.points = (points @ matrix.T)[:, :3]
        output_path.parent.mkdir(parents=True, exist_ok=True)
        mesh.save(output_path)
        print(f"saved {output_path}")


if __name__ == "__main__":
    main()
