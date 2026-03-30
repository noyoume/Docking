#!/bin/bash
set -euo pipefail

IMAGE_PATH="${1:-/scratch/r992a02/containers/vinadock.sif}"
REPO_DIR="${REPO_DIR:-/scratch/r992a02/Docking/vina-docking-pipeline}"
DATA_DIR="${DATA_DIR:-/scratch/r992a02/PDBBind2021}"
WORK_ROOT="${WORK_ROOT:-/scratch/r992a02/docking_full_pdbbind2021_container}"

module load singularity/3.11.0

mkdir -p "${WORK_ROOT}"
mkdir -p "${WORK_ROOT}/complexes"

python3 "${REPO_DIR}/utils/extract_pdbbind2021.py" \
    --tar-dir "${DATA_DIR}" \
    --output-dir "${WORK_ROOT}/complexes"

cat > "${WORK_ROOT}/config.env" <<EOF
VINADOCK_COMPLEXES_DIR=${WORK_ROOT}/complexes
VINADOCK_OUTPUT_DIR=${WORK_ROOT}/output

VINADOCK_ADFR_PYTHON=/opt/conda/envs/adcpsuite/bin/python
VINADOCK_ADFR_PREP_RECEPTOR=/opt/conda/envs/adcpsuite/bin/prepare_receptor4.py

VINADOCK_EXHAUSTIVENESS=8
VINADOCK_NUM_MODES=10
VINADOCK_NUM_RUNS=10
VINADOCK_ENERGY_RANGE=5.0
VINADOCK_VINA_TIMEOUT=600

VINADOCK_GRID_PADDING=3.0
VINADOCK_MAX_GRID_SIZE=126.0

VINADOCK_SKIP_EXISTING=true
VINADOCK_FAIL_LOG=failures.csv
EOF

singularity exec \
    --bind "${REPO_DIR}:${REPO_DIR}" \
    --bind "${DATA_DIR}:${DATA_DIR}" \
    --bind "${WORK_ROOT}:${WORK_ROOT}" \
    "${IMAGE_PATH}" \
    /opt/conda/envs/vina_dock/bin/python "${REPO_DIR}/run.py" --config "${WORK_ROOT}/config.env"
