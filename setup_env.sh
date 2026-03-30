#!/usr/bin/env bash
# Create conda environments for the Vina docking pipeline.
# Usage: bash setup_env.sh
#
# Two environments are created:
#   vina_dock   (Python 3.10) - main pipeline: vina, meeko, rdkit, spyrmsd
#   adcpsuite   (Python 3.7)  - receptor prep: ADFRsuite/AutoDockTools
#
# After running this script, update config.env with the correct paths:
#   VINADOCK_ADFR_PYTHON      -> <conda_prefix>/envs/adcpsuite/bin/python
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
$CONDA_CMD run -n adcpsuite pip install adfr

# --- Print paths for config.env ---
echo ""
echo "=== Setup complete ==="
echo ""

ADFR_PYTHON="$($CONDA_CMD run -n adcpsuite which python)"
echo "Add the following to your config.env:"
echo ""
echo "VINADOCK_ADFR_PYTHON=${ADFR_PYTHON}"

# Find prepare_receptor4.py
PREP_SCRIPT="$($CONDA_CMD run -n adcpsuite python -c "
import AutoDockTools
from pathlib import Path
p = Path(AutoDockTools.__file__).parent / 'Utilities24' / 'prepare_receptor4.py'
print(p)
" 2>/dev/null || echo "NOT_FOUND")"

if [ "$PREP_SCRIPT" != "NOT_FOUND" ] && [ -f "$PREP_SCRIPT" ]; then
    echo "VINADOCK_ADFR_PREP_RECEPTOR=${PREP_SCRIPT}"
else
    echo "# Could not auto-detect prepare_receptor4.py path."
    echo "# Find it manually: find \$(conda info --base)/envs/adcpsuite -name prepare_receptor4.py"
fi

echo ""
echo "Activate the main environment with: conda activate vina_dock"
