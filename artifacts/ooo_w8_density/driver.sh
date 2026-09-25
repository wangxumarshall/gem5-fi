#!/bin/bash
# W8.2/W8.3/W8.5 event-density measurement driver (event_coverage counting).
# No-fault golden runs + read-only CHAOSProbe (W0.3a), thresholds matching
# the injector event gates: ROB>80%, IQ>80%, flInt<=8, (flVec<=6 default;
# separate le0 runs for the D75 threshold-0 gate). 2 reps per binary for
# determinism. HARD BUDGET: 2 concurrent gem5 (Wave B holds 8 jobs).
cd /home/sdc/gem5-fi || exit 1
D=artifacts/ooo_w8_density
mkdir -p "$D"
JOBS=/tmp/ooo_w8_density_jobs.txt
: > "$JOBS"

add() { # name binpath [extra probe args...]
  local name=$1 binpath=$2; shift 2
  local out="$D/$name"
  if [ -f "$out/stats.txt" ]; then echo "SKIP $name (stats.txt exists)" >> "$D/driver.log"; return; fi
  echo "PYTHONHASHSEED=0 build/ARM/gem5.opt --outdir=$out configs/se/ooo_proxy.py --cmd workloads/ooo/$binpath --cpu O3 --chaos_probe $* > $out.out 2> $out.err; echo \"DONE $name rc=\$? wall=\$SECONDS\" >> $D/driver.log" >> "$JOBS"
}

add branch_mispred_r2 branch_mispred/branch_mispred
add coremark_r1 coremark/coremark
add coremark_r2 coremark/coremark
add crc32_r1 embench/crc32/crc32
add crc32_r2 embench/crc32/crc32
add matmult_int_r1 embench/matmult-int/matmult-int
add matmult_int_r2 embench/matmult-int/matmult-int
add md5sum_r1 embench/md5sum/md5sum
add md5sum_r2 embench/md5sum/md5sum
add minver_r1 embench/minver/minver
add minver_r2 embench/minver/minver
add nbody_r1 embench/nbody/nbody
add nbody_r2 embench/nbody/nbody
add wikisort_r1 embench/wikisort/wikisort
add wikisort_r2 embench/wikisort/wikisort
add dep_chain_r1 dep_chain/dep_chain
add dep_chain_r2 dep_chain/dep_chain
add dep_chain_vec_r1 dep_chain/dep_chain_vec
add dep_chain_vec_r2 dep_chain/dep_chain_vec
add dep_chain_vec_le0_r1 dep_chain/dep_chain_vec --probe_fl_vec_le 0
add dep_chain_vec_le0_r2 dep_chain/dep_chain_vec --probe_fl_vec_le 0
add rob_fill_r1 rob_fill/rob_fill
add rob_fill_r2 rob_fill/rob_fill
add rob_fill_fp_r1 rob_fill/rob_fill_fp
add rob_fill_fp_r2 rob_fill/rob_fill_fp
add gap_r1 gap/gap
add gap_r2 gap/gap
add gemm_r1 polybench/gemm/gemm
add gemm_r2 polybench/gemm/gemm
add lu_r1 polybench/lu/lu
add lu_r2 polybench/lu/lu
add cholesky_r1 polybench/cholesky/cholesky
add cholesky_r2 polybench/cholesky/cholesky
add jacobi2d_r1 polybench/jacobi-2d/jacobi-2d
add jacobi2d_r2 polybench/jacobi-2d/jacobi-2d
add jpeg_wl_r1 libjpeg/jpeg_wl
add jpeg_wl_r2 libjpeg/jpeg_wl

echo "driver start $(date)" >> "$D/driver.log"
n=0
while IFS= read -r cmd; do
  [ -z "$cmd" ] && continue
  while [ "$(jobs -rp | wc -l)" -ge 2 ]; do sleep 5; done
  SECONDS=0
  bash -c "$cmd" &
  n=$((n+1))
done < "$JOBS"
wait
echo "driver done $(date) jobs=$n" >> "$D/driver.log"
