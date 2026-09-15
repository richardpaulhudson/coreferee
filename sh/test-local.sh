#!/usr/bin/env bash
# Run Coreferee tests locally (mirrors CI). Requires pyenv.
#
# For "which python" to work in your shell:
#   Fish: add to ~/.config/fish/config.fish:  pyenv init - | source
#   Bash/zsh: add to ~/.bashrc or ~/.zshrc:  eval "$(pyenv init -)" and eval "$(pyenv init --path)"
# Then restart the terminal (or run: exec fish / exec zsh).
#
# Usage:
#   ./scripts/test-local.sh                    # Python 3.12 + spaCy 3.7.0
#   PYTHON_VERSION=3.11 SPACY_VERSION=3.5.3 ./scripts/test-local.sh
#
# First run downloads many spaCy models; use QUICK=1 to use only small models
# and run a subset of tests.

set -e

PYTHON_VERSION="${PYTHON_VERSION:-3.12}"
SPACY_VERSION="${SPACY_VERSION:-3.7.5}"
CLICK_VERSION="${CLICK_VERSION:-8.0.1}"
VENV_DIR="${VENV_DIR:-.venv-test}"

cd "$(dirname "$0")/.."

# Ensure Python version is installed and set locally (use exact patch version so
# the IDE/venv don't look for a different 3.12.x like 3.12.13 that isn't installed)
INSTALLED=$(pyenv versions --bare | grep "^${PYTHON_VERSION}" | sort -V | tail -1)
if [ -z "${INSTALLED}" ]; then
  echo "Installing Python ${PYTHON_VERSION} via pyenv..."
  pyenv install -s "${PYTHON_VERSION}"
  INSTALLED=$(pyenv versions --bare | grep "^${PYTHON_VERSION}" | sort -V | tail -1)
fi
pyenv local "${INSTALLED}"
echo "Using Python ${INSTALLED}"

# Use pyenv's Python by path so we don't rely on pyenv shims being in PATH
PYENV_ROOT="${PYENV_ROOT:-$HOME/.pyenv}"
PYTHON_BIN="${PYENV_ROOT}/versions/${INSTALLED}/bin/python"
if [ ! -x "${PYTHON_BIN}" ]; then
  echo "Error: ${PYTHON_BIN} not found. Ensure pyenv is installed and Python ${INSTALLED} is installed." >&2
  exit 1
fi

# Create venv and install dependencies
"${PYTHON_BIN}" -m venv "${VENV_DIR}"
# shellcheck disable=SC1090
source "${VENV_DIR}/bin/activate"

python -m pip install --upgrade pip
pip install "spacy==${SPACY_VERSION}" pytest
pip uninstall -y click 2>/dev/null || true
pip install "click==${CLICK_VERSION}"

# Use a local pip cache so model wheels persist across venv rebuilds
SPACY_CACHE="${SPACY_CACHE:-.spacy-cache}"
mkdir -p "${SPACY_CACHE}"
export PIP_CACHE_DIR="${SPACY_CACHE}"

ensure_model() {
  local model=$1
  local module_name="${model//-/_}"
  if python -c "import ${module_name}" 2>/dev/null; then
    echo "  ${model} — already installed, skipping."
  else
    python -m spacy download "${model}"
  fi
}

echo "Installing spaCy models (cached in ${SPACY_CACHE})..."
if [ "${QUICK:-0}" = "1" ]; then
  echo "QUICK mode: small models only..."
  ensure_model en_core_web_sm
  ensure_model de_core_news_sm
  ensure_model fr_core_news_sm
  ensure_model pl_core_news_sm
else
  ensure_model en_core_web_sm
  ensure_model en_core_web_md
  ensure_model en_core_web_lg
  ensure_model en_core_web_trf
  ensure_model de_core_news_sm
  ensure_model de_core_news_md
  ensure_model de_core_news_lg
  ensure_model fr_core_news_sm
  ensure_model fr_core_news_md
  ensure_model fr_core_news_lg
  ensure_model pl_core_news_sm
  ensure_model pl_core_news_md
  ensure_model pl_core_news_lg
fi

pip install -e .
python -m coreferee install en
python -m coreferee install de
python -m coreferee install fr
python -m coreferee install pl

echo "Running tests..."
python -m pytest --lf tests/common tests/en tests/de tests/fr tests/pl -v | tee pytest.log

echo "Done. Venv left in ${VENV_DIR}; to reuse: Fish: source ${VENV_DIR}/bin/activate.fish  |  Bash/zsh: source ${VENV_DIR}/bin/activate"
