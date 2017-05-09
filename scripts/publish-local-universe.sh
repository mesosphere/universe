#!/bin/bash
set -o errexit -o nounset -o pipefail

SCRIPTS_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
REPO_BASE_DIR=${SCRIPTS_DIR}/..

S3_DEPLOY_BUCKET="s3://downloads.mesosphere.com/universe/public/"

echo "Uploading local universe to: ${S3_DEPLOY_BUCKET}"
aws s3 cp --region us-east-1 "${REPO_BASE_DIR}"/docker/local-universe/local-universe.tar.gz "${S3_DEPLOY_BUCKET}"
