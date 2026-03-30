"""RMSD calculation using spyrmsd (symmetry-corrected Hungarian method)."""

import numpy as np
from pathlib import Path


def get_reference_coords(ligand_sdf: Path) -> tuple[np.ndarray, np.ndarray] | tuple[None, None]:
    """Get heavy atom coordinates and atomic numbers from crystal ligand SDF."""
    from rdkit import Chem

    supplier = Chem.SDMolSupplier(str(ligand_sdf), removeHs=True)
    mol = next(iter(supplier), None)
    if mol is None:
        return None, None
    conf = mol.GetConformer()
    coords = np.array([conf.GetAtomPosition(i) for i in range(mol.GetNumAtoms())])
    atomicn = np.array([atom.GetAtomicNum() for atom in mol.GetAtoms()])
    return coords, atomicn


def compute_rmsd(ref_coords, pose_coords, ref_atomicn, pose_atomicn) -> float:
    """Compute symmetry-corrected RMSD using spyrmsd Hungarian method."""
    from spyrmsd import rmsd as spyrmsd_rmsd

    val = spyrmsd_rmsd.hrmsd(ref_coords, pose_coords, ref_atomicn, pose_atomicn)
    return float(val)
