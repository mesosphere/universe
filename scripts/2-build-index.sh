#!/bin/bash
set -o errexit -o nounset -o pipefail

SCRIPTS_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )";
UNIVERSE_DIR="$SCRIPTS_DIR/..";
META_DIR="$UNIVERSE_DIR/repo/meta"

INDEX_FILE_NAME="index.json"

echo "Building index...";
$SCRIPTS_DIR/"build-index.py" $UNIVERSE_DIR;
echo "OK";

echo "Compressing index...";
gzip -c -n "$META_DIR/$INDEX_FILE_NAME" > "$META_DIR/$INDEX_FILE_NAME.gz";

echo "OK";

