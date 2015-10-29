#!/bin/bash
set -o errexit -o nounset -o pipefail

SCRIPTS_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )";
UNIVERSE_DIR="$SCRIPTS_DIR/..";
META_DIR="$UNIVERSE_DIR/repo/meta"

INDEX_FILE_NAME="index.json"

echo "Building index...";
[ -f "$META_DIR/$INDEX_FILE_NAME" ] && rm "$META_DIR/$INDEX_FILE_NAME"
$SCRIPTS_DIR/"build-index.py" $UNIVERSE_DIR;
echo "OK";

