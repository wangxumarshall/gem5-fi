#!/bin/bash
set -e
ROOT=/home/sdc/gem5-fi-ding
OUT=${1:-/tmp/gem5_lq_lifetime}
$ROOT/build/ARM/gem5.opt --outdir=$OUT $ROOT/configs/se/lsu_proxy.py --cmd=$ROOT/docs/gem5-fi/lsu/final_paper_audit_v3_1/workload_sources/lq_lifetime --cpu O3 --variant B0
