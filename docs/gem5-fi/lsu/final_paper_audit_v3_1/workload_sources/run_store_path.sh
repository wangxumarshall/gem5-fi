#!/bin/bash
set -e
ROOT=/home/sdc/gem5-fi-ding
OUT=${1:-/tmp/gem5_store_path}
$ROOT/build/ARM/gem5.opt --outdir=$OUT $ROOT/configs/se/lsu_proxy.py --cmd=$ROOT/docs/gem5-fi/lsu/final_paper_audit_v3_1/workload_sources/store_path --cpu O3 --variant B0
