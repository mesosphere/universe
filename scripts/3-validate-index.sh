#!/bin/bash
set -o errexit -o nounset -o pipefail

SCRIPTS_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )";
UNIVERSE_DIR="$SCRIPTS_DIR/..";
SCHEMA_DIR=$UNIVERSE_DIR/repo/meta/schema

echo "Validating index...";
jsonschema -i $UNIVERSE_DIR/repo/meta/index.json $SCHEMA_DIR/index-schema.json;

echo "OK";

