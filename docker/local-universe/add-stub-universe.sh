#!/bin/bash
set -e 
set -u
set -o pipefail

if [[ -z "$1" || -z "$2" ]]; then
    echo "Usage: "
    echo "  add-stub-universe -j <stub-universe-json>"
    echo "or"
    echo "  add-stub-universe -u <stub-universe-json>"
    exit 1
fi

mkdir -p stub-repo/packages
mkdir -p stub-repo/tmp

if [[ "$1" == "-u" ]]; then
    cd stub-repo/tmp && curl -LO "$2" && cd -
    FILE=stub-repo/tmp/$(basename $2)
elif [[ "$1" == "-j" ]]; then
    FILE=$2
else
    echo "Usage: "
    echo "  add-stub-universe -j <stub-universe-json>"
    echo "or"
    echo "  add-stub-universe -u <stub-universe-json>"
    exit 1
fi

# FILE=$1
PACKAGES=$(jq -r '.packages[].name' $FILE)

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