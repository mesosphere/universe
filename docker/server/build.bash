#!/bin/bash
set -o errexit -o nounset -o pipefail

function globals {
  export LC_ALL=en_US.UTF-8
  export LANG="$LC_ALL"
}; globals

DOCKER_TAG=${DOCKER_TAG:-"dev"}
DOCKER_IMAGE=${DOCKER_IMAGE:-"universe-server"}
DOCKER_IMAGE_AND_TAG="${DOCKER_IMAGE}:${DOCKER_TAG}"

DOCKER_SERVER_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"


function clean {

  rm -rf ${DOCKER_SERVER_DIR}/target

}

function prepare {

  local universeBuildTarget="${DOCKER_SERVER_DIR}/../../target"

  if [[ -f ${universeBuildTarget}/repo-empty-v3.json ]]; then
    cp -r ${DOCKER_SERVER_DIR}/../../target ${DOCKER_SERVER_DIR}
  else
    err "Please run scripts/build.sh before trying to build universe server"
  fi


}

function gzipJsonFiles {(

  prepare

  cd ${DOCKER_SERVER_DIR}/target

  for f in $(ls -1 *.json); do
    msg "GZipping $f"
    gzip -f -k "${f}"
    sizeOrig=$(stat -c "%s" "${f}")
    sizeGZip=$(stat -c "%s" "${f}.gz")
    msg "GZipped $f [${sizeOrig} B -> ${sizeGZip} B]"

    if [ ${sizeOrig} -le ${sizeGZip} ]; then
      msg "GZipped file ${f}.gz is larger than its original file, discarding"
      rm "${f}.gz"
    fi
  done

)}



function build {(

  gzipJsonFiles

  cd ${DOCKER_SERVER_DIR}

  msg "Building docker image ${DOCKER_IMAGE_AND_TAG}"
  docker build -t "${DOCKER_IMAGE_AND_TAG}" .
  msg "Built docker image ${DOCKER_IMAGE_AND_TAG}"

  cat marathon.json | jq ".container.docker.image |= \"${DOCKER_IMAGE_AND_TAG}\"" > target/marathon.json

  msg "marathon.json output to ${DOCKER_SERVER_DIR}/target/marathon.json"

)}

function publish {

  docker push "${DOCKER_IMAGE_AND_TAG}"

}

function now { date +"%Y-%m-%d %H:%M:%S" | tr -d '\n' ;}
function msg { println "$*" >&2 ;}
function err { local x=$? ; msg "$*" ; return $(( $x == 0 ? 1 : $x )) ;}
function println { printf '%s\n' "$(now) $*" ;}
function print { printf '%s ' "$(now) $*" ;}

######################### Delegates to subcommands or runs main, as appropriate
if [[ ${1:-} ]] && declare -F | cut -d' ' -f3 | fgrep -qx -- "${1:-}"
then "$@"
else build
fi
