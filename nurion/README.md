# Nurion Guide

This folder contains Nurion-specific helpers for two stages:

1. Interactive smoke test on a compute node with about 50 sampled PDBbind complexes
2. Full PDBbind 2021 batch submission with PBS

The examples below assume the following Nurion layout:

- repo: `/scratch/r992a02/Docking/vina-docking-pipeline`
- PDBbind data: `/scratch/r992a02/PDBBind2021`
- micromamba root: `/scratch/r992a02/micromamba`

Adjust paths if your layout changes.

## Files

- `env/config.nurion.smoke50.env.example`
- `env/config.nurion.full.env.example`
- `scripts/run_smoke50_interactive.sh`
- `pbs/run_full_pdbbind2021.pbs`

## Recommended Order

1. Clone the repo to `/scratch`
2. Make sure `vina_dock` and `adcpsuite` environments are available
3. Start an interactive compute session
4. Run the 50-complex smoke test end-to-end
5. Inspect `summary.csv` and `failures.csv`
6. If the smoke test looks good, submit the full PBS job

## 1. Interactive Smoke Test

Request an interactive node from the login node:

```bash
qsub -I -V -q normal -A na1527 -l select=1:ncpus=8:mpiprocs=1:ompthreads=8 -l walltime=02:00:00
```

Once you land on a compute node:

```bash
cd /scratch/r992a02/Docking/vina-docking-pipeline
bash nurion/scripts/run_smoke50_interactive.sh
```

That script will:

- activate `micromamba` and `vina_dock`
- sample 50 complexes from the PDBbind 2021 tar files
- write a smoke-test config file
- run docking and RMSD scoring end-to-end

Expected smoke-test outputs:

- `/scratch/r992a02/docking_smoke50/output/summary.csv`
- `/scratch/r992a02/docking_smoke50/output/failures.csv`

## 2. What To Check After Smoke Test

Check these files first:

```bash
head /scratch/r992a02/docking_smoke50/output/summary.csv
head /scratch/r992a02/docking_smoke50/output/failures.csv
```

The smoke test is considered good enough to move on if:

- receptor prep succeeds broadly
- ligand prep succeeds broadly
- Vina actually writes `run_*.pdbqt`
- `scores.csv` files are being created
- failures are limited to known chemistry exclusions or occasional timeouts

## 3. Full PDBbind Batch Submission

Submit from the login node:

```bash
cd /scratch/r992a02/Docking/vina-docking-pipeline
qsub nurion/pbs/run_full_pdbbind2021.pbs
```

This PBS job will:

- activate `micromamba`
- extract all PDBbind 2021 PL complexes into standard `complexes/` format
- write a production config file
- run the full docking pipeline with resume enabled

Expected full-run root:

- `/scratch/r992a02/docking_full_pdbbind2021`

Main output files:

- `/scratch/r992a02/docking_full_pdbbind2021/output/summary.csv`
- `/scratch/r992a02/docking_full_pdbbind2021/output/failures.csv`

## 4. Parameters

Smoke test parameters:

- `VINADOCK_EXHAUSTIVENESS=4`
- `VINADOCK_NUM_MODES=5`
- `VINADOCK_NUM_RUNS=2`
- `VINADOCK_VINA_TIMEOUT=300`

Full production parameters:

- `VINADOCK_EXHAUSTIVENESS=8`
- `VINADOCK_NUM_MODES=10`
- `VINADOCK_NUM_RUNS=10`
- `VINADOCK_VINA_TIMEOUT=600`

Shared parameters:

- `VINADOCK_ENERGY_RANGE=5.0`
- `VINADOCK_GRID_PADDING=3.0`
- `VINADOCK_MAX_GRID_SIZE=126.0`
- `VINADOCK_SKIP_EXISTING=true`

## 5. Environment Notes

These examples assume:

- `vina_dock` contains `vina`, `meeko`, `rdkit`, `spyrmsd`
- `adcpsuite` contains `prepare_receptor4.py`

If you need to check the envs manually:

```bash
export MAMBA_ROOT_PREFIX=/scratch/r992a02/micromamba
eval "$(/scratch/r992a02/micromamba/bin/micromamba shell hook -s bash)"
micromamba activate vina_dock
which vina
which mk_prepare_ligand.py
python -c "import rdkit, spyrmsd; print('ok')"
```

For ADFRsuite:

```bash
/scratch/r992a02/micromamba/envs/adcpsuite/bin/python -c "print('adcpsuite ok')"
ls /scratch/r992a02/micromamba/envs/adcpsuite/bin/prepare_receptor4.py
```
