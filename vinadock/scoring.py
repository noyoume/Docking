"""Score docked poses: parse PDBQT, reorder atoms, compute RMSD, write CSV."""

import csv
from pathlib import Path

from .pose_parser import parse_pdbqt_poses, build_serial_to_ref_map, reorder_pose_coords
from .rmsd import get_reference_coords, compute_rmsd


SCORE_FIELDS = ["run_id", "pose_idx", "vina_score", "rmsd", "n_atoms_pose", "n_atoms_ref"]


def load_scores_csv(csv_path: Path) -> list[dict] | None:
    """Load an existing scores.csv file back into score rows."""
    if not csv_path.exists() or csv_path.stat().st_size == 0:
        return None

    rows = []
    with open(csv_path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                rows.append({
                    "run_id": int(row["run_id"]),
                    "pose_idx": int(row["pose_idx"]),
                    "vina_score": float(row["vina_score"]),
                    "rmsd": float(row["rmsd"]) if row["rmsd"] not in ("", "None", None) else None,
                    "n_atoms_pose": int(row["n_atoms_pose"]),
                    "n_atoms_ref": int(row["n_atoms_ref"]),
                })
            except (KeyError, ValueError):
                return None
    return rows


def score_complex(
    ligand_sdf: Path,
    ligand_pdbqt: Path,
    run_files: list[tuple[int, Path]],
    output_dir: Path,
) -> list[dict] | None:
    """Parse all docked poses, compute RMSD, write scores.csv.

    Returns list of score dicts, or None on failure.
    """
    ref_coords, ref_atomicn = get_reference_coords(ligand_sdf)
    if ref_coords is None:
        print(f"  [ERROR] Cannot get reference coords from {ligand_sdf}")
        return None

    try:
        serial_to_ref = build_serial_to_ref_map(ligand_pdbqt, ligand_sdf)
    except ValueError as e:
        print(f"  [ERROR] Atom mapping failed: {e}")
        return None

    rows = []
    for seed, pdbqt_path in run_files:
        poses = parse_pdbqt_poses(pdbqt_path)
        for pose_idx, (score, coords_by_serial) in enumerate(poses, 1):
            try:
                pose_coords = reorder_pose_coords(len(ref_coords), serial_to_ref, coords_by_serial)
            except ValueError as e:
                print(f"  [WARN] Skipping run {seed} pose {pose_idx}: {e}")
                continue
            rmsd_val = compute_rmsd(ref_coords, pose_coords, ref_atomicn, ref_atomicn)
            rows.append({
                "run_id": seed,
                "pose_idx": pose_idx,
                "vina_score": score,
                "rmsd": rmsd_val,
                "n_atoms_pose": len(pose_coords),
                "n_atoms_ref": len(ref_coords),
            })

    csv_path = output_dir / "scores.csv"
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=SCORE_FIELDS)
        writer.writeheader()
        writer.writerows(rows)

    return rows
