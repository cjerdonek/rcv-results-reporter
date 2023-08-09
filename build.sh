#!/bin/bash

python src/rcvresults/demo.py
mkdir tmp
cp data/output-html/*.html tmp
rm tmp/index-test.html