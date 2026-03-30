"""Summary CSV and failure logging."""

import csv
from datetime import datetime
from pathlib import Path


SUMMARY_FIELDS = [
    "complex_id", "n_poses", "best_rmsd", "score_at_best_rmsd",
    "best_run_id", "best_pose_idx", "n_under_2A",
]

FAILURE_FIELDS = ["complex_id", "step", "error", "detail", "timestamp"]


def write_summary(all_results: dict, summary_path: Path) -> list[dict]:
    """Write summary CSV across all complexes."""
    rows = []
    for complex_id, scores in all_results.items():
        if not scores:
            continue
        valid = [r for r in scores if r["rmsd"] is not None]
        if not valid:
            continue
        best_row = min(valid, key=lambda r: r["rmsd"])
        rows.append({
            "complex_id": complex_id,
            "n_poses": len(scores),
            "best_rmsd": f"{best_row['rmsd']:.3f}",
            "score_at_best_rmsd": f"{best_row['vina_score']:.3f}",
            "best_run_id": best_row["run_id"],
            "best_pose_idx": best_row["pose_idx"],
            "n_under_2A": sum(1 for r in valid if r["rmsd"] < 2.0),
        })

    with open(summary_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=SUMMARY_FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    return rows


def append_failure(
    fail_log: Path,
    complex_id: str,
    step: str,
    error: str,
    detail: str = "",
):
    """Append one failure row to the failure CSV."""
    write_header = not fail_log.exists()
    with open(fail_log, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FAILURE_FIELDS)
        if write_header:
            writer.writeheader()
        writer.writerow({
            "complex_id": complex_id,
            "step": step,
            "error": str(error)[:500],
            "detail": str(detail)[:500],
            "timestamp": datetime.now().isoformat(timespec="seconds"),
        })
