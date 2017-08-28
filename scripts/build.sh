#!/bin/bash
set -o errexit -o nounset -o pipefail

SCRIPTS_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
REPO_BASE_DIR=${SCRIPTS_DIR}/..

echo "Building the universe!"

mkdir -p ${REPO_BASE_DIR}/target/

# Create a new virtual environment
rm -rf ${REPO_BASE_DIR}/target/venv
python3 -m venv ${REPO_BASE_DIR}/target/venv

# Install dependencies
${REPO_BASE_DIR}/target/venv/bin/pip install -r ${SCRIPTS_DIR}/requirements/requirements.txt

"${REPO_BASE_DIR}"/target/venv/bin/python3 "$SCRIPTS_DIR"/validate_packages.py
"${REPO_BASE_DIR}"/target/venv/bin/python3 "$SCRIPTS_DIR"/gen_universe.py \
  --repository="${REPO_BASE_DIR}"/repo/packages/ --out-dir="${REPO_BASE_DIR}"/target/

# Delete virtual environment
rm -rf ${REPO_BASE_DIR}/target/venv
