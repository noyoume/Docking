#!/bin/bash
set -euo pipefail

REPO_DIR="${REPO_DIR:-/scratch/r992a02/Docking}"
DATA_DIR="${DATA_DIR:-/scratch/r992a02/PDBBind2021}"
WORK_ROOT="${WORK_ROOT:-/scratch/r992a02/docking_full_pdbbind2021_container}"
NUM_SHARDS="${NUM_SHARDS:-96}"

mkdir -p "${WORK_ROOT}"
mkdir -p "${WORK_ROOT}/complexes"

python3 "${REPO_DIR}/utils/extract_pdbbind2021.py" \
    --tar-dir "${DATA_DIR}" \
    --output-dir "${WORK_ROOT}/complexes"

python3 "${REPO_DIR}/nurion/scripts/create_complex_shards.py" \
    --complexes-dir "${WORK_ROOT}/complexes" \
    --shards-root "${WORK_ROOT}/shards" \
    --num-shards "${NUM_SHARDS}"

echo "Prepared complexes in ${WORK_ROOT}/complexes"
echo "Prepared shards in ${WORK_ROOT}/shards"
