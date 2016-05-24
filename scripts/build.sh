#!/bin/bash
set -o errexit -o nounset -o pipefail

SCRIPTS_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )";

echo "Building the universe!";

$SCRIPTS_DIR/"0-validate-version.sh";
$SCRIPTS_DIR/"1-validate-packages.sh";

