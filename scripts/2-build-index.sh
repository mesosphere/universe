#!/bin/sh
set -o errexit -o nounset -o pipefail

SCRIPTS_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )";
UNIVERSE_DIR="$SCRIPTS_DIR/..";
META_DIR="$UNIVERSE_DIR/repo/meta"

INDEX_FILE_NAME="index.json"

echo "\nBuilding index...";
# TODO

echo "OK";

echo "\nCompressing index...";
gzip -c "$META_DIR/$INDEX_FILE_NAME" > "$META_DIR/$INDEX_FILE_NAME.gz";

echo "OK";

