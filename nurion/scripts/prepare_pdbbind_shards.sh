#!/bin/bash
set -euo pipefail

REPO_DIR="${REPO_DIR:-/scratch/r992a02/Docking}"
DATA_DIR="${DATA_DIR:-/scratch/r992a02/PDBBind2021}"
WORK_ROOT="${WORK_ROOT:-/scratch/r992a02/docking_full_pdbbind2021_container}"
NUM_SHARDS="${NUM_SHARDS:-96}"
SOURCE_SETS="${SOURCE_SETS:-1981-2000 2001-2010 2011-2020 refined+}"

mkdir -p "${WORK_ROOT}"
mkdir -p "${WORK_ROOT}/complexes"
rm -rf "${WORK_ROOT}/complexes"/*

for set_name in ${SOURCE_SETS}; do
    set_dir="${DATA_DIR}/${set_name}"
    if [ ! -d "${set_dir}" ]; then
        echo "Skip missing set: ${set_dir}"
        continue
    fi

    echo "Scanning ${set_dir}"
    for complex_dir in "${set_dir}"/*; do
        if [ ! -d "${complex_dir}" ]; then
            continue
        fi
        complex_id="$(basename "${complex_dir}")"
        protein_src="${complex_dir}/${complex_id}_protein.pdb"
        ligand_src="${complex_dir}/${complex_id}_ligand.sdf"
        if [ ! -f "${protein_src}" ] || [ ! -f "${ligand_src}" ]; then
            continue
        fi

        target_dir="${WORK_ROOT}/complexes/${complex_id}"
        mkdir -p "${target_dir}"
        ln -sfn "${protein_src}" "${target_dir}/protein.pdb"
        ln -sfn "${ligand_src}" "${target_dir}/ligand.sdf"
    done
done

python3 "${REPO_DIR}/nurion/scripts/create_complex_shards.py" \
    --complexes-dir "${WORK_ROOT}/complexes" \
    --shards-root "${WORK_ROOT}/shards" \
    --num-shards "${NUM_SHARDS}"

echo "Prepared complexes in ${WORK_ROOT}/complexes"
echo "Prepared shards in ${WORK_ROOT}/shards"
