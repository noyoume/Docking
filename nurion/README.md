# Nurion Guide

This folder contains Nurion-specific helpers for two stages:

1. Interactive smoke test on a compute node with about 50 sampled PDBbind complexes
2. Full PDBbind 2021 batch submission with PBS

The recommended Nurion path is:

- run a prebuilt Singularity image for the smoke test
- if the smoke test succeeds, submit the full PBS batch job with the same image

The micromamba-based files are kept as a fallback, but the primary Nurion
workflow in this repo is now the Singularity execution path.

The examples below assume the following Nurion layout:

- repo: `/scratch/r992a02/Docking/vina-docking-pipeline`
- PDBbind data: `/scratch/r992a02/PDBBind2021`
- micromamba root: `/scratch/r992a02/micromamba`

Adjust paths if your layout changes.

## Files

- `pbs/run_full_pdbbind2021_singularity.pbs`
- `singularity/run_smoke50_in_container.sh`
- `singularity/run_full_in_container.sh`
- `singularity/README.md`
- `singularity/Singularity.def`
- `env/config.nurion.smoke50.env.example`
- `env/config.nurion.full.env.example`
- `scripts/run_smoke50_interactive.sh`
- `pbs/run_full_pdbbind2021.pbs`

## Recommended Order

1. Clone the repo to `/scratch`
2. Prepare or copy a prebuilt `vinadock.sif` image to `/scratch`
3. Start an interactive compute session
4. Run the 50-complex smoke test in the container
5. Inspect `summary.csv` and `failures.csv`
6. If the smoke test looks good, submit the full PBS job with the same image

## 1. Recommended Singularity Workflow

### 1-1. Prebuilt Image

The intended Nurion workflow is to use a prebuilt image such as:

- `/scratch/r992a02/containers/vinadock.sif`

This avoids building on Nurion and avoids any `fakeroot` requirement during
routine use.

### 1-2. Interactive Smoke Test

Request an interactive node from the login node:

```bash
qsub -I -V -q normal -A na1527 -l select=1:ncpus=8:mpiprocs=1:ompthreads=8 -l walltime=02:00:00
```

Once you land on a compute node:

```bash
cd /scratch/r992a02/Docking/vina-docking-pipeline
bash nurion/singularity/run_smoke50_in_container.sh /scratch/r992a02/containers/vinadock.sif
```

That script will:

- load `singularity/3.11.0`
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
qsub nurion/pbs/run_full_pdbbind2021_singularity.pbs
```

This PBS job will:

- load `singularity/3.11.0`
- extract all PDBbind 2021 PL complexes into standard `complexes/` format
- write a production config file
- run the full docking pipeline inside the container with resume enabled

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

## 5. Optional Micromamba Fallback

If you do not want to use Singularity for some reason, this repo still includes
the older micromamba-based path:

- `scripts/run_smoke50_interactive.sh`
- `pbs/run_full_pdbbind2021.pbs`

Those files assume:

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

## 6. Notes On Building Images

Nurion supports Singularity execution. The examples here follow the Nurion
guide pattern:

- load module: `module load singularity/3.11.0`
- interactive test: `singularity exec ...`
- PBS batch: `module load singularity/3.11.0` inside the job script

Important note:

- the provided `Singularity.def` is a portable starting point
- you do not need `fakeroot` to run an already-built `.sif`
- `fakeroot` only becomes relevant if you try to build a custom image from
  `Singularity.def` on Nurion
- if local build is inconvenient, build the image elsewhere and copy the `.sif`
  to `/scratch`

Suggested image path:

- `/scratch/r992a02/containers/vinadock.sif`

Interactive container smoke test:

```bash
qsub -I -V -q normal -A na1527 -l select=1:ncpus=8:mpiprocs=1:ompthreads=8 -l walltime=02:00:00
cd /scratch/r992a02/Docking/vina-docking-pipeline
bash nurion/singularity/run_smoke50_in_container.sh /scratch/r992a02/containers/vinadock.sif
```

PBS container full run:

```bash
cd /scratch/r992a02/Docking/vina-docking-pipeline
qsub nurion/pbs/run_full_pdbbind2021_singularity.pbs
```
