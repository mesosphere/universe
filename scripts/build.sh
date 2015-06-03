#!/bin/bash
set -o errexit -o nounset -o pipefail

SCRIPTS_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )";

echo "Building the universe!";

$SCRIPTS_DIR/"0-validate-version.sh";
$SCRIPTS_DIR/"1-validate-packages.sh";
$SCRIPTS_DIR/"2-build-index.sh";
$SCRIPTS_DIR/"3-validate-index.sh";
$SCRIPTS_DIR/"4-detect-dependency-cycles.sh";

