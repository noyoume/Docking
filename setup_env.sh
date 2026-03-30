#!/usr/bin/env bash
# Create conda environments for the Vina docking pipeline.
# Usage: bash setup_env.sh
#
# Two environments are created:
#   vina_dock   (Python 3.10) - main pipeline: vina, meeko, rdkit, spyrmsd
#   adcpsuite   (Python 3.7)  - receptor prep support env + ADFRsuite paths
#
# After running this script, update config.env with the correct paths:
#   VINADOCK_ADFR_PYTHON      -> <ADFRsuite install>/bin/python
#   VINADOCK_ADFR_PREP_RECEPTOR -> <see output below>

set -euo pipefail

CONDA_CMD=""
for cmd in micromamba mamba conda; do
    if command -v "$cmd" &>/dev/null; then
        CONDA_CMD="$cmd"
        break
    fi
done

if [ -z "$CONDA_CMD" ]; then
    echo "Error: no conda/mamba/micromamba found in PATH" >&2
    exit 1
fi

echo "Using: $CONDA_CMD"

# --- vina_dock environment ---
echo ""
echo "=== Creating vina_dock environment ==="
$CONDA_CMD create -n vina_dock -y python=3.10
$CONDA_CMD install -n vina_dock -y -c conda-forge \
    numpy rdkit spyrmsd
$CONDA_CMD install -n vina_dock -y -c conda-forge \
    vina meeko

# --- adcpsuite environment ---
echo ""
echo "=== Creating adcpsuite environment ==="
$CONDA_CMD create -n adcpsuite -y python=3.7
$CONDA_CMD install -n adcpsuite -y -c conda-forge \
    numpy

echo ""
echo "=== Installing ADFRsuite (official binary) ==="
ADFR_ROOT="${HOME}/.local/ADFRsuite"
TMP_DIR="$(mktemp -d)"
cleanup() {
    rm -rf "$TMP_DIR"
}
trap cleanup EXIT

mkdir -p "$(dirname "$ADFR_ROOT")"
rm -rf "$ADFR_ROOT"

cd "$TMP_DIR"
wget -q https://ccsb.scripps.edu/adfr/download/1038/ -O ADFRsuite_x86_64Linux_1.0.tar.gz
tar xzf ADFRsuite_x86_64Linux_1.0.tar.gz
cd ADFRsuite_x86_64Linux_1.0
printf 'Y\n' | ./install.sh -d "$ADFR_ROOT" -c 0

# --- Print paths for config.env ---
echo ""
echo "=== Setup complete ==="
echo ""

echo "Add the following to your config.env:"
echo ""
echo "VINADOCK_ADFR_PYTHON=${ADFR_ROOT}/bin/python"

PREP_SCRIPT="${ADFR_ROOT}/CCSBpckgs/AutoDockTools/Utilities24/prepare_receptor4.py"
if [ -f "$PREP_SCRIPT" ]; then
    echo "VINADOCK_ADFR_PREP_RECEPTOR=${PREP_SCRIPT}"
else
    echo "# Could not auto-detect prepare_receptor4.py path."
    echo "# Expected under: ${ADFR_ROOT}/CCSBpckgs/AutoDockTools/Utilities24/prepare_receptor4.py"
fi

echo ""
echo "Activate the main environment with: conda activate vina_dock"
