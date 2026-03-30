# Singularity Notes

This folder provides an optional containerized path for Nurion.

## What It Covers

- `Singularity.def`: base image recipe
- `run_smoke50_in_container.sh`: interactive 50-complex smoke test
- `run_full_in_container.sh`: full PDBbind run inside a container

## Build Notes

Nurion documentation states that local Singularity builds may require
`fakeroot` approval. If building on Nurion is inconvenient, build the image on
another Linux machine and copy the resulting `.sif` to `/scratch`.

Typical image location:

- `/scratch/r992a02/containers/vinadock.sif`

## Example Build

```bash
module load singularity/3.11.0
mkdir -p /scratch/r992a02/containers
cd /scratch/r992a02/Docking/vina-docking-pipeline/nurion/singularity
singularity build --fakeroot /scratch/r992a02/containers/vinadock.sif Singularity.def
```

If `--fakeroot` is not available for your account, use a remote build or build
the image outside Nurion.
