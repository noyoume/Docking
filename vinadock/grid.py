"""Adaptive grid box calculation from reference ligand."""

import numpy as np
from pathlib import Path


def compute_grid_box(ligand_sdf: Path, padding: float, max_size: float) -> dict | None:
    """Compute adaptive grid box from crystal ligand heavy atoms.

    Returns dict with center_x/y/z and size_x/y/z, or None on failure.
    """
    from rdkit import Chem

    supplier = Chem.SDMolSupplier(str(ligand_sdf), removeHs=True)
    mol = next(iter(supplier), None)
    if mol is None:
        print(f"  [ERROR] Cannot read ligand SDF: {ligand_sdf}")
        return None

    conf = mol.GetConformer()
    coords = np.array([conf.GetAtomPosition(i) for i in range(mol.GetNumAtoms())])

    mins = coords.min(axis=0)
    maxs = coords.max(axis=0)
    center = 0.5 * (mins + maxs)
    span = maxs - mins
    size = span + 2 * padding
    size = np.minimum(size, max_size)

    return {
        "center_x": float(center[0]),
        "center_y": float(center[1]),
        "center_z": float(center[2]),
        "size_x": float(size[0]),
        "size_y": float(size[1]),
        "size_z": float(size[2]),
    }
