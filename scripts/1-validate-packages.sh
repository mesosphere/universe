#! /bin/sh
set -o errexit -o nounset -o pipefail

SCRIPTS_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )";
REG_DIR="$SCRIPTS_DIR/..";
PKG_DIR=$REG_DIR/repo/packages
SCHEMA_DIR=$REG_DIR/repo/meta/schema

validate () {
  query=$1;
  schema=$2;
  for file in $(find $PKG_DIR -name $query); do
    echo "Validating $file";
    jsonschema -i $file $schema
  done
}

echo "Validating package definitions...";

# validate all command.json files
validate "command.json" "$SCHEMA_DIR/command-schema.json";

# validate all marathon.json files
# TODO: ignore or resolve the moustache values to make this pass
# validate "marathon.json" "$SCHEMA_DIR/marathon-schema.json";

# validate all package.json files
validate "package.json" "$SCHEMA_DIR/package-schema.json";

echo "OK";

