#!/bin/bash
set -o errexit -o nounset -o pipefail

SCRIPTS_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )";
REPO_BASE_DIR=${SCRIPTS_DIR}/..

echo "Building the universe!";

mkdir -p ${REPO_BASE_DIR}/target/;

$SCRIPTS_DIR/"0-validate-version.sh";
$SCRIPTS_DIR/"validate-packages.py";
$SCRIPTS_DIR/gen-universe.py --repository=${REPO_BASE_DIR}/repo/packages/ --out-dir=${REPO_BASE_DIR}/target/;
