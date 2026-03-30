"""AutoDock Vina execution with multiple random seeds."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path

from .config import Config


@dataclass
class VinaRunResult:
    """Structured result for Vina execution."""

    run_files: list[tuple[int, Path]]
    reason: str | None = None
    detail: str | None = None


def _classify_vina_failure(text: str) -> tuple[str, str]:
    compact = (text or "").strip()
    if "not a valid AutoDock type" in compact:
        return "vina_invalid_atom_type", compact[:500]
    return "vina_failed", compact[:500] or "vina returned no output"


def run_vina(
    receptor_pdbqt: Path,
    ligand_pdbqt: Path,
    box: dict,
    output_dir: Path,
    config: Config,
) -> VinaRunResult:
    """Run Vina with multiple seeds."""
    results: list[tuple[int, Path]] = []
    failures: list[tuple[str, str]] = []

    for seed in range(1, config.num_runs + 1):
        out_pdbqt = output_dir / f"run_{seed:02d}.pdbqt"
        cmd = [
            "vina",
            "--receptor", str(receptor_pdbqt),
            "--ligand", str(ligand_pdbqt),
            "--center_x", f"{box['center_x']:.3f}",
            "--center_y", f"{box['center_y']:.3f}",
            "--center_z", f"{box['center_z']:.3f}",
            "--size_x", f"{box['size_x']:.3f}",
            "--size_y", f"{box['size_y']:.3f}",
            "--size_z", f"{box['size_z']:.3f}",
            "--exhaustiveness", str(config.exhaustiveness),
            "--num_modes", str(config.num_modes),
            "--energy_range", str(config.energy_range),
            "--seed", str(seed),
            "--out", str(out_pdbqt),
        ]
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=config.vina_timeout,
            )
            if result.returncode == 0 and out_pdbqt.exists() and out_pdbqt.stat().st_size > 0:
                results.append((seed, out_pdbqt))
                print(f"    seed {seed}: OK")
                continue

            combined = "\n".join(part for part in [result.stderr, result.stdout] if part)
            reason, detail = _classify_vina_failure(combined)
            failures.append((reason, detail))
            print(f"    seed {seed}: failed (rc={result.returncode})")
            if detail:
                print(f"      detail: {detail[:200]}")
        except subprocess.TimeoutExpired:
            failures.append(("vina_timeout", f"seed {seed} exceeded {config.vina_timeout}s"))
            print(f"    seed {seed}: TIMEOUT")
        except Exception as e:
            failures.append(("vina_exception", str(e)))
            print(f"    seed {seed}: ERROR {e}")

    if results:
        return VinaRunResult(run_files=results)

    if failures:
        reason, detail = failures[0]
        return VinaRunResult(run_files=[], reason=reason, detail=detail)
    return VinaRunResult(run_files=[], reason="vina_no_output", detail="no vina output")
