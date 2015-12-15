#!/bin/bash
set -o errexit -o nounset -o pipefail

SCRIPTS_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )";
UNIVERSE_DIR="$SCRIPTS_DIR/..";
PKG_DIR=$UNIVERSE_DIR/repo/packages
SCHEMA_DIR=$UNIVERSE_DIR/repo/meta/schema

validate () {
  query=$1;
  schema=$2;
  for file in $(find $PKG_DIR -name $query); do
    package=${file/$PKG_DIR/}
    echo "- $package"
    jsonschema -i $file $schema
    $SCRIPTS_DIR/json_dup_key_check.py $file
  done
}

echo "Validating package definitions...";

# validate all command.json files
validate "command.json" "$SCHEMA_DIR/command-schema.json";

# validate all config.json files
validate "config.json" "$SCHEMA_DIR/config-schema.json";

# validate all package.json files
validate "package.json" "$SCHEMA_DIR/package-schema.json";

# validate all resource.json files
validate "resource.json" "$SCHEMA_DIR/resource-schema.json";

echo "OK";
