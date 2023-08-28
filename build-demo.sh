#!/bin/bash
#
# Build the demo to an output directory.
#
# Usage:
#
#   $ ./build.sh BUILD_DIR
#

BUILD_DIR=$1

# TODO: pass BUILD_DIR into demo.py.
python src/rcvresults/demo.py
mkdir -p "${BUILD_DIR}"
cp data/output-html/*.html "${BUILD_DIR}"
rm "${BUILD_DIR}/index-test.html"
cp -R data/output-html/rcv-snippets "${BUILD_DIR}/rcv-snippets"
# Copy the non-html files.
cp data/output-html/default.css "${BUILD_DIR}"
# The -L flag resolves resolves symlinks.
cp -RL data/output-html/js "${BUILD_DIR}"
