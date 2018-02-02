#!/bin/bash
# Script takes a provided stub-universe json file and extracts it contents into a format usable by the local-universe (or other universe) build processes.
# Author: Justin Lee (jlee@mesosphere.com)
# Udpated: Richard Shaw (rshaw@mesosphere.com) 020218
# Version: 0.2
# Example usage (from the universe/docker/local-universe directory)
#       bash add-stub-universe.sh -j custom.json
#       bash add-stub-universe.sh -u https://hostname/custom-online.json
#       cp -rpv stub-repo/packages/* ../../repo/packages
set -e 
set -u
set -o pipefail

function print_usage() {
    echo "Usage: "
    echo "  add-stub-universe -j <stub-universe-json>"
    echo "or"
    echo "  add-stub-universe -u <stub-universe-json-url>"
}

if [[ -z "${1-}" || -z "${2-}" ]]; then
    print_usage
    exit 1
fi

if [[ $(uname -s) == Linux ]]; then
    BASE64="base64 -d"
else
    BASE64="base64 -D"
fi

mkdir -p stub-repo/packages
mkdir -p stub-repo/tmp

if [[ "$1" == "-u" ]]; then
    cd stub-repo/tmp && curl -LO "$2" && cd -
    FILE=stub-repo/tmp/$(basename $2)
elif [[ "$1" == "-j" ]]; then
    FILE=$2
else
    print_usage
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
[[ $(cat stub-repo/$PACKAGE.json | jq '.command') = "null"  ]] || cat stub-repo/$PACKAGE.json | jq '.command' > stub-repo/packages/${LETTER}/${PACKAGE}/0/command.json
cat stub-repo/$PACKAGE.json | jq 'del(.command, .marathon, .resource, .config, .releaseVersion)' > stub-repo/packages/${LETTER}/${PACKAGE}/0/package.json
cat stub-repo/$PACKAGE.json | jq -r '.marathon.v2AppMustacheTemplate' | ${BASE64} > stub-repo/packages/${LETTER}/${PACKAGE}/0/marathon.json.mustache

done

echo ""
echo "Full stub-repo contents:"
ls -alh stub-repo/packages/*/*/*

echo ""