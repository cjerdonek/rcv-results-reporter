#!/bin/bash
#
# Build the demo to an output directory.
#
# Usage:
#
#   $ ./build-demo.sh BUILD_DIR
#

BUILD_DIR=$1

# Exit if a command fails.
set -e

if [ -z "${BUILD_DIR}" ]
then
    echo "error: BUILD_DIR not provided" >&2
    exit 1
fi

# We want the datetime that's displayed to be in the Pacific timezone.
export TZ=America/Los_Angeles
BUILD_TIME="$(date +"%Y-%m-%dT%H:%M:%S")"

# See here for CircleCI's built-in environment variables:
# https://circleci.com/docs/variables/#built-in-environment-variables
python src/rcvresults/scripts/build_demo.py \
  --html-output-dir "${BUILD_DIR}" \
  --build-time "${BUILD_TIME}" \
  --commit-hash "${CIRCLE_SHA1}"

rm "${BUILD_DIR}/index-test.html"
# Copy the non-html files.
cp data/output-html/default.css "${BUILD_DIR}"
# The -L flag resolves resolves symlinks.
cp -RL data/output-html/js "${BUILD_DIR}"

echo "build-demo.sh succeeded!" >&2
