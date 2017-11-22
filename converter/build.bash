#!/bin/bash
set -o errexit -o nounset -o pipefail

DOCKER_TAG=${DOCKER_TAG:-"dev"}
DOCKER_IMAGE=${DOCKER_IMAGE:-"mesosphere/universe-converter"}
DOCKER_IMAGE_AND_TAG="${DOCKER_IMAGE}:${DOCKER_TAG}"

CONVERTER_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

function clean {

  rm -rf ${CONVERTER_DIR}/target

}

function build {

  # Check if the jq processor is installed correctly
  if ! command -v jq > /dev/null 2>&1; then
    echo "jq is required. Please install!"
    exit 1
  fi

  mkdir -p ${CONVERTER_DIR}/target

  msg "Building docker image ${DOCKER_IMAGE_AND_TAG}"
  docker build -t "${DOCKER_IMAGE_AND_TAG}" -f converter/Dockerfile .
  msg "Built docker image ${DOCKER_IMAGE_AND_TAG}"

  cat ${CONVERTER_DIR}/marathon.json | jq ".container.docker.image |= \"${DOCKER_IMAGE_AND_TAG}\"" > ${CONVERTER_DIR}/target/marathon.json

  msg "Output written to ${CONVERTER_DIR}/target/marathon.json"

}

function publish {

  docker push "${DOCKER_IMAGE_AND_TAG}"

}

function now { date +"%Y-%m-%d %H:%M:%S" | tr -d '\n' ;}
function println { printf '%s\n' "$(now) $*" ;}
function msg { println "$*" >&2 ;}

######################### Delegates to subcommands or runs main, as appropriate
if [[ ${1:-} ]] && declare -F | cut -d' ' -f3 | fgrep -qx -- "${1:-}"
then "$@"
else build
fi
