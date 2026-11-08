#!/usr/bin/env bash
# Source this file before building/running gem5 with a conda Python:
#
#   source ./init-env.sh [conda-env-name]
#
# Default environment name is py312. Override by passing an argument or setting
# GEM5_CONDA_ENV before sourcing.

if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
    echo "ERROR: run this script with source, not as an executable:"
    echo "  source ./init-env.sh [conda-env-name]"
    exit 1
fi

_gem5_repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
_gem5_conda_env="${1:-${GEM5_CONDA_ENV:-py312}}"

if ! command -v conda >/dev/null 2>&1; then
    if [[ -f "$HOME/miniconda3/etc/profile.d/conda.sh" ]]; then
        # shellcheck disable=SC1091
        source "$HOME/miniconda3/etc/profile.d/conda.sh"
    elif [[ -f "$HOME/anaconda3/etc/profile.d/conda.sh" ]]; then
        # shellcheck disable=SC1091
        source "$HOME/anaconda3/etc/profile.d/conda.sh"
    else
        echo "ERROR: conda was not found. Initialize conda first, or edit init-env.sh."
        return 1
    fi
fi

conda activate "$_gem5_conda_env" || return 1

export GEM5_REPO_ROOT="$_gem5_repo_root"
export GEM5_SRC="$GEM5_REPO_ROOT/CHAOS/gem5"
export GEM5_BUILD_DIR="$GEM5_SRC/build"
export GEM5_X86_OPT="$GEM5_BUILD_DIR/X86/gem5.opt"
export GEM5_ARM_OPT="$GEM5_BUILD_DIR/ARM/gem5.opt"
export GEM5_OPT="${GEM5_OPT:-$GEM5_X86_OPT}"

if [[ -n "${CONDA_PREFIX:-}" ]]; then
    export LD_LIBRARY_PATH="$CONDA_PREFIX/lib:${LD_LIBRARY_PATH:-}"
    if [[ -x "$CONDA_PREFIX/bin/python3-config" ]]; then
        export PYTHON_CONFIG="$CONDA_PREFIX/bin/python3-config"
    elif [[ -x "$CONDA_PREFIX/bin/python-config" ]]; then
        export PYTHON_CONFIG="$CONDA_PREFIX/bin/python-config"
    fi
fi

export PYTHONPATH="$GEM5_SRC:${PYTHONPATH:-}"

echo "gem5 environment initialized"
echo "  conda env:      $_gem5_conda_env"
echo "  CONDA_PREFIX:   ${CONDA_PREFIX:-unset}"
echo "  GEM5_SRC:       $GEM5_SRC"
echo "  GEM5_OPT:       $GEM5_OPT"
echo "  PYTHON_CONFIG:  ${PYTHON_CONFIG:-not found}"
echo
echo "Build X86 with:"
echo "  cd \"$GEM5_SRC\""
echo "  scons build/X86/gem5.opt -j\"\$(nproc)\" PYTHON_CONFIG=\"\$PYTHON_CONFIG\""

unset _gem5_repo_root
unset _gem5_conda_env
