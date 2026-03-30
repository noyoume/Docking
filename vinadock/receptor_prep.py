"""Receptor preparation: water stripping + ADFRsuite prepare_receptor4.py."""

import subprocess
from pathlib import Path

from .config import Config


def strip_waters(protein_pdb: Path, output_pdb: Path):
    """Write a copy of protein.pdb with HOH/WAT HETATM records removed."""
    kept = []
    with open(protein_pdb) as f:
        for line in f:
            if line.startswith("HETATM") and line[17:20].strip().upper() in {"HOH", "WAT"}:
                continue
            kept.append(line)
    output_pdb.write_text("".join(kept), encoding="utf-8")


def prepare_receptor(protein_pdb: Path, output_dir: Path, config: Config) -> Path | None:
    """Strip waters and run ADFRsuite prepare_receptor4.py.

    Returns path to receptor.pdbqt on success, None on failure.
    """
    nohoh_pdb = output_dir / "protein_nohoh.pdb"
    receptor_pdbqt = output_dir / "receptor.pdbqt"

    # Strip waters
    try:
        strip_waters(protein_pdb, nohoh_pdb)
    except Exception as e:
        print(f"  [ERROR] Failed to strip waters: {e}")
        return None

    # Run ADFRsuite
    try:
        result = subprocess.run(
            [
                str(config.adfr_python),
                str(config.adfr_prep_receptor),
                "-r", str(nohoh_pdb),
                "-o", str(receptor_pdbqt),
                "-A", "hydrogens",
            ],
            capture_output=True, text=True, timeout=180,
        )
        if receptor_pdbqt.exists() and receptor_pdbqt.stat().st_size > 0:
            if result.returncode != 0:
                print(f"  [WARN] prepare_receptor4.py returned rc={result.returncode}, but receptor.pdbqt was created")
                if result.stderr:
                    print(f"    stderr: {result.stderr[:500]}")
            return receptor_pdbqt
        print(f"  [ERROR] prepare_receptor4.py failed (rc={result.returncode})")
        if result.stderr:
            print(f"    stderr: {result.stderr[:500]}")
    except Exception as e:
        print(f"  [ERROR] prepare_receptor4.py failed: {e}")

    return None
