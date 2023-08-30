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

python src/rcvresults/demo.py --html-output-dir "${BUILD_DIR}"
rm "${BUILD_DIR}/index-test.html"
# Copy the non-html files.
cp data/output-html/default.css "${BUILD_DIR}"
# The -L flag resolves resolves symlinks.
cp -RL data/output-html/js "${BUILD_DIR}"

echo "build-demo.sh succeeded!" >&2
