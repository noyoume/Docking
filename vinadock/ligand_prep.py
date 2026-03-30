"""Ligand preparation: RDKit precheck + Meeko mk_prepare_ligand.py."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path

from rdkit import Chem


# Conservative ligand element set based on common Vina/Meeko workflows.
SUPPORTED_ELEMENTS = {
    "H", "C", "N", "O", "F", "MG", "P", "S", "CL",
    "CA", "MN", "FE", "ZN", "BR", "I",
}


@dataclass
class LigandPrepResult:
    """Structured result for ligand preparation."""

    pdbqt_path: Path | None
    prepared_sdf: Path | None
    reason: str | None = None
    detail: str | None = None
    rescue: str | None = None


def _load_sdf(ligand_sdf: Path) -> Chem.Mol | None:
    supplier = Chem.SDMolSupplier(str(ligand_sdf), removeHs=False)
    return next(iter(supplier), None)


def _has_implicit_hs(mol: Chem.Mol) -> bool:
    return any(atom.GetNumImplicitHs() > 0 for atom in mol.GetAtoms())


def _unsupported_elements(mol: Chem.Mol) -> list[str]:
    found = {atom.GetSymbol().upper() for atom in mol.GetAtoms()}
    return sorted(elem for elem in found if elem not in SUPPORTED_ELEMENTS)


def _write_prepared_sdf(mol: Chem.Mol, prepared_sdf: Path) -> None:
    writer = Chem.SDWriter(str(prepared_sdf))
    writer.write(mol)
    writer.close()


def _run_meeko(input_sdf: Path, ligand_pdbqt: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["mk_prepare_ligand.py", "-i", str(input_sdf), "-o", str(ligand_pdbqt)],
        capture_output=True,
        text=True,
        timeout=60,
    )


def prepare_ligand(ligand_sdf: Path, output_dir: Path) -> LigandPrepResult:
    """Convert ligand SDF to PDBQT with RDKit precheck and Meeko."""
    ligand_pdbqt = output_dir / "ligand.pdbqt"
    prepared_sdf = output_dir / "ligand_prepared.sdf"

    try:
        mol = _load_sdf(ligand_sdf)
        if mol is None:
            return LigandPrepResult(
                pdbqt_path=None,
                prepared_sdf=None,
                reason="ligand_rdkit_read_failed",
                detail=f"RDKit could not read {ligand_sdf.name}",
            )

        unsupported = _unsupported_elements(mol)
        if unsupported:
            return LigandPrepResult(
                pdbqt_path=None,
                prepared_sdf=None,
                reason="ligand_unsupported_element",
                detail="unsupported elements: " + ",".join(unsupported),
            )

        fragments = Chem.GetMolFrags(mol)
        if len(fragments) != 1:
            return LigandPrepResult(
                pdbqt_path=None,
                prepared_sdf=None,
                reason="ligand_multifragment",
                detail=f"RDKit molecule has {len(fragments)} fragments. Must have 1.",
            )

        rescue = None
        if _has_implicit_hs(mol):
            mol = Chem.AddHs(mol, addCoords=True)
            rescue = "rdkit_addhs"

        _write_prepared_sdf(mol, prepared_sdf)
        result = _run_meeko(prepared_sdf, ligand_pdbqt)

        if result.returncode == 0 and ligand_pdbqt.exists() and ligand_pdbqt.stat().st_size > 0:
            return LigandPrepResult(
                pdbqt_path=ligand_pdbqt,
                prepared_sdf=prepared_sdf,
                rescue=rescue,
            )

        detail = (result.stderr or result.stdout or "").strip()[:500]
        if "implicit Hs" in detail and rescue is None:
            rescued = Chem.AddHs(mol, addCoords=True)
            rescue = "rdkit_addhs"
            _write_prepared_sdf(rescued, prepared_sdf)
            retry = _run_meeko(prepared_sdf, ligand_pdbqt)
            if retry.returncode == 0 and ligand_pdbqt.exists() and ligand_pdbqt.stat().st_size > 0:
                return LigandPrepResult(
                    pdbqt_path=ligand_pdbqt,
                    prepared_sdf=prepared_sdf,
                    rescue=rescue,
                )
            detail = (retry.stderr or retry.stdout or "").strip()[:500]

        reason = "ligand_prep_failed"
        if "implicit Hs" in detail:
            reason = "ligand_implicit_hs"
        elif "Must have 1." in detail and "fragments" in detail:
            reason = "ligand_multifragment"

        print(f"  [ERROR] mk_prepare_ligand failed (rc={result.returncode})")
        if detail:
            print(f"    detail: {detail}")
        return LigandPrepResult(
            pdbqt_path=None,
            prepared_sdf=prepared_sdf if prepared_sdf.exists() else None,
            reason=reason,
            detail=detail or f"mk_prepare_ligand failed (rc={result.returncode})",
            rescue=rescue,
        )
    except Exception as e:
        print(f"  [ERROR] Ligand prep failed: {e}")
        return LigandPrepResult(
            pdbqt_path=None,
            prepared_sdf=None,
            reason="ligand_prep_exception",
            detail=str(e),
        )
