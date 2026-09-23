#!/usr/bin/env python3
"""Delete PNG files recursively inside the current directory's subfolders."""

import os
from pathlib import Path


def main() -> None:
    root = Path.cwd()
    count = 0
    merged = root / "merged.png"
    if merged.is_file():
        merged.unlink()
        print(f"已删除：{merged.name}")
        count += 1
    for directory, _, filenames in os.walk(root, followlinks=False):
        if Path(directory) == root:
            continue
        for filename in filenames:
            path = Path(directory) / filename
            if path.suffix.lower() == ".png":
                path.unlink()
                print(f"已删除：{path.relative_to(root)}")
                count += 1
    print(f"共删除 {count} 个 PNG 文件。")


if __name__ == "__main__":
    main()
