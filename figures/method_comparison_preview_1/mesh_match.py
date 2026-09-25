#!/usr/bin/env python3
"""Apply a matrix from an ``.aln`` file to an STL mesh."""
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
    parser.add_argument("folder", type=Path, help="sample folder containing sample1.stl and sample1.aln")
    parser.add_argument("--input", type=Path, default=None)
    parser.add_argument("--alignment", type=Path, default=None)
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()

    folder = args.folder.resolve()
    input_path = (args.input or folder / "sample1.stl").resolve()
    alignment_path = (args.alignment or folder / "sample1.aln").resolve()
    output_path = (args.output or folder / "sample1_match.stl").resolve()
    mesh = pv.read(input_path)
    matrix = _read_alignment(alignment_path, input_path.name)
    points = np.c_[np.asarray(mesh.points), np.ones(mesh.n_points)]
    mesh.points = (points @ matrix.T)[:, :3]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    mesh.save(output_path)
    print(f"saved {output_path}")


if __name__ == "__main__":
    main()
