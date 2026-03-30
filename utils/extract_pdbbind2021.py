#!/usr/bin/env python3
"""Extract PDBbind v2021 tar archives into the standard complexes/ format.

PDBbind tars contain directories like:
    {period}/{PDB_ID}/{PDB_ID}_protein.pdb
    {period}/{PDB_ID}/{PDB_ID}_ligand.sdf

This script extracts them into:
    complexes/{PDB_ID}/protein.pdb
    complexes/{PDB_ID}/ligand.sdf
"""

import argparse
import random
import tarfile
from pathlib import Path


def find_tar_files(tar_dir: Path) -> list[Path]:
    """Find all .tar.gz files in a directory."""
    return sorted(tar_dir.glob("*.tar.gz"))


def list_complexes_in_tar(tar_path: Path) -> list[str]:
    """List PDB IDs available in a tar archive."""
    pdb_ids = set()
    with tarfile.open(tar_path, "r:gz") as tar:
        for member in tar.getmembers():
            parts = Path(member.name).parts
            if len(parts) >= 2:
                candidate = parts[1] if len(parts) >= 3 else parts[0]
                if len(candidate) == 4 and candidate.isalnum():
                    pdb_ids.add(candidate)
    return sorted(pdb_ids)


def extract_complex(tar_path: Path, pdb_id: str, output_dir: Path) -> bool:
    """Extract one complex from a tar archive.

    Looks for {*}/{pdb_id}/{pdb_id}_protein.pdb and {*}/{pdb_id}/{pdb_id}_ligand.sdf.
    Returns True on success.
    """
    complex_dir = output_dir / pdb_id
    complex_dir.mkdir(parents=True, exist_ok=True)

    protein_found = False
    ligand_found = False

    with tarfile.open(tar_path, "r:gz") as tar:
        for member in tar.getmembers():
            name = member.name
            if name.endswith(f"{pdb_id}_protein.pdb"):
                data = tar.extractfile(member)
                if data:
                    (complex_dir / "protein.pdb").write_bytes(data.read())
                    protein_found = True
            elif name.endswith(f"{pdb_id}_ligand.sdf"):
                data = tar.extractfile(member)
                if data:
                    (complex_dir / "ligand.sdf").write_bytes(data.read())
                    ligand_found = True

    if not (protein_found and ligand_found):
        missing = []
        if not protein_found:
            missing.append("protein.pdb")
        if not ligand_found:
            missing.append("ligand.sdf")
        print(f"  [WARN] {pdb_id}: missing {', '.join(missing)}")
        return False
    return True


def main():
    parser = argparse.ArgumentParser(
        description="Extract PDBbind v2021 data into standard complexes/ format",
    )
    parser.add_argument(
        "--tar-dir", required=True, type=Path,
        help="Directory containing PDBbind .tar.gz files",
    )
    parser.add_argument(
        "--output-dir", required=True, type=Path,
        help="Output complexes directory",
    )
    parser.add_argument(
        "--sample", type=int, default=0,
        help="Random sample N complexes per tar (0 = all)",
    )
    parser.add_argument(
        "--pdb-ids", nargs="+",
        help="Extract only these PDB IDs",
    )
    parser.add_argument(
        "--seed", type=int, default=42,
        help="Random seed for sampling (default: 42)",
    )
    args = parser.parse_args()

    tar_files = find_tar_files(args.tar_dir)
    if not tar_files:
        print(f"No .tar.gz files found in {args.tar_dir}")
        return

    print(f"Found {len(tar_files)} tar files")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    rng = random.Random(args.seed)
    total = 0

    for tar_path in tar_files:
        print(f"\nProcessing {tar_path.name}...")
        available = list_complexes_in_tar(tar_path)
        print(f"  {len(available)} complexes available")

        if args.pdb_ids:
            targets = [pid for pid in args.pdb_ids if pid in available]
        elif args.sample > 0:
            targets = rng.sample(available, min(args.sample, len(available)))
        else:
            targets = available

        for pdb_id in sorted(targets):
            ok = extract_complex(tar_path, pdb_id, args.output_dir)
            if ok:
                print(f"  {pdb_id}: OK")
                total += 1

    print(f"\nDone. {total} complexes extracted to {args.output_dir}")


if __name__ == "__main__":
    main()
