#!/bin/bash
# Script takes a provided stub-universe json file and extracts it contents into a format usable by the local-universe (or other universe) build processes.
# Author: Justin Lee (jlee@mesosphere.com)
# Version: 0.1
# Example usage (from the universe/docker/local-universe directory)
#       bash add-stub-universe.sh edgelb.json
#       bash add-stub-universe.sh edgelb-pool.json
#       cp -rpv stub-repo/packages/* ../../repo/packages
set -e 
set -u
set -o pipefail

if [[ -z "$1" ]]; then
    echo "Usage: add-stub-universe.sh <stub-universe-json>"
    exit 1
elif [[ ! -f "$1" ]]; then
    echo "File '$1' does not exist"
    exit 1
fi

mkdir -p stub-repo/packages

FILE=$1
PACKAGES=$(jq -r '.packages[].name' $1)

for PACKAGE in $PACKAGES; do
echo "Building repo structure for $PACKAGE..."
LETTER=$(echo $PACKAGE | head -c 1 | tr '[:lower:]' '[:upper:]')
mkdir -p stub-repo/packages/${LETTER}/${PACKAGE}/0

jq --arg PACKAGE "$PACKAGE" '.packages[] | select(.name == $PACKAGE)' $FILE > stub-repo/$PACKAGE.json

cat stub-repo/$PACKAGE.json | jq '.config'  > stub-repo/packages/${LETTER}/${PACKAGE}/0/config.json
cat stub-repo/$PACKAGE.json | jq '.resource' > stub-repo/packages/${LETTER}/${PACKAGE}/0/resource.json
cat stub-repo/$PACKAGE.json | jq '.command' > stub-repo/packages/${LETTER}/${PACKAGE}/0/command.json
cat stub-repo/$PACKAGE.json | jq 'del(.command, .marathon, .resource, .config, .releaseVersion)' > stub-repo/packages/${LETTER}/${PACKAGE}/0/package.json
cat stub-repo/$PACKAGE.json | jq -r '.marathon.v2AppMustacheTemplate' | base64 -D > stub-repo/packages/${LETTER}/${PACKAGE}/0/marathon.json.mustache

done

echo ""
echo "Full stub-repo contents:"
ls -alh stub-repo/packages/*/*/*

echo ""
