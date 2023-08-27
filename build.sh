#!/bin/bash

python src/rcvresults/demo.py
mkdir tmp
cp data/output-html/*.html tmp
cp -R data/output-html/rcv-snippets tmp/rcv-snippets
rm tmp/index-test.html