$SCRIPTS_DIR = Split-Path $script:MyInvocation.MyCommand.Path
$UNIVERSE_DIR = Split-Path $SCRIPTS_DIR
$PKG_DIR="$UNIVERSE_DIR\repo\packages"
$SCHEMA_DIR="$UNIVERSE_DIR\repo\meta\schema"
Function validate {
  param($query, $schema)

  $query_files = Get-ChildItem $PKG_DIR -filter "$query" -Recurse | Select-Object -ExpandProperty FullName
  Foreach ($file in $query_files) {
  jsonschema -i $file $schema
  }
}
echo "Validating package definitions..."

# validate all command.json files
validate "command.json" "$SCHEMA_DIR/command-schema.json"

# validate all config.json files
validate "config.json" "$SCHEMA_DIR/config-schema.json"

# validate all package.json files
validate "package.json" "$SCHEMA_DIR/package-schema.json"

echo "OK"
