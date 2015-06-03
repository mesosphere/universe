#!/bin/bash
set -o errexit -o nounset -o pipefail

SCRIPTS_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )";
UNIVERSE_DIR="$SCRIPTS_DIR/..";
SCHEMA_DIR=$UNIVERSE_DIR/repo/meta/schema

echo "Validating version...";
jsonschema -i $UNIVERSE_DIR/repo/meta/version.json $SCHEMA_DIR/version-schema.json;

echo "OK";


