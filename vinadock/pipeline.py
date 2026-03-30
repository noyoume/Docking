"""Main pipeline: discover complexes, run docking, collect results."""

from pathlib import Path

from .config import Config
from .receptor_prep import prepare_receptor
from .ligand_prep import prepare_ligand
from .grid import compute_grid_box
from .docking import run_vina
from .scoring import score_complex, load_scores_csv
from .summary import write_summary, append_failure


def discover_complexes(complexes_dir: Path) -> list[tuple[str, Path]]:
    """Find all valid complex directories.

    Each subdirectory must contain protein.pdb and ligand.sdf.
    Returns sorted list of (complex_id, complex_path).
    """
    found = []
    for d in sorted(complexes_dir.iterdir()):
        if not d.is_dir():
            continue
        protein = d / "protein.pdb"
        ligand = d / "ligand.sdf"
        if protein.exists() and ligand.exists():
            found.append((d.name, d))
        else:
            missing = []
            if not protein.exists():
                missing.append("protein.pdb")
            if not ligand.exists():
                missing.append("ligand.sdf")
            print(f"  [SKIP] {d.name}: missing {', '.join(missing)}")
    return found


def is_complete(complex_id: str, output_dir: Path) -> bool:
    """Check if a complex already has scores.csv."""
    scores_csv = output_dir / complex_id / "scores.csv"
    return scores_csv.exists() and scores_csv.stat().st_size > 0


def load_existing_scores(complex_id: str, output_dir: Path) -> list[dict] | None:
    """Load existing scores.csv for a completed complex."""
    return load_scores_csv(output_dir / complex_id / "scores.csv")


def process_one(
    complex_id: str,
    complex_dir: Path,
    config: Config,
) -> list[dict] | None:
    """Run the full pipeline for one complex. Returns score rows or None."""
    out_dir = config.output_dir / complex_id
    out_dir.mkdir(parents=True, exist_ok=True)
    fail_log = config.output_dir / config.fail_log

    protein_pdb = complex_dir / "protein.pdb"
    ligand_sdf = complex_dir / "ligand.sdf"

    # 1. Receptor prep
    print("  Preparing receptor...")
    receptor_pdbqt = prepare_receptor(protein_pdb, out_dir, config)
    if receptor_pdbqt is None:
        append_failure(
            fail_log,
            complex_id,
            "receptor_prep",
            "receptor_prep_failed",
            "receptor prep failed",
        )
        return None

    # 2. Ligand prep
    print("  Preparing ligand...")
    ligand_result = prepare_ligand(ligand_sdf, out_dir)
    ligand_pdbqt = ligand_result.pdbqt_path
    if ligand_pdbqt is None:
        append_failure(
            fail_log,
            complex_id,
            "ligand_prep",
            ligand_result.reason or "ligand_prep_failed",
            ligand_result.detail or "ligand prep failed",
        )
        return None
    if ligand_result.rescue:
        print(f"    ligand rescue: {ligand_result.rescue}")

    # 3. Grid box
    print("  Computing grid box...")
    box = compute_grid_box(ligand_sdf, config.grid_padding, config.max_grid_size)
    if box is None:
        append_failure(
            fail_log,
            complex_id,
            "grid_box",
            "grid_box_failed",
            "grid box calculation failed",
        )
        return None

    with open(out_dir / "box.txt", "w") as f:
        for k, v in box.items():
            f.write(f"{k} = {v:.3f}\n")
    print(f"    center: ({box['center_x']:.1f}, {box['center_y']:.1f}, {box['center_z']:.1f})")
    print(f"    size:   ({box['size_x']:.1f}, {box['size_y']:.1f}, {box['size_z']:.1f})")

    # 4. Vina docking
    print(f"  Running Vina ({config.num_runs} seeds x {config.num_modes} modes)...")
    vina_result = run_vina(receptor_pdbqt, ligand_pdbqt, box, out_dir, config)
    run_files = vina_result.run_files
    if not run_files:
        append_failure(
            fail_log,
            complex_id,
            "vina",
            vina_result.reason or "vina_no_output",
            vina_result.detail or "no vina output",
        )
        return None

    # 5. Scoring / RMSD
    print("  Computing RMSD...")
    scores = score_complex(ligand_sdf, ligand_pdbqt, run_files, out_dir)
    if not scores:
        append_failure(
            fail_log,
            complex_id,
            "scoring",
            "scoring_failed",
            "scoring failed or no valid poses",
        )
        return None

    # Print summary for this complex
    valid = [r for r in scores if r["rmsd"] is not None]
    best_rmsd = min((r["rmsd"] for r in valid), default=None)
    n_under_2 = sum(1 for r in valid if r["rmsd"] < 2.0)
    rmsd_str = f"{best_rmsd:.3f}" if best_rmsd is not None else "N/A"
    print(f"  Result: {len(scores)} poses, best RMSD={rmsd_str}, "
          f"{n_under_2}/{len(valid)} under 2A")

    return scores


def run_all(config: Config):
    """Main entry point: discover, process, summarize."""
    config.validate()
    config.output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("Discovering complexes...")
    print("=" * 60)
    complexes = discover_complexes(config.complexes_dir)
    print(f"Found {len(complexes)} complexes")

    if not complexes:
        print("Nothing to process.")
        return

    all_results = {}
    skipped = 0

    for i, (complex_id, complex_dir) in enumerate(complexes, 1):
        print(f"\n{'=' * 60}")
        print(f"[{i}/{len(complexes)}] {complex_id}")
        print(f"{'=' * 60}")

        if config.skip_existing and is_complete(complex_id, config.output_dir):
            print("  [SKIP] Already complete")
            existing_scores = load_existing_scores(complex_id, config.output_dir)
            if existing_scores:
                all_results[complex_id] = existing_scores
            skipped += 1
            continue

        scores = process_one(complex_id, complex_dir, config)
        if scores:
            all_results[complex_id] = scores

    # Write summary
    print(f"\n{'=' * 60}")
    print("Writing summary")
    print(f"{'=' * 60}")
    summary_path = config.output_dir / "summary.csv"
    summary_rows = write_summary(all_results, summary_path)
    for row in summary_rows:
        print(f"  {row['complex_id']}: {row['n_poses']} poses, "
              f"best_rmsd={row['best_rmsd']}, n_under_2A={row['n_under_2A']}")

    print(f"\nDone. {len(all_results)} completed, {skipped} skipped.")
    print(f"Results in {config.output_dir}")
