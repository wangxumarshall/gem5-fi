#!/bin/sh
set -e
cd "$(dirname "$0")"
gcc -O2 -static sq03_probe.c -o sq03_probe
./sq03_probe > sq03_probe.golden
cat sq03_probe.golden
