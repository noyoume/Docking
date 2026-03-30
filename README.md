# Vina Docking Pipeline

A generic AutoDock Vina re-docking framework. Clone this repo and run on any server with conda/mamba.

## Pipeline

1. **Water stripping** -- remove HOH/WAT from protein PDB
2. **Receptor prep** -- ADFRsuite `prepare_receptor4.py` (preserves metal ions)
3. **Ligand precheck + prep** -- RDKit sanity check, optional explicit-H rescue, then Meeko `mk_prepare_ligand.py`
4. **Grid box** -- adaptive box from crystal ligand bounding box + padding
5. **Vina docking** -- multiple random seeds, each producing N poses
6. **Scoring** -- symmetry-corrected RMSD (spyrmsd Hungarian) vs crystal pose
7. **Summary** -- per-complex CSV + global summary

## Quick Start

```bash
# 1. Create environments
bash setup_env.sh

# 2. Configure
cp config.env.example config.env
# Edit config.env with your paths

# 3. Activate main environment
conda activate vina_dock

# 4. Run
python3 run.py --config config.env
```

## Input Format

The pipeline expects a `complexes/` directory:

```
complexes/
  3Q47/
    protein.pdb
    ligand.sdf
  3WNG/
    protein.pdb
    ligand.sdf
  ...
```

Each subdirectory name is used as `complex_id`. Both `protein.pdb` and `ligand.sdf` must be present.

### PDBbind Data

To convert PDBbind v2021 tar archives into the standard input format:

```bash
python3 utils/extract_pdbbind2021.py \
    --tar-dir /path/to/pdbbind/tars \
    --output-dir complexes \
    --sample 5
```

## CLI Options

```
python3 run.py [OPTIONS]

  --config FILE         Path to .env config file (default: config.env)
  --complexes-dir DIR   Override VINADOCK_COMPLEXES_DIR
  --output-dir DIR      Override VINADOCK_OUTPUT_DIR
  --no-skip             Re-run even if scores.csv already exists
```

## Configuration Reference

All settings use `VINADOCK_*` environment variables. See `config.env.example` for the full list.

| Variable | Default | Description |
|---|---|---|
| `VINADOCK_COMPLEXES_DIR` | `.` | Input complexes directory |
| `VINADOCK_OUTPUT_DIR` | `output` | Output directory |
| `VINADOCK_ADFR_PYTHON` | `python` | ADFRsuite Python interpreter |
| `VINADOCK_ADFR_PREP_RECEPTOR` | `prepare_receptor4.py` | ADFRsuite receptor prep script |
| `VINADOCK_EXHAUSTIVENESS` | `8` | Vina exhaustiveness |
| `VINADOCK_NUM_MODES` | `10` | Poses per run |
| `VINADOCK_NUM_RUNS` | `10` | Number of random seeds |
| `VINADOCK_ENERGY_RANGE` | `5.0` | Vina energy range (kcal/mol) |
| `VINADOCK_VINA_TIMEOUT` | `600` | Timeout per Vina run (seconds) |
| `VINADOCK_GRID_PADDING` | `3.0` | Grid padding around ligand (angstroms) |
| `VINADOCK_MAX_GRID_SIZE` | `126.0` | Maximum grid dimension |
| `VINADOCK_SKIP_EXISTING` | `true` | Skip completed complexes |
| `VINADOCK_FAIL_LOG` | `failures.csv` | Failure log filename |

## Output Structure

```
output/
  3Q47/
    protein_nohoh.pdb
    receptor.pdbqt
    ligand_prepared.sdf
    ligand.pdbqt
    box.txt
    run_01.pdbqt ... run_10.pdbqt
    scores.csv
  summary.csv
  failures.csv
```

## Requirements

Two conda environments (created by `setup_env.sh`):

- **vina_dock** (Python 3.10): `vina`, `meeko`, `rdkit`, `spyrmsd`, `numpy`
- **adcpsuite** (Python 3.7): `adfr` (ADFRsuite/AutoDockTools)

ADFRsuite requires Python 3.7, which is why it runs in a separate environment via subprocess.

Runtime prerequisites to verify on a new server:

- `vina` must be callable from the active `vina_dock` environment
- `mk_prepare_ligand.py` must be callable from the active `vina_dock` environment
- RDKit and `spyrmsd` must import successfully in `vina_dock`
- `VINADOCK_ADFR_PYTHON` and `VINADOCK_ADFR_PREP_RECEPTOR` must point to real ADFRsuite paths

## Ligand Policy

Ligand preparation follows a conservative default policy:

- Use `ligand.sdf` as the authoritative ligand input
- Preserve the input ligand chemistry by default
- Run an RDKit precheck before Meeko:
  - unreadable SDF -> fail
  - unsupported elements for the current Vina workflow -> fail
  - multi-fragment ligand -> fail
- If RDKit detects implicit hydrogens, convert them to explicit hydrogens with
  `AddHs(mol, addCoords=True)` and write `ligand_prepared.sdf`
- Do **not** enumerate tautomers or protonation states by default
- Do **not** replace unsupported atoms such as boron with surrogate atom types

This keeps the workflow consistent across datasets while still rescuing the
common “implicit Hs” input issue without moving heavy-atom coordinates.

## Failure Logging

`failures.csv` stores step-specific reasons such as:

- `ligand_unsupported_element`
- `ligand_multifragment`
- `ligand_implicit_hs`
- `vina_invalid_atom_type`
- `vina_timeout`
