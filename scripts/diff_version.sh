#!/bin/bash
set -o errexit -o nounset -o pipefail


if [ "$#" -ne 3 ]; then
  echo "Usage: $0 package-name revision1 revision2 (e.g., nexus 3 4)" >&2
  exit 1
fi

SCRIPTS_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )";
REPO_DIR=$SCRIPTS_DIR/../repo/packages

echo "Diffing package $1 revision $2 revision $3"

# get capital first letter for directory name
FIRSTCHAR=`echo $1 | cut -c1-1 | tr [:lower:] [:upper:]`

for f in ${REPO_DIR}/$FIRSTCHAR/$1/$2/*
do
        BASE_NAME=$(basename $f)
	echo ""
	echo ""
	echo "Diffing File $BASE_NAME:"
	diff ${REPO_DIR}/$FIRSTCHAR/$1/$2/$BASE_NAME ${REPO_DIR}/$FIRSTCHAR/$1/$3/$BASE_NAME || true 
done


