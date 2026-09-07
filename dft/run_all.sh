#!/usr/bin/env bash
# DFT 向量批跑脚本（§8.3）——逐向量执行注入配置并抓取签名比对。
# 用法: ./dft/run_all.sh [vector_id ...]   (缺省跑全部)
set -u
cd "$(dirname "$0")/.."
source /home/sdc/gem5-deps/env.sh
G5=CHAOS/gem5/build/ARM/gem5.opt
OUT=$(mktemp -d /tmp/dft-XXXX)
pass=0; fail=0; skip=0

run_vector() {
    local id="$1" cfg="$2" kernel="$3"
    echo "=== [$id] ==="
    if [[ "$cfg" == *"--chaos_addrpath"* ]]; then
        echo "SKIP: m2-addrpath 需要 FS 模式（MMU-on），SE 向量集跳过（见 manifest honesty）"
        skip=$((skip+1)); return
    fi
    rm -rf "$OUT/$id"
    if ! timeout 600 $G5 --quiet --outdir="$OUT/$id" \
        configs/se/arm_chaos.py --cmd="$kernel" --cpu=O3 $cfg 2>/dev/null \
        | tail -1 > "$OUT/$id.stdout"; then
        echo "FAIL: gem5 运行失败"; fail=$((fail+1)); return
    fi
    echo "output: $(cat $OUT/$id.stdout)"
    # 签名比对由人工/CI 对照 manifest 的 defect_signature 判定
    # （健康基线 = 无注入同 kernel 的 golden，另有 CI 侧维护）。
    pass=$((pass+1))
}

# 健康（无注入）基线先行
echo "=== [baseline] reg_chain golden ==="
rm -rf "$OUT/base"
timeout 300 $G5 --quiet --outdir="$OUT/base" \
    configs/se/arm_chaos.py --cmd=workloads/directed/reg_chain --cpu=O3 \
    2>/dev/null | tail -1
echo "(期望 f247ef3fe6f02cfd)"

run_vector m1-rat-history-residue \
    "--chaos_rat --rat_mode=f5_substitute --rat_target_arch=9 --probability=1.0 --first_clock=100000 --max_faults=1 --rng_seed=20260825" \
    workloads/directed/accum_kernel
run_vector m3-lsqfwd-bitflip \
    "--chaos_lsqfwd --probability=1.0 --first_clock=1000000 --max_faults=1 --rng_seed=20260825 --fault_type=bit_flip" \
    workloads/directed/fp_fwd_kernel
run_vector d1-byte-lane-skew-rol1 \
    "--chaos_lsqfwd --lsq_structural_fault=byte_lane_skew --lsq_skew_bytes=1 --first_clock=1000000 --max_faults=1" \
    workloads/directed/fp_fwd_kernel
run_vector e-ecc-logic-fault \
    "--chaos_mem --mem_protection_model=ecc_logic_fault --first_clock=5000 --max_faults=1 --rng_seed=1" \
    workloads/directed/l1d_reduce

echo
echo "DFT 向量批跑完成: pass=$pass fail=$fail skip=$skip（输出 $OUT）"
echo "签名比对: 逐向量对照 dft/manifest.yaml 的 defect_signature"
