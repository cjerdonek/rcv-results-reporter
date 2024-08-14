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
# The repo has the following symlinks that point to the following
# directories relative to the repo root:
#  * data/demo-pages/static-files     -> data/election-htmls/2024-03-05
# In the cp invocations below, the -L flag resolves symlinks.
#   Here, leaving the slash off the end of the source directory causes
# the directory **itself** to be created in and copied into the build
# directory.
cp -RL data/demo-pages/static-files/js "${BUILD_DIR}"
cp -RL data/demo-pages/static-files/styles "${BUILD_DIR}"
#   Here, leaving the slash off the end of the source directory causes
# the directory **itself** to be created at the directory path specified
# by the target directory argument (and its contents recursively copied).
cp -R static-files "${BUILD_DIR}/static-files-rcv"

echo "build-demo.sh succeeded!" >&2
