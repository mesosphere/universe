#! /bin/sh
set -o errexit -o nounset -o pipefail

SCRIPTS_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )";
REG_DIR="$SCRIPTS_DIR/..";
SCHEMA_DIR=$REG_DIR/repo/meta/schema

echo "Validating index...";
jsonschema -i $REG_DIR/repo/meta/index.json $SCHEMA_DIR/index-schema.json;

echo "OK";

