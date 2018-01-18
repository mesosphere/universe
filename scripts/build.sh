#!/bin/bash
set -o errexit -o nounset -o pipefail

####################
#    VARIABLES     #
####################

SCRIPT_NAME=$(basename $0)

####################
#    FUNCTIONS     #
####################

# Usage function
usage() {
  echo "Usage : ${SCRIPT_NAME} [<VENV_BASE_DIR>]"
  echo "Help  : ${SCRIPT_NAME} -h"
  exit 1
}

####################
#       MAIN       #
####################

if [ $# -ne 0 -a $# -ne 1 ]; then
  usage
fi

SCRIPTS_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

if [ $# -ge 1 ]; then
  VENV_BASE_DIR="$1"
else
  VENV_BASE_DIR="$SCRIPTS_DIR/target"
fi

REPO_BASE_DIR=${SCRIPTS_DIR}/..

echo "Building the universe!"

mkdir -p ${REPO_BASE_DIR}/target/

# Create a new virtual environment
rm -rf ${VENV_BASE_DIR}/venv
python3 -m venv ${VENV_BASE_DIR}/venv

# Install dependencies
${VENV_BASE_DIR}/venv/bin/pip install -r "${SCRIPTS_DIR}"/requirements/requirements.txt

"${VENV_BASE_DIR}"/venv/bin/python3 "$SCRIPTS_DIR"/validate_packages.py
"${VENV_BASE_DIR}"/venv/bin/python3 "$SCRIPTS_DIR"/gen_universe.py \
  --repository="${REPO_BASE_DIR}"/repo/packages/ --out-dir="${REPO_BASE_DIR}"/target/

# Delete virtual environment
rm -rf ${VENV_BASE_DIR}/venv
