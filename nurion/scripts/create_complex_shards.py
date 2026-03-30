#!/usr/bin/env python3
"""Create shard directories for PBS array jobs by symlinking complex folders."""

import argparse
import shutil
from pathlib import Path


def discover_complexes(complexes_dir: Path) -> list[Path]:
    found = []
    for d in sorted(complexes_dir.iterdir()):
        if not d.is_dir():
            continue
        if (d / "protein.pdb").exists() and (d / "ligand.sdf").exists():
            found.append(d)
    return found


def main():
    parser = argparse.ArgumentParser(description="Create shard directories from complexes/")
    parser.add_argument("--complexes-dir", type=Path, required=True)
    parser.add_argument("--shards-root", type=Path, required=True)
    parser.add_argument("--num-shards", type=int, required=True)
    args = parser.parse_args()

    complexes = discover_complexes(args.complexes_dir)
    if not complexes:
        raise SystemExit(f"No valid complexes found in {args.complexes_dir}")

    if args.shards_root.exists():
        shutil.rmtree(args.shards_root)
    args.shards_root.mkdir(parents=True, exist_ok=True)

    shards = [[] for _ in range(args.num_shards)]
    for idx, complex_dir in enumerate(complexes):
        shards[idx % args.num_shards].append(complex_dir)

    for shard_idx, shard_complexes in enumerate(shards, start=1):
        shard_dir = args.shards_root / f"shard_{shard_idx:04d}"
        shard_dir.mkdir(parents=True, exist_ok=True)
        manifest = shard_dir / "complex_ids.txt"
        with open(manifest, "w") as mf:
            for complex_dir in shard_complexes:
                target = shard_dir / complex_dir.name
                target.symlink_to(complex_dir.resolve(), target_is_directory=True)
                mf.write(f"{complex_dir.name}\n")
        print(f"{shard_dir.name}: {len(shard_complexes)} complexes")

    print(f"Created {args.num_shards} shards under {args.shards_root}")


if __name__ == "__main__":
    main()
