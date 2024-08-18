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

# This is for the static-file assets (js and css) for the **top-level** page.
# The RCV-specific assets go in ${BUILD_DIR}/static-files-rcv.
STATIC_FILES_DIR="${BUILD_DIR}/static-files"

# See here for CircleCI's built-in environment variables:
# https://circleci.com/docs/variables/#built-in-environment-variables
python src/rcvresults/scripts/build_demo.py \
  --html-output-dir "${BUILD_DIR}" \
  --template-vars config/template-contexts-demo-ci.yml \
  --build-time "${BUILD_TIME}" \
  --commit-hash "${CIRCLE_SHA1}"

rm "${BUILD_DIR}/index-test.html"

mkdir "${STATIC_FILES_DIR}"
# Here, leaving the slash off the end of the source directory causes
# the directory **itself** to be created in and copied into the build
# directory.
cp -R data/election-htmls/2024-03-05/js "${STATIC_FILES_DIR}"
cp -R data/election-htmls/2024-03-05/styles "${STATIC_FILES_DIR}"
# Here, leaving the slash off the end of the source directory causes
# the directory **itself** to be created at the directory path specified
# by the target directory argument (and its contents recursively copied).
cp -R static-files "${BUILD_DIR}/static-files-rcv"

echo "build-demo.sh succeeded!" >&2
