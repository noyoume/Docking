"""Parse docked poses from PDBQT and map atom ordering to reference SDF."""

import numpy as np
from pathlib import Path


def parse_pdbqt_poses(pdbqt_path: Path) -> list[tuple[float, dict]]:
    """Parse multi-model PDBQT, returning (vina_score, coords_by_serial) per pose.

    coords_by_serial maps PDBQT atom serial -> np.array([x, y, z]).
    Only heavy atoms are included (H and HD filtered).
    """
    poses = []
    current_score = None
    current_coords = {}

    with open(pdbqt_path) as f:
        for line in f:
            if line.startswith("MODEL"):
                current_coords = {}
                current_score = None
            elif line.startswith("REMARK VINA RESULT:"):
                parts = line.split()
                current_score = float(parts[3])
            elif line.startswith("ATOM") or line.startswith("HETATM"):
                ad4_type = line.split()[-1]
                if ad4_type in ("H", "HD"):
                    continue
                serial = int(line[6:11])
                x = float(line[30:38])
                y = float(line[38:46])
                z = float(line[46:54])
                current_coords[serial] = np.array([x, y, z], dtype=float)
            elif line.startswith("ENDMDL"):
                if current_score is not None and current_coords:
                    poses.append((current_score, current_coords.copy()))
    return poses


def build_serial_to_ref_map(ligand_pdbqt: Path, ligand_sdf: Path) -> dict:
    """Map PDBQT atom serials to reference SDF atom indices using SMILES IDX.

    Meeko writes REMARK SMILES and REMARK SMILES IDX lines into ligand PDBQT.
    These provide the mapping from PDBQT serial numbers back to the SMILES atom
    indices, which can then be matched to SDF atoms via substructure search.
    """
    from rdkit import Chem

    # Read SMILES and IDX from PDBQT remarks
    smiles = None
    idx_tokens = []
    with open(ligand_pdbqt) as f:
        for line in f:
            if line.startswith("REMARK SMILES IDX "):
                idx_tokens.extend(line.split("REMARK SMILES IDX ", 1)[1].split())
            elif line.startswith("REMARK SMILES "):
                smiles = line.split("REMARK SMILES ", 1)[1].strip()

    if not smiles or not idx_tokens:
        raise ValueError(f"Missing REMARK SMILES/SMILES IDX in {ligand_pdbqt}")

    # Match SMILES to reference SDF
    ref_mol = Chem.SDMolSupplier(str(ligand_sdf), removeHs=True)
    ref_mol = next(iter(ref_mol), None)
    if ref_mol is None:
        raise ValueError(f"Cannot read reference ligand: {ligand_sdf}")

    smiles_mol = Chem.MolFromSmiles(smiles)
    if smiles_mol is None:
        raise ValueError(f"Failed to parse SMILES: {smiles}")

    match = ref_mol.GetSubstructMatch(smiles_mol)
    if len(match) != smiles_mol.GetNumAtoms():
        raise ValueError(f"SMILES substructure match failed against {ligand_sdf}")

    # Build serial -> ref_idx mapping
    serial_to_ref = {}
    for i in range(0, len(idx_tokens), 2):
        smiles_idx_1based = int(idx_tokens[i])
        pdbqt_serial = int(idx_tokens[i + 1])
        serial_to_ref[pdbqt_serial] = match[smiles_idx_1based - 1]
    return serial_to_ref


def reorder_pose_coords(
    ref_n_atoms: int, serial_to_ref: dict, coords_by_serial: dict
) -> np.ndarray:
    """Reorder docked pose coordinates to match reference SDF atom order."""
    coords = [None] * ref_n_atoms
    for serial, xyz in coords_by_serial.items():
        ref_idx = serial_to_ref.get(serial)
        if ref_idx is None:
            continue
        coords[ref_idx] = xyz

    missing = sum(v is None for v in coords)
    if missing:
        raise ValueError(f"{missing} reference atoms have no mapped coordinates")

    return np.array(coords, dtype=float)
