# Singularity Notes

This folder provides the recommended Nurion execution path.

## What It Covers

- `Singularity.def`: base image recipe
- `run_smoke50_in_container.sh`: interactive 50-complex smoke test
- `run_full_in_container.sh`: full PDBbind run inside a container

## Recommended Usage

Use a prebuilt image and run it directly.

Typical image location:

- `/scratch/r992a02/containers/vinadock.sif`

Routine use on Nurion does not require `fakeroot`.

- smoke test: `bash run_smoke50_in_container.sh /scratch/r992a02/containers/vinadock.sif`
- full batch: `qsub ../pbs/run_full_pdbbind2021_singularity.pbs`

## Build Notes

Nurion documentation states that local Singularity builds may require
`fakeroot` approval. If building on Nurion is inconvenient, build the image on
another Linux machine and copy the resulting `.sif` to `/scratch`.

## Example Build

```bash
module load singularity/3.11.0
mkdir -p /scratch/r992a02/containers
cd /scratch/r992a02/Docking/nurion/singularity
singularity build --fakeroot /scratch/r992a02/containers/vinadock.sif Singularity.def
```

If `--fakeroot` is not available for your account, use a remote build or build
the image outside Nurion.
