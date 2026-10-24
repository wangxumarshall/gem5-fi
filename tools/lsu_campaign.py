#!/usr/bin/env python3
"""LSU campaign orchestrator (09 W10) — model resolution + adaptive-sampling engine.

Reads 07-expanded-matrix.csv (337 cells), resolves every cell to either a
runnable gem5 command or an honest BLOCKED/DEFERRED/N-A classification
(README §8.3: blocked is marked, never silently skipped), runs each runnable
cell with the three-phase adaptive sampling from 05 r12-r15:
  Phase 1 (trial): 30 activated — discover injector errors / all-Crash /
                   zero-activation units (05 r13)
  Phase 2 (screening): >=385 activated (95% CI, ±5pp) — cell pass/fail
  Phase 3 (main): sequential until Wilson 95% half-width <=2pp or 5000
                   activated (05 r14/r15)

Per-run classification via tools/lsu_l5_classify.py (L5 conservation).

MODEL->INJECTOR MAPPING PROVENANCE (git-verified, 2026-09-26):
  A-series   W4 9fbec314 (dual-hook 7-mode family on CHAOSAddrPath)
  S/L-series W5 c7743989..a0ecfd20 (pre-hook family + lsqfwd modes + l03)
  C-series   W6 65e5d022..2b967a9b (CHAOSCache targetField/faultType)
  P-series   W8 (this branch, f76f5632 CHAOSPrefetch)
  O-series   W8 (this branch, 1b97b714 ExMon O01/O02 + existing stxr modes)
HONEST DEFERRED (notify-only event sources, consumer-side corruption NOT
implemented — W5/W6 wired chaosLsuF6Notify call sites only): S10, L04,
C11, C12, C14, C15. No-clean-hook deferred: A07, P06, O04, O09.
B0 protection rows (09 §6.4 — not applicable, never zero-filled):
S12, T09, C13, O08.

Usage:
  python3 tools/lsu_campaign.py --matrix docs/gem5-fi/lsu/07-expanded-matrix.csv \
      --outdir runs/lsu --max-parallel 4 [--cells A01-F0-W3,...] [--dry-run]
"""
import argparse
import csv
import json
import os
import signal
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
G5 = REPO / "build/ARM/gem5.opt"
LSU_PROXY = REPO / "configs/se/lsu_proxy.py"
L5 = REPO / "tools/lsu_l5_classify.py"


def resolve_g5(env=None):
    """gem5 binary for campaign runs.

    Precedence: $LSU_GEM5_BIN (the worktree convention — a worktree has no
    repo-root build/, cf. tools/lsu_runner.py) → repo-root build/ARM/gem5.opt.
    Loud SystemExit when neither exists: a campaign that silently ran the
    wrong binary is the stale-binary failure mode this repo has been bitten
    by twice (CLAUDE.md: a stale duplicate once caused fake segfaults).
    """
    import os
    env = os.environ if env is None else env
    cand = env.get("LSU_GEM5_BIN")
    path = Path(cand) if cand else G5
    if not path.exists():
        raise SystemExit(
            "[campaign] gem5 binary not found: %s — set LSU_GEM5_BIN to a "
            "built gem5.opt (worktrees build at CHAOS/gem5/build/ARM/gem5.opt)"
            % path)
    return path


def fs_dir(env=None):
    """Directory holding the FS images (vmlinux / ubuntu.img / boot.arm64).

    A worktree does not carry the ~3 GB gem5-fs/ submodule, so the assets are
    REUSED from wherever they exist: $LSU_FS_DIR → <repo>/gem5-fs. Same
    discipline as LSU_GEM5_BIN (and item 四.2 of the 2026-10-20 instruction:
    inventory the existing kernel/disk/bootloader/checkpoint and reuse them).
    """
    import os
    env = os.environ if env is None else env
    d = env.get("LSU_FS_DIR")
    return Path(d) if d else (REPO / "gem5-fs")


def fs_asset(name, env=None):
    return fs_dir(env) / name


def wl_binary_path(binary):
    """[MDSPEC][R4-8-W1] Workload binary -> real path, directed-first.

    The 9 directed W9 carriers live in workloads/directed/<binary>; the W1
    MiBench-TC23 carrier lives at workloads/mibench/bin/w1_all (i.e. a
    subdirectory of workloads/, NOT of workloads/directed/). resolve_cell
    used to hardcode the directed prefix, so an unblocked W1 cell would have
    been launched with a NON-EXISTENT --cmd path. Same directed-then-root
    fallback as lsu_runner._wl_path (the two drivers must not drift).
    """
    p = REPO / "workloads" / "directed" / binary
    return p if p.exists() else REPO / "workloads" / binary


# [MDSPEC][R4-8-W1] Per-workload SE wall-clock budget. The campaign's generic
# --timeout (300 s) is calibrated for the directed W9 carriers (golden 10-40 s);
# the W1 MiBench-TC23 golden measured 7.44-7.51 h (F-050), so 300 s would kill
# every W1 run as a FABRICATED Timeout (injected=0). lsu_runner.TIMEOUTS
# already freezes SE_W1=43200 s for exactly this reason; the campaign reuses
# the same constant so the two drivers agree (no drift, no silent fake Timeout).
SE_W1_TIMEOUT = 43200

# [LSU][R6-CAMPAIGN] Per-run wall-clock budgets. The FS default was 1800 s,
# which silently killed FS runs that legitimately needed longer on this
# checkpoint (classified Timeout with only a salvaged prefix). 2700 s is the
# KNOWN-GOOD budget — runs given `--fs-timeout 2700` terminated cleanly with a
# complete stream + stats.txt. Both defaults are surfaced (never silently
# lowered): the effective value lands in every per-seed entry and the cell
# result (timeout_budget / timeout_seconds) and prints on the cell line.
FS_TIMEOUT_DEFAULT = 2700
SE_TIMEOUT_DEFAULT = 300


def require_fs_assets():
    """Hard-fail (with the reuse hint) when the FS images are absent."""
    missing = [str(p) for p in (fs_asset("vmlinux"), fs_asset("ubuntu.img"),
                                fs_asset("boot.arm64")) if not p.exists()]
    if missing:
        raise SystemExit(
            "[campaign] FS assets missing: %s — set LSU_FS_DIR to the "
            "directory holding vmlinux/ubuntu.img/boot.arm64 (the main tree's "
            "gem5-fs/ works from a worktree)." % ", ".join(missing))


def propagation_flags(runid, seed):
    """[MDSPEC][H0] per-SAMPLE propagation-trace flags.

    Every campaign sample attaches CHAOSPropagation and stamps its identity,
    so propagation evidence comes from the OFFICIAL entry point, not only
    from hand-driven lsu_proxy invocations. prop_sample_run_id = the sample
    index within the RunID (spec sheet 11 requires run_id + sample_run_id on
    every event); prop_evt.txt.gz lands in the seed dir (= gem5 --outdir).
    """
    return ["--chaos_propagation",
            "--prop_run_id", str(runid),
            "--prop_sample_run_id", "s%d" % int(seed)]

sys.path.insert(0, str(Path(__file__).resolve().parent))
from wilson import wilson_ci  # repo's single Wilson impl (no drift)

# Expanded matrix column indices (0-based; col 0 = "Excel行")
COL_RUNID = 1     # RunID like A01-F0-W3
COL_MODEL = 2     # Model ID like A01
COL_UNIT = 3      # Unit like AGU
COL_FREQ = 7      # Frequency tier F0-F6
COL_WORKLOAD = 9  # Workload name

# ---------------------------------------------------------------- workloads
# W9 SE-testable binaries (all gem5==native, goldens in runner.py GOLDEN_IDS).
WL_BINARY = {
    "MiniCheck": "mini_check",
    "AGU-AddrModes": "agu_addrmodes",
    "SQ-Forward": "sq_forward",
    "Cache-DirtyEvict": "cache_dirtyevict",
    "Prefetch-Stride": "prefetch_stride",
    "STREAM+PointerChase": "stream_chase",
    "BEEBS-DelayAVF": "beebs_kernels",
    "GAP/Graph500": "gap_bfs",
    "SQLite": "sqlite_like",
    # [LSU][W1-REG] DR-001 D+A（2026-10-11 注册）：MiBench-TC23 十件套单进程
    # 载体（F-050 三次 golden 闭环，oracle 规范哈希 5bb9298a…75245b）。
    # golden = sha256(8 个 fnv1a64 行 join+尾换行)[:16]——g1/g2/g3/原生 all_A
    # 四方实证恒等 6dab8ec221c46677（分类器 W1 派生回退同算法）。
    "MiBench-TC23": "mibench/bin/w1_all",
}
GOLDENS = {
    "mini_check": "07568da9f3ad5665",
    "agu_addrmodes": "728e604ffcec539d",
    "sq_forward": "1f4cbf14327717df",
    "cache_dirtyevict": "062e5124df3667f9",
    "prefetch_stride": "629727c0ad9ca8ef",
    "stream_chase": "50ab96a7fe8f6ec2",
    "beebs_kernels": "a10b9827edd8a9fb",
    "gap_bfs": "030921682b3731f2",
    "sqlite_like": "33f836327a416d35",
    "mibench/bin/w1_all": "6dab8ec221c46677",
}
# Workload-level structural blocks (README §8.3 — W4/W7/W13, plus
# SPEC-license W11). Matched by keyword on the workload column.
#
# [MDSPEC][R4-8-W1] "MiBench" was REMOVED from this table (2026-10-22). Its
# old reason ("fs-infra: SE has no MiBench FS pipeline") was factually wrong:
# the W1 MiBench-TC23 carrier has an SE binary + a frozen golden AND a legal
# SE run path, all verified on disk —
#   * binary  workloads/mibench/bin/w1_all (ELF aarch64, static, 938232 B);
#   * golden  6dab8ec221c46677 (runner.py GOLDEN_IDS + lsu_w1_rerun's frozen
#     5-way-equal manifest docs/gem5-fi/lsu/evidence/golden_w1_all_manifest.json,
#     canonical sha256 5bb9298aa1100edd…75245b);
#   * path    SE (the campaign's own SE branch; lsu_w1_rerun already drove 15
#     items on this carrier) — no FS is required.
# The machine-readable runid_map generator (tools/lsu_runid_map.py
# _resolve_workload) already resolved these 19 cells as runnable (WL_BINARY
# precedes WL_BLOCKED there), so the static table was the ONLY thing refusing
# them — the exact 口径 conflict recorded in round4_findings.md §R4-6.0 §0.5.
# Removing the key does NOT change any T-model (FS-family) cell: those `continue`
# past every non-SPEC key and resolve to the armtlb FS flag set either way
# (T01/T02/T10 W1 rows are unchanged — asserted in tests/test_lsu_fs_infra.py).
# Kept blockers are precise: TLB-AliasPerm (needs FS), Atomic-Litmus/PARSEC
# (need multi-core FS), SPEC (needs a license).

# [R4-8-INT 语义合并] 与 r4-8-spec-residual 的 W11 粒度订正并集（两侧不冲突）：
# Workload-level structural blocks (README §8.3 — 65 cells on W1/W4/W7/W13,
# plus SPEC-license W11). Matched by keyword on the workload column.
#
# [LSU][MDSPEC][R4-8-SPEC] W11 granuality audit (2026-10-22). The W11 cells'
# spec workload name is byte-identical on all 12 rows — "SPEC CPU2017 采样区间"
# (sheet 6/7 W11 = "选择 mcf、omnetpp、xalancbmk、lbm 的固定 SimPoint/
# checkpoint；不跑全程", purpose "外部有效性；主结论之后复核"). So the block is
# on a workload IDENTITY the spec pins, NOT a blanket model-level gap: the four
# W11 models (C15/L04/S13/T10) each already own runnable non-W11 cells on
# open-source SE carriers (W5/W6/W10/W12), i.e. the blocker adds no model
# coverage — it withholds the licensed SPEC data set only. The match key is
# therefore narrowed from the bare substring "SPEC" to the pinned identity
# "SPEC CPU2017" (strictly more precise; all 12 W11 rows still match, no other
# row in the 325-RunID matrix contains "SPEC CPU2017" — see
# tests/test_lsu_w11_spec_residual.py). Substitution verdict: an open-source
# carrier would silently re-identify a SPEC cell, so the SPEC license gap stays
# an external blocker (the licensed binaries/inputs + SimPoint set are not on
# disk — audited by find; see R4-8-SPEC-residual-report.md §A.c).
# [LSU][MDSPEC][R4-8-SPEC] The W11 workload identity the spec pins (sheet 6/7).
# Named once so the block table and resolve_cell's FS-family special-case
# cannot drift apart — the earlier bare key "SPEC" + literal `key == "SPEC"`
# comparison in resolve_cell was exactly that drift trap: narrowing the key
# without the comparison silently made T10-F{0,1,2}-W11 resolve to the
# fs:tlb_probe carrier instead of the license refusal (caught by
# tests/test_lsu_w11_spec_residual.py A4).
SPEC_WL_IDENTITY = "SPEC CPU2017"

WL_BLOCKED = {
    "TLB-AliasPerm": "blocked(fs-infra: TLB workload needs FS)",
    # [R4-8-INT 语义合并] 两侧都改写了 WL_BLOCKED 的取值，取并集：
    # * Atomic-Litmus / PARSEC：采 r4-9-fsmc-a 的**实测**理由（多核 FS 基础设施
    #   已落地并真机跑通，故"没有多核 FS"不再是事实；保留 'multicore-fs:'
    #   前缀是有意的——lsu_blocked_triage.py 用正则 r"multicore" 做互斥分类，
    #   去前缀会让这些格子掉出 FS-MULTICORE 桶 = 静默解锁，本轮明令禁止）。
    # * SPEC：保留 r4-8-spec-residual 收窄后的具名键 SPEC_WL_IDENTITY
    #   （Agent6 的分支早于该收窄，仍写裸 "SPEC"）。
    "Atomic-Litmus": ("blocked(multicore-fs: 载体已就绪——2 核 Ruby/CHI FS "
                      "+ 仓库本地 freestanding litmus（O01/O02/O03 的 F0/F5 "
                      "格已 routable，见 tools/lsu_fsmc_verdict.py）；本格不在 "
                      "该模型×档位亲和集合内：C08 是注入器宿主互斥，"
                      "O04-O09 是模型语义未实现。见 R4-9-FSMC-A 报告 §4)"),
    "PARSEC": ("blocked(multicore-fs: W13 负载身份——PARSEC(dedup/ferret/"
               "streamcluster) **开源（不是授权障碍）但本仓库不可得**：find 实证"
               "只有 gem5 上游测试脚手架 CHAOS/gem5/tests/gem5/parsec_benchmarks/，"
               "而它默认被禁用（PARSEC disk image is too big）、valid_hosts="
               "(host_x86_64_tag,) 仅 x86_64 宿主、需 --resource-directory 指向"
               "预编译镜像 + KVM；无源码/输入集/aarch64 构建。另叠加各自的模型/宿主"
               "缺口（O09 缺 RMW operand hook；P09 的 dirty-evict 走 classic "
               "CHAOSCache，与'多线程真实应用'语义构造性互斥）；替代负载会改写格子"
               "定义 ⇒ 规格级决定。见 R4-9-FSMC-A 报告 §5)"),
    SPEC_WL_IDENTITY: "blocked(spec-license: SPEC CPU2017 needs a license)",
}

# ---------------------------------------------------------------- models
# model -> (family, extra_flags). The family decides the trigger-tier flags
# and the seed flag; tier value comes from the cell's F column.
#   addrpath family: bit-level A01-A03 ride --addrpath_mode; the PRE family
#     (A04-A06/A08 + S04-S07/S11/S13 + L01/L02) rides --agu_pre_mode at the
#     LSQ::pushRequest entry hook (W1 ⑦ ruling).
#   lsqfwd family: S01-S03/S08/S09 data/forwarding modes + L03 flag.
#   cache family: CHAOSCache on l1d-cache-0 (legacy firstClock/probability/
#     maxFaults mechanism — lsuTier params are wire-ready, NOT consumed yet;
#     honest approximation documented per-cell in the backfill notes).
#   prefetch family: CHAOSPrefetch (W8, f76f5632).
#   exmon family: CHAOSExMon (legacy window path; O-cells are workload-
#     blocked anyway — wire-verification vehicle only).
MODEL_FLAGS = {
    # --- AGU (W4 9fbec314) ---
    "A01": ("addrpath", ["--addrpath_mode", "a01_bit"]),
    "A02": ("addrpath", ["--addrpath_mode", "a02_2bit"]),
    "A03": ("addrpath", ["--addrpath_mode", "a03_stuck0"]),  # stuck1 by seed parity (note)
    "A04": ("addrpath", ["--agu_pre_mode", "a04_subst"]),
    "A05": ("addrpath", ["--agu_pre_mode", "a05_shift"]),
    # [LSU][MDSPEC][A6] A06（规格名，2026-10-19 计划 §2 裁决 + R4-6-A06
    # 2026-10-22 load 侧落地 + R4-8-A06 2026-10-22 load shrink 落地）：
    # a06_size = A06-a，按 op-class 的合法包络 —— store 侧任意合法目标；
    # load 侧**任意另一合法值**（--agu_size_to_load；widen 或 shrink 都合法，
    # 与规格 "替换为另一合法组合" 一致）。shrink 的安全性由定宽完成合同的
    # **缓冲下限**提供（DynInst::chaosA06BufBytes；见 CHAOSAddrPath.hh）。
    # 本路由 target=8：实宽 1/2/4 的 load 加宽到 8，实宽 16 的向量 load 收缩到
    # 8（实宽 8 的 load 落在 NoChange 拒斥），故 carrier 内的访存可同时覆盖
    # widen 与 shrink 两个方向。
    # 旧名 a06s_store_size 仍为被拒别名（不得私改模型 ID，无 A06S RunID 族）。
    # A06 RunID 保持 MODEL_BLOCKED：shrink 路径只到 COMPILE-UNVERIFIED
    # （待集成构建），解除要 §2.c spike 的**真实 gem5 运行**断言。
    "A06": ("addrpath", ["--agu_pre_mode", "a06_size", "--agu_size_to", "2",
                          "--agu_size_to_load", "8"]),
    "A08": ("addrpath", ["--agu_pre_mode", "a08_subst"]),
    # [MDSPEC][R4-5.8] A07 AGU clean-ready/handshake timing model (03 sheet
    # A07-b "ready延迟"): --agu_ready_mode a07b_ready_delay at the IEW
    # memRef ready point (IEW::executeInsts), bounded delay pinned to the
    # spec's 延后1周期. A07 stays in MODEL_BLOCKED until the integration
    # build + ADDRPATH_F0_SPAN census + pilot proof land (C11/C12/L04
    # discipline: delete from MODEL_BLOCKED only when real runs assert it).
    "A07": ("addrpath", ["--agu_ready_mode", "a07b_ready_delay",
                          "--agu_ready_delay_cycles", "1"]),
    # --- SQ data/forwarding family on CHAOSLSQFwd (W5 b41f4d9a verified) ---
    "S01": ("lsqfwd", ["--lsq_struct_mode", "byte_flip"]),
    "S02": ("lsqfwd", ["--lsq_struct_mode", "byte_flip", "--bits_to_change", "2"]),
    "S03": ("lsqfwd", ["--lsq_struct_mode", "byte_lane_skew"]),  # approx: stuck-lane mask family
    "S08": ("lsqfwd", ["--lsq_struct_mode", "fwd_source_sub"]),
    "S09": ("lsqfwd", ["--lsq_struct_mode", "byte_lane_skew"]),  # approx: concat/assembly skew
    # --- SQ addr/state family on the PRE hook (W5 c7743989..1beea50d) ---
    "S04": ("addrpath", ["--agu_pre_mode", "s04_store_subst"]),
    "S05": ("addrpath", ["--agu_pre_mode", "s05_store_size"]),
    "S06": ("addrpath", ["--agu_pre_mode", "s06_store_state"]),
    "S07": ("addrpath", ["--agu_pre_mode", "s07_store_ptr"]),
    "S11": ("addrpath", ["--agu_pre_mode", "s11_store_lost"]),
    "S13": ("addrpath", ["--agu_pre_mode", "s13_store_addr"]),
    # --- LQ (W5) ---
    "L01": ("addrpath", ["--agu_pre_mode", "l01_load_addr"]),
    "L02": ("addrpath", ["--agu_pre_mode", "l02_load_state"]),
    "L03": ("lsqfwd", ["--lsqfwd_l03"]),
    # [MDSPEC][R4-5.3] L04: response-pairing target exchange (L04-b) —
    # two in-flight loads' response-pairing entries are exchanged at the
    # request->instruction() pairing point (LSQUnit::completeDataAccess ->
    # CHAOSLSQFwd::maybeSwapResponseTarget): each load's returning response
    # is delivered to the OTHER load (data unchanged, wrong consumer).
    # Event-normalized trigger on the pairing-point stream (lsuTier; the
    # SQ-forward data-path hook is split off, L03 discipline); the
    # candidate gate = plain register-WB load + live same-size/byte-enable
    # in-flight partner with an outstanding packet. L04-a (one-shot
    # transaction-ID replacement, victim-hang) NOT landed — recorded in
    # lsu_runid_map SPEC_IMPL_LANDED (mode_unimpl_plan.md L04 row, landed
    # per the template).
    "L04": ("lsqfwd", ["--lsqfwd_l04"]),
    # [MDSPEC][R4-5.7] S10: StoreSet SSIT-ID 换值 (S10-a) — the load's
    # freshly assigned SSIT SSID is substituted with ANOTHER LEGAL live
    # store-set ID (candidates = valid SSIT entries' SSIDs, no random bit
    # strings — workbook 07 实施细则) at the StoreSet training point
    # (StoreSet::violation's new-SSID arm, chaosS10* hooks in
    # CHAOSLSQFwd). Event-normalized trigger on the SSIT-training stream
    # (lsuTier; the SQ-forward data-path hook is split off, L03/L04
    # discipline). S10-b (LFST target) / S10-c (valid loss) / the other
    # violation() merge arms are NOT landed — lsu_runid_map
    # SPEC_IMPL_LANDED pending list. NOTE (honest): landed compile-
    # unverified by the isolated worktree (build/census/pilot are the
    # integration side's steps); F0 cells refuse loudly until
    # LSQFWD_F0_SPAN gains the measured (S10, binary) pairs.
    "S10": ("lsqfwd", ["--lsqfwd_s10"]),
    # --- L1D-Cache (W6; C-series runs the CHAOSCache legacy mechanism) ---
    "C01": ("cache", ["--l1d_target_field", "data", "--l1d_fault_type", "bit_flip"]),
    "C02": ("cache", ["--l1d_target_field", "data", "--l1d_fault_type", "bit_flip",
                      "--bits_to_change", "2"]),
    "C03": ("cache", ["--l1d_target_field", "data", "--l1d_fault_type", "stuck_at_zero"]),
    "C04": ("cache", ["--l1d_target_field", "tag", "--l1d_fault_type", "bit_flip"]),
    "C05": ("cache", ["--l1d_target_field", "tag", "--l1d_fault_type", "bit_flip"]),   # approx: tag relabel = C04
    "C06": ("cache", ["--l1d_target_field", "valid"]),
    "C07": ("cache", ["--l1d_target_field", "dirty"]),
    "C08": ("cache", ["--l1d_target_field", "coh"]),
    "C09": ("cache", ["--l1d_target_field", "data_shift"]),
    "C10": ("cache", ["--l1d_target_field", "valid"]),  # approx: PLRU->valid invalidate
    # [MDSPEC][R4-5.1] C11: MSHR merge corruption — the merging target's
    # address gets ONE offset-domain bit flipped at the coalescing hook
    # (BaseCache::handleTimingReqMiss, before allocateTarget). Event-
    # normalized trigger on the merge-event stream (lsuTier, see
    # _cache_tier_flags); the legacy periodic block attack is disabled in
    # this mode (mode_unimpl_plan.md C11 row, landed per the template).
    "C11": ("cache", ["--l1d_target_field", "mshr_merge"]),
    # [MDSPEC][R4-5.2] C12: fill-timing offset — a fill response on the
    # mounted L1D is DEFERRED by lsuFillDelayCycles cache cycles (stash +
    # scheduled resume into BaseCache::recvTimingResp; the fill/MSHR-free/
    # target-service all run at the shifted tick). Event-normalized
    # trigger on the fill-response stream (lsuTier, see _cache_tier_flags);
    # the legacy periodic block attack is disabled in this mode
    # (mode_unimpl_plan.md C12 row, landed per the template; submodels
    # C12-a drop / C12-b dup / C12-c early-valid / C12-d stale-tag are NOT
    # landed — the bounded offset only, recorded in lsu_runid_map
    # SPEC_IMPL_LANDED).
    "C12": ("cache", ["--l1d_target_field", "mshr_fill_timing",
                      "--l1d_fill_delay_cycles", "100"]),
    # [MDSPEC][R4-5.5] C14-a: MSHR busy/occupied stuck-at-1 (resource
    # leak) — the serviced MSHR entry is NOT released at the fill release
    # point (BaseCache::recvTimingResp's mshrQueue.deallocate), so the slot
    # never returns to the free list. Event-normalized trigger on the
    # release-event stream (lsuTier, see _cache_tier_flags); the legacy
    # periodic block attack is disabled in this mode (mode_unimpl_plan.md
    # C14 row, landed per the template). C14 has ONE sub-model (C14-a) so
    # none is deferred. NOTE (honest): the C++ is COMPILE-UNVERIFIED and
    # there is no pilot evidence — landed from an isolated no-build
    # worktree; C14-F5 cells resolve runnable but unrun, and the
    # integration side owns build + census + pilot (R4-5.5-5.6-report.md).
    "C14": ("cache", ["--l1d_target_field", "mshr_busy_leak"]),
    # [MDSPEC][R4-5.6] C15-b: MSHR capacity-arbitration "fake free" — at MSHR
    # capacity the injector fabricates a free slot (clears the full block)
    # so exactly one further miss allocation runs beyond the arbitration's
    # capacity. Event-normalized trigger on the allocation-at-capacity
    # stream (lsuTier, see _cache_tier_flags); the legacy periodic block
    # attack is disabled in this mode (mode_unimpl_plan.md C15 row, landed
    # per the template). C15-a (occupancy +/-1) and C15-c (free-list picks
    # an in-use entry) are NOT landed — recorded in lsu_runid_map
    # SPEC_IMPL_LANDED. NOTE (honest): the C++ is COMPILE-UNVERIFIED and
    # there is no pilot evidence — landed from an isolated no-build
    # worktree; C15-F4/F6 cells resolve runnable but unrun, C15-F0 cells
    # additionally stay BLOCKED(F0-span-unmeasured) until integration
    # measures the stream (R4-5.5-5.6-report.md).
    "C15": ("cache", ["--l1d_target_field", "mshr_occupancy"]),
    # --- Prefetcher (W8 f76f5632, verified today) ---
    "P01": ("prefetch", ["--prefetch_mode", "p01_stride_bitflip"]),
    "P02": ("prefetch", ["--prefetch_mode", "p02_confidence_corrupt"]),
    "P03": ("prefetch", ["--prefetch_mode", "p03_addr_subst"]),
    "P04": ("prefetch", ["--prefetch_mode", "p05_drop_dup"]),   # approx: queue drop/dup
    "P05": ("prefetch", ["--prefetch_mode", "p05_drop_dup"]),
    "P07": ("cache", ["--l1d_target_field", "tag"]),            # approx: fill way/tag -> tag
    "P08": ("prefetch", ["--prefetch_mode", "p08_stride_stuck"]),
    # [MDSPEC][R4-5.4] P06-a prefetch-as-demand fill-classification
    # marking (CHAOSPrefetch mode p06_as_demand; hook maybeMarkFillAsDemand
    # at Cache::serviceMSHRTargets' setPrefetched gate). C++ is
    # COMPILE-UNVERIFIED and pilot evidence is PENDING at landing time
    # (integration owns build + campaign — see R4-5.4 report); F0 cells
    # additionally stay loudly blocked on the PF_F0_SPAN census until
    # integration measures the two spans.
    "P06": ("prefetch", ["--prefetch_mode", "p06_as_demand"]),
    "P09": ("cache", ["--l1d_target_field", "dirty"]),          # approx: pf dirty evict -> dirty
    # --- Atomic (W8 1b97b714 + existing stxr modes) ---
    # [MDSPEC][R4-9-FSMC-A] O01/O02/O03 的家族从 "exmon"（SE 遗留窗口路径）
    # 改为 "exmon-fsmc"：这三格是 atomic/monitor 模型，只有在**有跨核一致性**
    # 的平台上才有语义，而三格在 SE 侧从来是 workload-blocked（没有可跑的 SE
    # 载体）。新家族只走 FS：lsu_multicore_fs.py 2 核 Ruby/CHI + 检查点 +
    # litmus_free 载体。**SE 路径不是被删掉，是从未存在过**（exmon 家族此前
    # 只作为"接线验证载体"存在，见 FAMILY_TIER_FLAGS 的原注释）。
    "O01": ("exmon-fsmc", ["--exmon_mode", "o01_monitor_addr_bitflip"]),
    "O02": ("exmon-fsmc", ["--exmon_mode", "o02_monitor_state_corrupt"]),
    "O03": ("exmon-fsmc", ["--exmon_mode", "stxr_force_fail"]),  # status-flip semantics
    # [MDSPEC][R4-9-FSMC] O04/O05/O09 LSE atomic-RMW family: the RMW
    # data-select MUX (O04-a), the result/old-value latch (O09-a) and the
    # RMW completion (O05-a lost) are corrupted at the SwapReq commit site
    # in BaseCache::satisfyRequest (CHAOSCache targetField=rmw_*; the same
    # event-normalized trigger discipline via --l1d_lsu_tier, F6 = the
    # first eligible RMW commit). Independence finding (R4-9-FSMC report
    # §2): the node is the CACHE-side RMW data path — NOT a multi-core
    # construct; the earlier "needs cache-side SwapResp hook" diagnosis was
    # right about the gap, wrong about it being a multi-core dependency.
    # NOTE (honest): the C++ is COMPILE-UNVERIFIED — this worktree may not
    # build — so the cells STAY in MODEL_BLOCKED until integration builds
    # the tree, censuses the RMW-commit stream and pilots (the C11/C12/L04
    # rule: delete only when real runs assert it).
    "O04": ("cache", ["--l1d_target_field", "rmw_mux",
                      "--l1d_rmw_rule", "swap_oldnew"]),
    "O09": ("cache", ["--l1d_target_field", "rmw_latch",
                      "--l1d_rmw_rule", "result_old"]),
    "O05": ("cache", ["--l1d_target_field", "rmw_order",
                      "--l1d_rmw_rule", "lost"]),
    # [MDSPEC][R4-9-FSMC] O06/O07 barrier-completion / order-tag family on
    # CHAOSLSQFwd (lsqfwd family; the LSU trigger's stream is the MemDepUnit
    # barrier-SN bookkeeping — see cpu/o3/chaos_barrier_hook.hh for the
    # code-level proof that this IS the only barrier-completion structure on
    # the platform). O06-a (early done) is the campaign default sub-model;
    # the O06-b (stuck) sub-model is reachable via --lsqfwd_o06_done stuck.
    "O06": ("lsqfwd", ["--lsqfwd_o06", "--lsqfwd_o06_done", "early"]),
    "O07": ("lsqfwd", ["--lsqfwd_o07"]),

    # --- TLB (W7 / M3 plan Task 5): FS-only family on lsu_b0_fs + B0 cpt.
    # faultType surface verified on arm_chaos_fs.py:81-100 (T3 smoke real run).
    # HONEST approximations: T10's low/mid/high pfn-bit banding submodel is
    # NOT parameterized in CHAOSArmTLB (random-bit only) — T10 rides T01's
    # bit_flip with the campaign seed driving bit choice (noted per-cell).
    "T01": ("armtlb", ["--tlb_fault_type", "bit_flip"]),
    "T02": ("armtlb", ["--tlb_fault_type", "bit_flip",
                       "--tlb_bits_to_change", "2"]),
    "T03": ("armtlb", ["--tlb_fault_type", "stuck_at_zero"]),  # stuck1 by seed parity
    "T04": ("armtlb", ["--tlb_fault_type", "pfn_to_mapped_page"]),
    "T10": ("armtlb", ["--tlb_fault_type", "bit_flip"]),  # approx: no banding submodel
    # [MDSPEC][R4-5.9] T08: FS page-table walk/fill pairing (T08-a lost
    # walk) — the walk is DROPPED at its issue point (TableWalker::walk) so
    # the requesting translation never completes (spec Timeout channel).
    # Rides the event-normalized tier on the walk-issue stream
    # (--tlb_lsu_tier <F>; the armtlb branch below appends it). Landed
    # compile-unverified by the isolated worktree; FS-only — neither the
    # build nor the pilot can run here (see MODEL_BLOCKED["T08"] and the
    # R4-5.9 report). NOT removed from MODEL_BLOCKED: no real-run evidence.
    "T08": ("armtlb", ["--tlb_fault_type", "walk_pairing"]),
    # [MDSPEC][R4-10-T05/T06/T07] entry-state / attribute / CAM-select
    # modes — implemented in CHAOSArmTLB (R4-10, compile-unverified in the
    # isolated worktree). The campaign default sub-model is the spec's
    # "-a" arm; the other sub-models are reachable via --tlb_fault_type.
    "T05": ("armtlb", ["--tlb_fault_type", "valid_clear"]),
    "T06": ("armtlb", ["--tlb_fault_type", "perm_subst"]),
    "T07": ("armtlb", ["--tlb_fault_type", "false_hit"]),
}

# [MDSPEC][R4-8-FS] The full TLB-translation model family (T01-T08 + T10;
# T09 is B0-N/A, not a translation model). Used by resolve_cell's workload-
# block step: for these models the TLB-AliasPerm workload is NOT the blocker
# (the FS tlb_probe carrier serves it), so the reason must come from the
# model-level check — precise per model. T05/T06/T07 are deliberately NOT in
# MODEL_FLAGS (their CHAOSArmTLB modes do not exist yet): they must report
# "deferred(mode unimplemented: …)" from MODEL_BLOCKED, never the misleading
# workload-level "fs-infra" phrase.
ARMTLB_MODELS = {"T01", "T02", "T03", "T04", "T05", "T06", "T07", "T08", "T10"}

# These modes are implemented but deliberately remain MODEL_BLOCKED until
# real evidence is reviewed.  Trial may route them to the FS carrier to
# collect that evidence; formal/default resolution must stay blocked.
EVIDENCE_PILOT_MODELS = {"T05", "T06", "T07", "T08"}

# [R4-10] the walk/refill family — the four sub-models of T08. All ride the
# event-normalized tier on the walk-ISSUE stream (the armtlb branch below
# appends --tlb_lsu_tier <F> for these). T08-a drops the walk at issue;
# T08-b/c/d are applied at the refill completion point.
WALK_FAULT_TYPES = ("walk_pairing", "walk_fill_dup", "walk_done_early",
                    "walk_stale_result")

# [MDSPEC][R4-6-T08] Pinned F0 window for T08's walk-issue stream. The values
# ARE the config defaults (configs/se/arm_chaos_fs.py --tlb_lsu_warmup_events
# 0 / --tlb_lsu_span_events 1000): this is an explicit pin, not a re-tune, so
# the injection index is auditable from the flag list and cannot drift with a
# default change. F0 draws next_fire = warmup + chaosSampleLCG(seed) % span
# over the WALK-ISSUE stream; with the campaign's seed=1..N (the FS branch
# appends --tlb_rng_seed <seed>) the drop lands at walk-event index 412
# (seed 1) / 417 (seed 2) / 806 (seed 3). It is NOT a census-measured span —
# the walk stream has never been counted on a real FS run (F0 census
# discipline: re-tune with a measured eligible count).
ARMTLB_T08_WARMUP_EVENTS = 0
ARMTLB_T08_SPAN_EVENTS = 1000

# [MDSPEC][R6-FTIER] The armtlb (TLB) family's F-tier contract, split by fault
# type — the defect this closes (measured 2026-10-24): the six first-wave
# RunIDs T01-F0-W4 / T02-F0-W4 / T02-F2-W4 / T04-F0-W4 / T04-F2-W4 /
# T04-F6-W4 produced pairwise-IDENTICAL normalized command lines and so
# collapsed to THREE independent experimental conditions.
#
#   * WALK family (WALK_FAULT_TYPES: T08-a/b/c/d) — the walk-ISSUE point
#     (TableWalker::walk -> CHAOSArmTLB::maybeDropWalkFill) polls the
#     event-normalized trigger, so the tier flags below ride the walk-issue
#     stream (unchanged; R4-5.9).
#   * LOOKUP modes (T01-T04/T10 / T05-T07; every other fault type) — the
#     lookup-hit path (TLB::lookup -> CHAOSArmTLB::maybeCorrupt /
#     maybeCorruptLookup) was, before R6-FIXCPP `6ec7c5aa`, a path that NEVER
#     polled `lsuTrigger`, so F1-F6 were physically NOT expressible there and
#     --tlb_lsu_tier was inert ("half-wired"). That commit landed the real
#     gate (CHAOSArmTLB::lookupTierMounted / lookupTierAllowsInjection, one
#     eligible event per TLB lookup, F6 = first TlbHit) so the lookup path now
#     consumes the SAME tier semantics as every other injector family. The
#     tool side therefore passes a REAL `--tlb_lsu_tier <F>` for F1-F6.
#
# [MDSPEC][R6-FTIER] F0 stays byte-for-byte legacy: NO `--tlb_lsu_tier` flag is
# emitted — the pre-R6 command (--tlb_max_faults 1 / --tlb_probability 1.0 +
# seed-varied eligible-event skip) IS the F0 semantics ("每次运行只注入 1 次；
# warm-up 后的 eligible event 中均匀抽样", 方案.md §5 sheet-5), and emitting a
# tier flag there would change behaviour for the already-landed F0 cells.
#
# [MDSPEC][R6-FIXTOOLS] A tier is NOT trusted merely because the tool can now
# name it: F1-F6 runs are additionally gated on a RUNTIME capability proof
# (lookup_tier_capability_gate below) — a real run must print the
# CHAOS_LSU_TIER_CAP startup marker with effective == requested and
# lookup_tier_enabled=1, or the sample is refused LOUDLY (see
# _ARMTLB_CAP_MISSING for the old-binary / missing-marker case). This keeps a
# stale binary from silently producing degenerate F0 data under an F2/F6 label.
ARMTLB_LOOKUP_TIERS = frozenset({"F0", "F1", "F2", "F3", "F4", "F5", "F6"})
# F0 = legacy path (no tier flag); F1-F6 = the landed tiered lookup path.
ARMTLB_LOOKUP_LEGACY_TIERS = frozenset({"F0"})
ARMTLB_LOOKUP_TIERED_TIERS = frozenset({"F1", "F2", "F3", "F4", "F5", "F6"})


def _armtlb_lookup_tier_block_reason(model, tier):
    """resolve_cell 的 loud block 理由（与 ARMTLB_LOOKUP_TIERS 同源，不漂移）。

    仅在档位**不在** F0-F6 时触发（未知档位，如 F7/off/拼写错误）——F1-F6
    现由 6ec7c5aa 的真实 lookup gate 表达，不再落到这里。
    """
    return ("BLOCKED(armtlb-lookup-tier-unimplemented: model %s tier %s — not a "
            "known F-tier (valid: F0-F6). F0 = legacy --tlb_max_faults 1; F1-F6 "
            "= the ARM TLB lookup-path tier landed by R6-FIXCPP 6ec7c5aa "
            "(CHAOSArmTLB::lookupTierMounted / lookupTierAllowsInjection, one "
            "eligible event per TLB lookup). Refusing rather than silently "
            "re-labelling an F0 run as %s (R6-FTIER)" % (model, tier, tier))


# [MDSPEC][R6-FIXTOOLS] Runtime lookup-tier capability marker. The landing
# binary MUST print exactly this once at startup (see the C++ field contract in
# the R6-FIXTOOLS report). Campaign parses it to prove an F1-F6 lookup run
# really ran with the tier mounted — requested vs effective must agree and the
# lookup path must be enabled; an old binary that prints no marker (or a binary
# whose effective tier disagrees) is refused LOUDLY, never accepted silently.
LSU_TIER_CAP_PREFIX = "CHAOS_LSU_TIER_CAP:"
LSU_TIER_CAP_FIELDS = ("requested", "effective", "lookup_tier_enabled")


def parse_lsu_tier_capability(text):
    """Parse the CHAOS_LSU_TIER_CAP startup marker from a run's output.

    Returns {"requested", "effective", "lookup_tier_enabled", "raw"} for the
    FIRST such line, or None when the marker is absent (old binary / not run).
    Values are the raw strings; a marker line with missing fields keeps them "".
    """
    if not text:
        return None
    for ln in text.splitlines():
        s = ln.strip()
        i = s.find(LSU_TIER_CAP_PREFIX)
        if i < 0:
            continue
        rec = {f: "" for f in LSU_TIER_CAP_FIELDS}
        rec["raw"] = s
        body = s[i + len(LSU_TIER_CAP_PREFIX):].strip()
        for tok in body.split():
            k, sep, v = tok.partition("=")
            if sep:
                rec[k] = v
        return rec
    return None


def lookup_tier_capability_gate(requested, text):
    """Runtime capability proof for an F1-F6 ARM-TLB-lookup run.

    `requested` is the tier the campaign asked for (e.g. "F2"). Returns
    {"ok": bool, "requested", "effective", "enabled", "marker", "reason"}.
    `ok` only when the marker is present AND effective == requested AND
    lookup_tier_enabled == 1. A missing marker (old binary), a mismatch, or a
    disabled lookup tier is refused LOUDLY (`reason` names which) — never a
    silent pass into an F0-degenerate dataset.
    """
    rec = parse_lsu_tier_capability(text)
    base = {"requested": requested, "effective": None, "enabled": None,
            "marker": rec}
    if rec is None:
        return dict(base, ok=False, reason=(
            "armtlb-lookup-tier-capability-missing: 二进制未输出 %s 启动标记"
            "（requested/effective/lookup_tier_enabled）——旧二进制无能力标记，"
            "拒绝把 %s 当已挂载档位采信（不得产生静默退化数据）"
            % (LSU_TIER_CAP_PREFIX, requested)))
    miss = [f for f in LSU_TIER_CAP_FIELDS if not str(rec.get(f, "")).strip()]
    if miss:
        return dict(base, ok=False,
                    effective=rec.get("effective") or None,
                    enabled=rec.get("lookup_tier_enabled") or None,
                    reason=(f"armtlb-lookup-tier-capability-malformed: 标记缺字段 "
                            f"{miss}（raw={rec.get('raw')!r}）"))
    eff = rec["effective"]
    en = rec["lookup_tier_enabled"]
    out = dict(base, effective=eff, enabled=en)
    if en not in ("1", "true", "True", "yes"):
        return dict(out, ok=False, reason=(
            f"armtlb-lookup-tier-capability-disabled: lookup_tier_enabled={en!r}"
            f"（应为 1）——lookup 路径未启用档位，{requested} 不成立"))
    if eff != requested:
        return dict(out, ok=False, reason=(
            f"armtlb-lookup-tier-capability-mismatch: requested={requested} 但 "
            f"effective={eff} ——请求档位与运行时生效档位不一致，拒绝采信"))
    if str(rec.get("requested", "")) not in ("", requested):
        return dict(out, ok=False, reason=(
            f"armtlb-lookup-tier-capability-mismatch: 标记 requested="
            f"{rec.get('requested')!r} 与命令请求 {requested!r} 不一致"))
    return dict(out, ok=True, reason="")


def _armtlb_lookup_tier_flags(freq):
    """Flags the armtlb LOOKUP path needs for `freq` (None ⇒ not expressible)."""
    if freq in ARMTLB_LOOKUP_LEGACY_TIERS:      # F0: byte-for-byte legacy
        return []
    if freq in ARMTLB_LOOKUP_TIERED_TIERS:      # F1-F6: real tier flag
        return ["--tlb_lsu_tier", freq]
    return None

# ---- FS carrier (M3 plan Task 5/6 decision tree) ----
# T-cell design workloads (MiBench/TLB-AliasPerm/GAP) have no binaries on the
# stock ubuntu image; SPEC stays license-blocked. Runnable T-cells execute on
# the tlb_probe.rcS carrier (kernel/user mixed TLB pressure + md5 oracle) —
# the substitution is recorded in the backfill note, never silent.
FS_CONFIG = REPO / "configs/fs/lsu_b0_fs.py"
FS_CARRIER_RC = REPO / "configs/fs/tlb_probe.rcS"
FS_KERNEL = REPO / "gem5-fs/vmlinux"
FS_DISK = REPO / "gem5-fs/ubuntu.img"
FS_BOOTLOADER = REPO / "gem5-fs/boot.arm64"
TLB_PROBE_GOLDEN = "b6d81b360a5672d80c27430f39153e2c"  # md5 of 1 MiB zeros (host-computed)

# --- [MDSPEC][R4-9-FSMC-A] 多核 FS Atomic-Litmus 载体 ---------------------
# O01/O02/O03 是 **atomic / exclusive-monitor** 模型：它们只有在**有跨核
# 一致性**的平台上才有语义（R4-8-FSMC §1.2：gem5 v25 classic 多核没有跨核
# 一致性，MP 型 litmus 的无故障对照就会挂死）。所以这三格的载体是
# configs/fs/lsu_multicore_fs.py（2 核 Ruby/CHI）+ workloads/litmus 的
# litmus_free（零 libc freestanding，~8 KB，见 R4-9-FSMC-A 报告），
# 经 litmus_free.rcS 投放，oracle 是载体自报的三条"禁出现计数"行 + 一行
# FINAL=<16hex>（golden 即无故障运行的 FINAL）。
#
# 检查点：2 核 CHI 的用户态检查点是 /tmp 下的**可再生临时产物**（启动约 16
# min，见 R4-8-FSMC §3）。为了让工具不把一个 /tmp 路径硬编码成"资产"，这里
# 走环境变量 LSU_FS_MC_CHECKPOINT，缺省指向 R4-8-FSMC 生成的那个；不存在时
# 在 resolve 阶段就**大声拒绝**（不是静默跑一个没有检查点的配置）。
FSMC_CONFIG = REPO / "configs/fs/lsu_multicore_fs.py"
FSMC_CARRIER_RC = REPO / "configs/fs/litmus_free.rcS"
FSMC_CHECKPOINT_ENV = "LSU_FS_MC_CHECKPOINT"
FSMC_DEFAULT_CHECKPOINT = "/tmp/r4-8-fsmc/mc_boot/cpt.243414599076"
FSMC_GOLDEN_FINAL = "6b39e7aaa74b663f"  # 无故障运行的 FINAL（见 R4-9-FSMC-A 报告 §3）
# F 档位里 CHAOSExMon **能诚实表达**的那些：
#   * F0 = 单次瞬态（task_plan.md §18）——maxFaults=1 单次注入即是 F0；
#   * F5 = 永久（"always true，注入器对每个 eligible 事件施加"）——
#     maxFaults=0（无限）即永久。
#   * F2 = 重复/突发（chaos_trigger.hh 的 interval 260000 cycles）与
#     F6 = 确定性路径/矩阵规定层：**CHAOSExMon 不消费 chaos_trigger**，
#     没有 interval / 确定性路径语义 ⇒ 无法表达，保持 BLOCKED（见
#     resolve_cell 的 F 档位门与 lsu_fsmc_verdict.py 的逐格理由）。
FSMC_FAULT_EXPRESSIBLE_TIERS = ("F0", "F5")

# Model-level blocks (never silently skipped; the reason lands in col26/27).
MODEL_BLOCKED = {
    # notify-only event sources — consumer-side corruption NOT implemented
    # (W5/W6 wired chaosLsuF6Notify call sites only; grep-verified 2026-09-26)
    # [MDSPEC][R4-5.1] C11 removed from this table: the merge corruption
    # mode is implemented (targetField=mshr_merge, CHAOSCache
    # maybeCorruptMergeTarget at BaseCache::handleTimingReqMiss) and proven
    # by real runs — see round4_findings.md §R4-5.1.
    # [MDSPEC][R4-5.2] C12 removed from this table: the fill-timing offset
    # mode is implemented (targetField=mshr_fill_timing, CHAOSCache
    # maybeDeferFillTiming at the top of BaseCache::recvTimingResp) and
    # proven by real runs — see round4_findings.md §R4-5.2.
    # [MDSPEC][R4-5.3] L04 removed from this table: the response-pairing
    # target exchange (L04-b) is implemented (--lsqfwd_l04, CHAOSLSQFwd
    # maybeSwapResponseTarget at the LSQUnit::completeDataAccess pairing
    # point) and proven by real runs — see round4_findings.md §R4-5.3.
    # [MDSPEC][R4-5.4] P06-a prefetch-as-demand fill-classification marking
    # (--prefetch_mode p06_as_demand, CHAOSPrefetch maybeMarkFillAsDemand at
    # Cache::serviceMSHRTargets' setPrefetched gate) IS implemented and
    # proven runnable by integration: the C++ built clean on binary
    # 2c5a03913bebfcae, the census showed the hook firing on real
    # prefetch-owned fills (cache_dirtyevict attempted=56 eligible=56;
    # prefetch_stride attempted=32 eligible=32), and the campaign pilot is
    # recorded in round4_findings.md §R4-5.4. Removed from this table only
    # on that evidence (the round's "assert runnable first" rule), exactly
    # as C11/C12/L04 were.
    # ---
    # [MDSPEC][R4-5.7] S10 StoreSet SSIT-ID 换值模式（S10-a）已由隔离 worktree
    # 实现（`--lsqfwd_s10` + `CHAOSLSQFwd` 的 chaosS10* 钩子 @ StoreSet::
    # violation / checkInst + `store_set.cc`），但**尚无论证可跑**：该 worktree
    # 禁跑 build/pilot，故并入时仍是 compile-unverified。按本轮铁律
    # 「断言可跑才删」，**S10 暂留本表**；主 worktree 的 build + 跨度普查 +
    # 真机 pilot 通过后，在同一集成提交内改为证据化移除。
    # [MDSPEC][R4-5.7b integration] S10 STAYS BLOCKED — measured reason: the
    # S10-a premise ("another legal live store-set to substitute") is
    # UNREACHABLE on this platform. Real runs (integration binary
    # 0d2f0664823f4315, 6 workloads sq_forward / gap_bfs / alias_sites /
    # cache_dirtyevict / stream_chase / sqlite_like): attempted=4..55,
    # arm1_events == attempted, arm1_cand_empty == arm1_events,
    # max_live_ssids == 0, arm1_cand_ok == 0, eligible == 0.
    # Proven mechanism (dedicated probe build, probes removed before commit):
    # every victim returned by SSIT.findVictim() lies OUTSIDE the calling
    # StoreSet's own entry array (23/23), because the per-CPU
    # params.SSITIndexingPolicy object is SHARED by all MaxThreads
    # MemDepUnits and each StoreSet::init() overwrites the policy's
    # entry-pointer table (AssociativeCache::initParams ->
    # indexingPolicy->setEntry) — only the last-initialised thread's SSIT is
    # reachable, the active thread's SSIT never validates, so the candidate
    # set is empty by construction. See round4_findings.md §R4-5.7b and
    # blocked_triage.md (new WORKLOAD/PLATFORM class).
    # [MDSPEC][R4-8-S10] S10 MODEL_BLOCKED entry DELETED here — the
    # platform defect that justified it (§R4-5.7b: shared SSITIndexingPolicy
    # across MaxThreads MemDepUnits) was FIXED and real-run verified in
    # §R4-6-S10 (binary 7d52bc1392a10055, eligible>0 on two carriers). The
    # C11/C12/L04/A07 discipline ("delete only when real runs assert it")
    # is now satisfied per-tier:
    #   * F5 cells (S10-F5-W5/W9) — really activated (9/12) in §R4-6-S10b;
    #   * F0 cells (S10-F0-W5/W9) — runnable via the per-(model, workload)
    #     measured span in LSQFWD_F0_SPAN (streams 3 / 4, measured this
    #     round; warmup=1+span=N IS the exact F0-uniform parameterization)
    #     and real-run verified (injection log non-empty) in R4-8-S10;
    #   * F2 cells (S10-F2-W5/W9) — do NOT ride this deletion: their
    #     SPEC-FIXED interval (100000) makes them structurally zero on
    #     these carriers and they are refused cell-by-cell by
    #     LSQFWD_INTERVAL_UNREACHABLE (a loud, measured, per-cell block,
    #     not a silent zero). See round4_findings.md §R4-8-S10.
    # no clean hook (documented in injector headers / W4-W8 session notes)
    # [MDSPEC][R4-5.8 integration] A07 MODEL_BLOCKED entry DELETED here —
    # the C11/C12/L04 discipline ("delete only when real runs assert it")
    # is satisfied by real integration runs on binary sha256 prefix
    # 09d70dd0987c57d1: (1) clean build; (2) ADDRPATH_F0_SPAN census
    # (eligible=2795 on agu_addrmodes, 2579 on sq_forward — see
    # ADDRPATH_F0_SPAN); (3) pilot: 6 cells x 3 seeds, injection log
    # non-empty and lsu_chain_check per-edge records — see
    # docs/gem5-fi/lsu/mdspec/round4_findings.md §R4-5.8.
    # NOTE (merge-order): the R4-5.4 P06 MODEL_BLOCKED entry was already
    # deleted on the integration branch (P06 landed and pilot-proven) —
    # this merge keeps it deleted and does NOT reintroduce it.
    # [MDSPEC][R4-9-FSMC] O04/O09: the RMW data-path hooks NOW EXIST
    # (CHAOSCache targetField=rmw_mux / rmw_latch at BaseCache::
    # satisfyRequest's SwapReq branch; MODEL_FLAGS carries the routing) but
    # the C++ is COMPILE-UNVERIFIED (this worktree may not build) and no
    # real run has asserted them — same state as C11/C12/L04 at their
    # landing. The block is KEPT (delete-only-on-real-run-evidence, the
    # round's rule); the honest phrase replaces the old "needs cache-side
    # SwapResp hook" gap statement. Reason text keeps a model-gap token
    # (RMW) so tools/lsu_blocked_triage.py still buckets these as
    # HOOK-UNIMPL until the integration pilot moves them.
    "O04": "deferred(RMW data-path hook LANDED (rmw_mux @ SwapReq commit) "
           "but COMPILE-UNVERIFIED — build + RMW-commit census + pilot "
           "pending, R4-9-FSMC)",
    "O09": "deferred(RMW operand hook LANDED (rmw_latch @ SwapReq commit, "
           "result/old-value latch) but COMPILE-UNVERIFIED — build + "
           "RMW-commit census + pilot pending, R4-9-FSMC)",
    # B0 protection rows (09 §6.4): not applicable, never zero-filled
    "S12": "不适用(B0无保护)",
    "T09": "不适用(B0无保护)",
    "C13": "不适用(B0无保护)",
    "O08": "不适用(B0无保护)",
    # TLB models: T01-T04/T08/T10 are mapped (armtlb family above), T09 is
    # B0-N/A below. The old blanket T01-T10 block fired before MODEL_FLAGS and
    # masked the new FS routing (dry-run caught).
    # [MDSPEC][R4-10-T05/T06/T07] the entry-state / attribute-substitution /
    # CAM-select MODES are now IMPLEMENTED in CHAOSArmTLB (valid_clear/
    # valid_set/global_flip/asid_subst; perm_subst/memtype_subst/
    # pagesize_subst; false_hit/double_hit/wrong_way — see the R4-10 report
    # and tests/test_lsu_hook_t05_state.py). The C++ is COMPILE-UNVERIFIED
    # (the R4-10 worktree may not build) and no real FS run has asserted
    # them, so the block is KEPT on the same discipline as O04/O09 (delete
    # only on real-run evidence). The honest phrase replaces the old
    # "mode unimplemented" gap statement.
    "T05": ("deferred(T05 entry-state modes LANDED (valid_clear/valid_set/"
            "global_flip/asid_subst) but COMPILE-UNVERIFIED — build + FS "
            "pilot pending, R4-10)"),
    "T06": ("deferred(T06 attribute legal-substitution modes LANDED "
            "(perm_subst/memtype_subst/pagesize_subst) but "
            "COMPILE-UNVERIFIED — build + FS pilot pending, R4-10)"),
    "T07": ("deferred(T07 CAM/way-select modes LANDED (false_hit/double_hit/"
            "wrong_way) but COMPILE-UNVERIFIED — build + FS pilot pending, "
            "R4-10)"),
    # [MDSPEC][R4-5.9] T08: the walk/fill pairing MODE now exists
    # (faultType=walk_pairing, T08-a lost walk — TableWalker::walk drops the
    # walk; registerTlbWalkPair emits the tlb_walk/tlb_refill node pair).
    # [R4-8-INT 语义合并] 两侧都在订正 T08 的理由文本，事实互补（W4 见
    # r4-7-fsinfra-w1，W9 见 r4-8-spec-residual），取并集：
    # T08-a（walk_pairing）**已真机断言**——旧理由 "landed compile-unverified,
    # pilot pending" 已被证伪（冻结二进制 7d52bc1392a10055 既带修复字符串、
    # 又能打印只可能由修复后 maybeDropWalkFill 产生的 drop 行；pilot 已实跑）。
    #   * T08-F0-W4 seed1（R4-8-FS-W1 §4.3）：arm_tlb_walk_issue_probe +
    #     arm_tlb_lookup_hit_skipped + arm_tlb_walk_issue_drop **walk_id=703**，
    #     且 prop_evt 的 tlb_walk/tlb_refill 共享 walk_id=703 + fault_id=1、
    #     tlb_refill field=lost —— R4-6-T08 §4.3 四项验收判据全中。
    #   * T08-F0-W9（R4-6-T08）与 T08-F6-W9（R4-8-SPEC §B.3，F6=首次 walk 即
    #     注入，drop walk_id=1 与 probe 同 tick）同样注入成功、activated=1。
    #   * T08-F4-W9 = **诚实零（结构性）**：F4 burst interval=100000 eligible
    #     events ≫ 实测 walk-issue 流 ~1e3（probe 行证明钩子到达，无 drop 行）。
    # 条目**保留**（不删）以免静默解锁：残留理由是未落地的 T08-b/c/d 子模型
    # 模式（mode 未实现、无真机覆盖）+ 上述 pilot 仅 1 seed（本仓别处删除门槛
    # 为 3 seed）。删除是一行改动，留给集成方裁决（R4-6-T08 §4.4 /
    # R4-8-FS-W1 §7.2 / R4-8-SPEC-residual §B）。
    "T08": ("walk_pairing (T08-a) landed AND real-run proven — F0-W4 seed1 "
            "(R4-8-FS-W1 §4.3: walk_issue_probe + walk_issue_drop walk_id=703 "
            "+ tlb_walk/tlb_refill sharing walk_id=703/fault_id=1 with refill "
            "field=lost), F0-W9 (R4-6-T08) and F6-W9 (R4-8-SPEC §B.3) injected "
            "with the same walk_id/field=lost signature, activated=1; F4-W9 "
            "honest zero (burst interval 1e5 eligible events >> the ~1e3 "
            "walk-issue stream — hook reached, never fires), binary "
            "7d52bc1392a10055. [R4-10] the T08-b/c/d sub-model modes "
            "(walk_fill_dup / walk_done_early / walk_stale_result) are now "
            "LANDED in CHAOSArmTLB + table_walker.cc (refill completion hook, "
            "walk_id-paired tlb_walk/tlb_refill with field/outcome per "
            "sub-model) but COMPILE-UNVERIFIED — build + FS pilot await "
            "integration. "
            "Block retained: pilots are 1 seed each and the sub-models have no "
            "real-run coverage; deletion is an integration decision"),
}
# O05-O07 are multicore-semantic models — their cells sit on Atomic-Litmus/
# PARSEC (workload-blocked); add the model-level reason for robustness.
# [MDSPEC][R4-8-FSMC] 这三条原先只写 "needs multi-core"，暗示多核 FS 是
# 唯一缺口。实测不是：多核 FS 基础设施已经落地并真机跑通（configs/fs/
# lsu_multicore_fs.py，guest nproc=2），而这三个模型连**语义**都还没实现
# —— 与多核无关的独立阻塞。理由补齐为模型缺口 + 指出基础设施已就绪。
MODEL_BLOCKED.update({
    # [R4-8-INT 语义合并] O05/O06/O07 的 MODEL_BLOCKED 理由采
    # r4-9-fsmc-c 的**更新后事实**（钩子已落地 → 旧的"模型语义未实现"
    # 已被证伪），保留 "multicore-fs:" 前缀（既真实又承重：
    # lsu_blocked_triage.py 按 r"multicore" 分桶）。
    # [MDSPEC][R4-9-FSMC] O05: the RMW-completion hook NOW EXISTS
    # (CHAOSCache targetField=rmw_order, rule=lost — the memory update is
    # dropped at the SwapReq commit site, DATA payload stays correct;
    # MODEL_FLAGS carries the routing) but the C++ is COMPILE-UNVERIFIED
    # and un-piloted, so the block is KEPT (C11/C12/L04 rule). The cells
    # additionally sit on Atomic-Litmus (W7) — a workload that genuinely
    # needs the multi-core FS carrier — so the "multicore-fs:" token is
    # kept deliberately: it is BOTH true and load-bearing for
    # tools/lsu_blocked_triage.py's FS-MULTICORE bucket (dropping it would
    # silently re-bucket these RunIDs).
    "O05": "blocked(multicore-fs: W7 Atomic-Litmus workload; RMW-completion "
           "hook rmw_order LANDED @ SwapReq commit and COMPILED (build OK) "
           "but un-piloted, R4-9-FSMC)",
    # [MDSPEC][R4-9-FSMC] O06/O07: the barrier-completion / order-tag hooks
    # NOW EXIST (CHAOSLSQFwd --lsqfwd_o06/--lsqfwd_o07; MemDepUnit barrier-SN
    # bookkeeping, cpu/o3/chaos_barrier_hook.hh) but the C++ is
    # COMPILE-UNVERIFIED (this worktree may not build) and un-piloted, so the
    # blocks are KEPT (C11/C12/L04 rule). The cells sit on Atomic-Litmus
    # (W7) — a workload that genuinely needs the multi-core FS carrier — so
    # the "multicore-fs:" token is kept deliberately: it is BOTH true and
    # load-bearing for tools/lsu_blocked_triage.py's FS-MULTICORE bucket.
    "O06": "blocked(multicore-fs: W7 Atomic-Litmus workload; barrier-"
           "completion hook LANDED (MemDepUnit barrier-SN bookkeeping, "
           "CHAOSLSQFwd --lsqfwd_o06) and COMPILED but un-piloted, "
           "R4-9-FSMC)",
    "O07": "blocked(multicore-fs: W7 Atomic-Litmus workload; order-tag "
           "exchange hook LANDED (MemDepUnit barrier-SN set as the ordering-"
           "tag proxy, CHAOSLSQFwd --lsqfwd_o07) and COMPILED but "
           "un-piloted, R4-9-FSMC)",

    # [LSU][MDSPEC][A6] A06 专项裁决（计划 §2.d 2026-10-19；R4-6-A06 + R4-8-A06
    # + R4-8-INT 2026-10-22 集成实测更新）。**忠实实现 = 已实现臂的全集**：
    #   * store 侧 size（含 shrink）——真机可达且有 Crash 后果（R4-8-A06 §5）；
    #   * load 侧 **WIDEN** ——真机可达（R4-8-A06；本轮 campaign 试跑
    #     activated=1，见 runs/lsu/trial_r48_a06）；
    #   * A06-b byte-enable store 掩码 ——真机 be_subst=1（本轮复验）。
    # **load 侧 SHRINK 被判为「真正不可达路径」并响亮拒绝**：定宽完成合同在
    # Packet::getRaw<T> 上断言 sizeof(T) <= pkt->size（src/mem/packet_access.hh:55），
    # 用的是 **packet 的 size 字段**而非目的缓冲区 ⇒ 缓冲区下限在构造上无效。
    # 集成实测（二进制 78b8582966e83072）：--agu_size_to_load 1 → SIGABRT
    # `Assertion sizeof(T) <= size failed`。已在 a06LoadSize 里判 ShrinkUnsafe
    # （计数拒绝、绝不注入；修后同命令 rc=0 不再崩溃）。忠实 shrink 需要把
    # packet size 保持 >= 静态宽度、截断改在 commit 完成 —— 属 LSQ/AGU 重设计，
    # 非本臂。仍 BLOCKED 的**具体**理由：A06 的 F0 跨度未实测（本轮 campaign
    # 试跑报 CHAOS_LSU_TRIGGER_ALARM EARLY_BIAS：eligible=1677 ≫ span=1000），
    # 且 pilot 仅 1 seed（本仓别处解锁门槛为 3 seed + 逐边链）。
    "A06": ("BLOCKED(load WIDEN + store size/shrink + A06-b store mask are "
            "real-machine verified (campaign trial: activated=1); load SHRINK "
            "is a PROVEN-unreachable path and is declined loudly "
            "(Packet::getRaw asserts sizeof(T) <= pkt->size — real SIGABRT "
            "evidence; faithful shrink needs an LSQ/AGU redesign). Remaining: "
            "A06 F0 span unmeasured (EARLY_BIAS alarm, eligible 1677 >> span "
            "1000) and the pilot is 1 seed. SPEC-SCOPE ruling item "
            "(MDSPEC §2.d ruling 2026-10-19, A06 load-side contract) — "
            "R4-8-A06 + R4-8-INT 2026-10-22)"),})

# Trigger-tier flags per family. F0 span: addrpath/lsqfwd eligible streams
# are per-request (large; span 1000 verified by the W10 trial); prefetch
# eligible streams are per-calculatePrefetch (131/9 on prefetch_stride —
# span 50/8 verified today; a span larger than the stream never fires,
# noted as the F0-uniform approximation).
#
# [LSU][MDSPEC][A5] F6 单语义门禁（用户指令二.4 / 规格 F6 = 首次出现指定
# 事件时注入一次）：正式（mdspec）track 只允许 early_stress 语义；
# steady_state 仅限显式 opt-in 的独立扩展实验，不得与正式 F6 样本混合。
F6_DEFAULT_MODE = "early_stress"


def assert_formal_f6_mode(mode):
    """正式 track 的 F6 模式门禁：仅 early_stress 通过，其余 SystemExit。"""
    if mode != F6_DEFAULT_MODE:
        sys.stderr.write(
            f"[F6-GATE] formal track 拒绝 f6Mode={mode!r}：规格 F6 = 首次出现"
            f"指定事件时注入一次（early_stress）。steady_state 仅限显式 "
            f"opt-in 的独立扩展实验，不得与正式 F6 样本混合。\n")
        raise SystemExit(2)
    return None


# [MDSPEC][R4-5.8] A07 (agu_ready a07b_ready_delay) F0 span table — the
# SAME per-(model, workload binary) contract as LSQFWD_F0_SPAN /
# CACHE_F0_SPAN above (an unmeasured pair is refused LOUDLY by
# resolve_cell -> BLOCKED(F0-span-unmeasured), never a silent reuse of
# another pair's span; the teardown CHAOS_LSU_TRIGGER eligible= is the
# stream size when measured with tier=F0 + span=1000000). The A07
# eligible stream = plain (non-atomic, non-prefetch) loads/stores
# reaching the AGU clean-ready point (IEW::executeInsts' isMemRef
# branch) — a DIFFERENT stream from the A01-A03 sendFragment fragments
# and every PRE-family model, measured separately. THE TWO A07 ENTRIES
# ARE DELIBERATELY ABSENT: this session was forbidden to run the census
# (no build, no gem5 runs). The main agent must measure, with the
# rebuilt binary (commands in R4-5.8-report.md):
#   (A07, "agu_addrmodes")  — W3 AGU-AddrModes probe
#   (A07, "sq_forward")     — W5 SQ-Forward probe
# then set them here. A07-F0 cells refuse loudly until then.
ADDRPATH_F0_SPAN = {
    # (model, workload binary) -> measured eligible event stream size
    # [MDSPEC][R4-5.8 integration] A07 census (tier=F0, warmup=1,
    # span=1000000 pure-census runs; integration binary sha256 prefix
    # 09d70dd0987c57d1): the A07 eligible stream = plain (non-atomic,
    # non-prefetch) loads/stores reaching the IEW ready/handshake point —
    # a DIFFERENT stream from the A01-A03 fragments and from every
    # PRE-family model; no other model's number may be reused. Real
    # teardown lines (runs/lsu/r4_a07_span/<wl>.run.out):
    #   agu_addrmodes: injector=CHAOSAddrPath tier=F0 attempted=2795
    #                  eligible=2795 injected=0 (SPAN_UNREACHABLE, census)
    #   sq_forward:    injector=CHAOSAddrPath tier=F0 attempted=2579
    #                  eligible=2579 injected=0 (SPAN_UNREACHABLE, census)
    ("A07", "agu_addrmodes"): 2795,
    ("A07", "sq_forward"): 2579,
}


def _addrpath_tier_flags(model, tier, wl_binary=None):
    # [MDSPEC][R4-5.8] A07: per-(model, workload) F0 span with the
    # LSQFWD_F0_SPAN loud-refusal contract (see ADDRPATH_F0_SPAN above);
    # warmup=1 + span=N = the TRUE F0-uniform parameterization. Every
    # other addrpath model keeps the historical tier flags byte-identical
    # (the pre-R4-5.8 span=1000 family default — the R4-2 §2.4 parked
    # addrpath-span item, unchanged by this task).
    if model == "A07" and tier == "F0":
        span = ADDRPATH_F0_SPAN.get((model, wl_binary))
        if span is None:
            return None   # resolve_cell turns this into a loud BLOCKED cell
        flags = ["--addrpath_lsu_tier", tier,
                 "--addrpath_warmup_events", "1",
                 "--addrpath_span_events", str(span)]
    else:
        flags = ["--addrpath_lsu_tier", tier,
                 "--addrpath_warmup_events", "0",
                 "--addrpath_span_events", "1000"]
    if tier == "F6":
        # 显式钉死规格 F6 语义并过正式门禁（防 steady_state 混入正式样本）
        assert_formal_f6_mode(F6_DEFAULT_MODE)
        flags += ["--addrpath_f6_mode", F6_DEFAULT_MODE]
    return flags


# [MDSPEC][R4-1-review-I2] lsqfwd F0 span is PER (MODEL, WORKLOAD BINARY),
# measured with real runs (a family-wide constant silently biases F0 to the
# first `span` events on longer streams and never fires on shorter ones —
# the reviewer's two failure modes; and a model-only table is unsound where
# the eligible stream is workload-dependent: L03 measured 571 on
# sq_forward but 18681 on sqlite_like). warmup=1 + span=N is the TRUE
# F0-uniform parameterization: next_fire = 1 + lcg(seed)%N ∈ [1,N] hits
# each of the N eligible events with probability 1/N (warmup=0 + span=N
# double-weights event 1 and can never hit event N — that bias was real in
# the previous span=7/warmup=0 config). The teardown alarm
# (CHAOS_LSU_TRIGGER_ALARM, chaos_lsu_trigger.hh summary) fires LOUDLY on
# both drift modes: SPAN_UNREACHABLE (attempted>0 && injected==0) and
# EARLY_BIAS (injected>0 && eligible ran past the draw window).
#
# Measurements (real runs 2026-10-20, binary cd49e8dfabe531c4, the resolved
# campaign command with tier=F0 and span=1000000 so the draw never lands;
# CHAOS_LSU_TRIGGER teardown eligible= is the stream size). Quoted output in
# docs/gem5-fi/lsu/mdspec/round4_findings.md §R4-1-fix.
LSQFWD_F0_SPAN = {
    # (model, workload binary) -> measured eligible-stream size
    ("S01", "sq_forward"): 7,    # byte_flip, corrupt() path
    ("S02", "sq_forward"): 7,    # byte_flip x2, corrupt() path
    ("S03", "sq_forward"): 7,    # byte_lane_skew, corrupt() path
    ("S08", "sq_forward"): 2,    # fwd_source_sub, maybeSubstituteSource
                                 #   (alt-SQ-entry opportunities; the
                                 #   R4-1-review-I2 change routes this site
                                 #   through the trigger — before, the tier
                                 #   flags were inert here)
    ("S09", "sq_forward"): 7,    # byte_lane_skew, corrupt() path
    ("L03", "sq_forward"): 571,  # violation-check stream (lsqfwd_l03)
    ("L03", "sqlite_like"): 18681,
    # [MDSPEC][R4-5.3] L04 rows (real runs 2026-10-21, binary
    # 7a546ef5f2df1127, same census shape: tier=F0 warmup=1 span=1000000,
    # seed 1 — draw_next_fire=756413 never landed, injected=0,
    # SPAN_UNREACHABLE alarm = the census intent; full census commands in
    # round4_findings.md §R4-5.3). The L04 stream is the response-pairing
    # point's ELIGIBLE responses: a plain register-WB load response with a
    # live same-size/byte-enable in-flight partner whose request has an
    # outstanding packet (LSQUnit::completeDataAccess hook) — a DIFFERENT
    # stream from the S models' forwards (7) and L03's violation checks.
    ("L04", "sq_forward"): 324,    # attempted=2317
    ("L04", "sqlite_like"): 5597,  # attempted=35156
    # [MDSPEC][R4-8-S10] S10 rows — MEASURED 2026-10-22 (binary
    # 7d52bc1392a10055, census shape identical to the L04 rows above:
    # tier=F0 warmup=1 span=1000000 seed 1 — the draw never lands, so the
    # teardown CHAOS_LSU_TRIGGER `eligible=` IS the whole stream and the
    # SPAN_UNREACHABLE alarm is the census intent). The S10 stream is the
    # StoreSet new-SSID assignment arm's ELIGIBLE events: a violation
    # retrain where NEITHER the load nor the store PC has a valid SSIT
    # entry AND at least one OTHER live store-set ID exists (candidate
    # scan non-empty) — a DIFFERENT stream from L03's violation checks
    # (571 on sq_forward: every checkViolations hit) and from the S
    # models' forwards (7). Raw teardown lines (quoted in
    # docs/gem5-fi/lsu/mdspec/R4-8-S10-span-report.md):
    #   sq_forward: injector=CHAOSLSQFwd tier=F0 attempted=4 eligible=3
    #               injected=0 ... mode=SPAN_UNREACHABLE draw_next_fire=756413
    #   gap_bfs   : injector=CHAOSLSQFwd tier=F0 attempted=5 eligible=4
    #               injected=0 ... mode=SPAN_UNREACHABLE draw_next_fire=756413
    # Both runs also logged (platform fix witness, §R4-6-S10):
    #   CHAOS_LSU_S10_FORK ... arm1_cand_ok=3 (sq_forward) / 4 (gap_bfs),
    #   max_live_ssids=3 / 4.
    # The stream is workload-length-bound at 10^1: both spec carriers are
    # SHORT directed probes (single loop nest, run ends by itself) and the
    # S10 eligible event is one-shot per (store_PC, load_PC) pair per
    # StoreSet::clear() period (250000 memory ops, store_set.cc
    # checkClear) — so a stream of 10^5 is unreachable for either carrier
    # (see LSQFWD_INTERVAL_UNREACHABLE below for the F2 consequence).
    ("S10", "sq_forward"): 3,    # W5 carrier (SQ-Forward 转发探针)
    ("S10", "gap_bfs"): 4,       # W9 carrier (GAP/Graph500 子集)
}


# [MDSPEC][R4-8-S10] INTERVAL-TIER reachability refusals, keyed per
# (model, tier, workload binary) exactly like the span tables above.
#
# F1/F2/F3 (+F4's burst period) arm on an eligible-COUNT threshold drawn as
# `interval/2 + rng % interval` (chaos_lsu_trigger.hh intervalEvents() +
# scheduleNext()) — so the MINIMUM first fire for tier T is
# intervalEvents(T)/2. A run whose WHOLE eligible stream is shorter than
# that can NEVER fire tier T: the zero is structural (no window, nothing to
# tune), and it is NOT fixable by calibration the way F0 is — F1-F4's
# intervals are SPEC-FIXED (05 r3-r5: mean 1e6/1e5/1e4 eligible events) and
# re-tuning them to the workload would ALTER THE FAULT-MODEL SEMANTICS.
# That asymmetry is exactly why F0 (no interval) gets the per-workload span
# calibration above while F1-F4 do not.
#
# Measured S10 streams (LSQFWD_F0_SPAN, this round): sq_forward 3,
# gap_bfs 4. F2's minimum first draw is intervalEvents(F2)/2 = 50000
# (intervalEvents(F2) = 100000, store_set.cc/chaos_lsu_trigger.hh) — four
# orders of magnitude above either stream, so S10-F2-W5 / S10-F2-W9 are
# STRUCTURALLY ZERO on the spec-pinned W5/W9 carriers. They therefore
# refuse LOUDLY (never run and report a hollow activated=0) until either
# (a) the spec's W5/W9 carrier is re-scoped to a long carrier sustaining
# >= 5*10^4 eligible StoreSet events, or (b) the S10 F2 cell is dropped.
# Both are spec-level decisions, NOT taken here.
#
# NOTE (honest, recorded NOT acted on — one-patch-per-unit): the identical
# interval/2 > measured-stream condition holds for the other lsqfwd-family
# F2 cells (S01/S02/L01/L02/L04/S04-S06/S08/S09/S13-F2-*, 26 cells whose
# measured streams are 2-5597). Flagging it here rather than silently
# re-blocking 26 cells outside this S10 patch; the orchestrator decides.
LSQFWD_INTERVAL_UNREACHABLE = {
    ("S10", "F2", "sq_forward"),   # measured stream 3    << min draw 50000
    ("S10", "F2", "gap_bfs"),      # measured stream 4    << min draw 50000
    # F1/F3/F4 on the same carriers would be identically unreachable (min
    # draws 500000 / 5000 / 50000 all > 3-4); S10 has no such cells, so no
    # entries are added (the refusal table is keyed on REAL cells).
}


# [MDSPEC][R4-8-S10] the SPEC-FIXED interval-tier periods (eligible events),
# mirrored from chaos_lsu_trigger.hh ChaOSLsuTrigger::intervalEvents(). The
# minimum first fire for tier T is interval(T)/2 (scheduleNext: from +
# iv/2 + rng % iv). Kept in lockstep with the header by the S10 contract
# test (tests/test_lsu_hook_s10_span.py) — a drift here would silently
# mis-gate every interval-tier cell.
LSU_INTERVAL_EVENTS = {"F1": 1000000, "F2": 100000, "F3": 10000,
                       "F4": 100000}


def _lsqfwd_tier_flags(model, tier, wl_binary=None):
    if tier == "F0":
        span = LSQFWD_F0_SPAN.get((model, wl_binary))
        if span is None:
            return None   # resolve_cell turns this into a loud BLOCKED cell
        # warmup=1: see the uniform-parameterization note above.
        return ["--lsqfwd_lsu_tier", tier,
                "--lsqfwd_warmup_events", "1",
                "--lsqfwd_span_events", str(span)]
    # [MDSPEC][R4-8-S10] interval-tier (F1-F4) reachability: a (model, tier,
    # workload) whose tier can never fire because the measured eligible
    # stream is shorter than the tier's MINIMUM first draw refuses LOUDLY
    # with its own reason string (resolve_cell passes it through) — never a
    # silent run that would report a hollow activated=0. No re-tuning of the
    # spec-fixed interval (that would alter fault-model semantics).
    if (model, tier, wl_binary) in LSQFWD_INTERVAL_UNREACHABLE:
        iv = LSU_INTERVAL_EVENTS.get(tier)
        stream = LSQFWD_F0_SPAN.get((model, wl_binary))
        return ("BLOCKED(interval-tier-unreachable: model %s tier %s on "
                "workload %s — the tier's SPEC-FIXED first-fire draw is "
                "U[%s/2, 3*%s/2) = at least %s eligible events, but the "
                "measured eligible stream is %s; the interval may NOT be "
                "re-tuned to the workload (that alters fault-model "
                "semantics — see LSQFWD_INTERVAL_UNREACHABLE); needs a "
                "re-scoped long carrier or a cell ruling, R4-8-S10)"
                % (model, tier, wl_binary,
                   "F2", "F2", iv // 2 if iv else "n/a",
                   stream if stream is not None else "n/a"))
    # F1-F4/F5/F6 do not consume span_events (interval/warm-up/event-based);
    # keep the historical inert values for those tiers.
    return ["--lsqfwd_lsu_tier", tier,
            "--lsqfwd_warmup_events", "0",
            "--lsqfwd_span_events", "1000"]


# [MDSPEC][R4-5.1] cache family C11 (mshr_merge): the eligible stream is the
# L1D's DEMAND-READ MSHR merges — per (model, workload), measured with real
# runs exactly like LSQFWD_F0_SPAN above (tier=F0 + span=1000000 so the draw
# never lands; the CHAOSCache teardown line CHAOS_LSU_TRIGGER eligible= is
# the stream size). Same loud-refusal contract: an unmeasured (model,
# workload) pair never silently reuses another pair's span.
# [MDSPEC][R4-5.2] C12 (mshr_fill_timing) extends the table with its OWN
# stream: the L1D's read fills (non-error READ responses on a non-forward
# MSHR) — a DIFFERENT stream from C11's merges, measured separately per
# (model, workload); a C11 span is never reused for C12.
CACHE_F0_SPAN = {
    # (model, workload binary) -> measured eligible event stream size
    # C11 rows (real runs 2026-10-21, binary ddde342587407b3a, tier=F0
    # warmup=1 span=1000000 so the draw never lands — CHAOS_LSU_TRIGGER
    # teardown eligible= is the stream size; quoted output in
    # docs/gem5-fi/lsu/mdspec/round4_findings.md §R4-5.1)
    ("C11", "cache_dirtyevict"): 3421,     # attempted=10879
    ("C11", "stream_chase"): 4737,         # attempted=32792
    ("C11", "cache_mshr_refetch"): 41091,  # attempted=46957 (aux carrier)
    # C12 rows (real runs 2026-10-21, binary 503f35b7ed049342, same census
    # shape: tier=F0 warmup=1 span=1000000, seed 1 — draw_next_fire=756413
    # never landed, injected=0, SPAN_UNREACHABLE alarm = the census intent;
    # full census commands + quoted teardown lines in round4_findings.md
    # §R4-5.2). The C12 stream is the L1D's read FILLS — a different stream
    # from C11's merges (merges-per-fill ~3.3 on the refetch carrier), so
    # the numbers are NOT comparable across models by design.
    ("C12", "cache_dirtyevict"): 1535,     # attempted=2556
    ("C12", "stream_chase"): 20229,        # attempted=20541
    ("C12", "cache_mshr_refetch"): 12551,  # attempted=13348 (aux carrier)
    # [MDSPEC][R4-5.5] C14 (mshr_busy_leak): DELIBERATELY ABSENT. Its
    # stream exists — the L1D's MSHR RELEASE events (a completed fill whose
    # entry is about to return to the free list) — but this landing session
    # was forbidden to run gem5, so the census could not be performed. An
    # unmeasured (model, workload) F0 pair must refuse LOUDLY
    # (resolve_cell -> BLOCKED(F0-span-unmeasured)) rather than silently
    # reuse C11's merge stream or C12's fill stream: different streams on
    # the same cache, per-pair measurement (the R4-1-review-I2 rule).
    #
    # NOTE: C14's matrix cells are F5 only (C14-F5-W6/W10), so nothing
    # consults these pairs today; they are recorded so a future F0 C14 cell
    # cannot silently reuse another model's number.
    #
    # Integration MUST census these pairs before any C14-F0 cell runs (same
    # shape as the C11/C12 censuses above: tier=F0, warmup=1, span=1000000
    # so the F0 draw never lands; the CHAOSCache teardown
    # CHAOS_LSU_TRIGGER `eligible=` IS the stream size; the
    # SPAN_UNREACHABLE alarm is the census intent):
    #   build/ARM/gem5.opt --outdir=runs/lsu/r4_t55_span/<wl> \
    #     configs/se/lsu_proxy.py --cmd workloads/directed/<wl> --cpu O3 \
    #     --chaos_l1d --l1d_target_field mshr_busy_leak \
    #     --l1d_lsu_tier F0 --l1d_warmup_events 1 \
    #     --l1d_span_events 1000000 --l1d_max_faults 1 --l1d_rng_seed 1 \
    #     --chaos_propagation --prop_run_id C14-SPAN-<wl> \
    #     --prop_sample_run_id s1
    #   # <wl> ∈ {cache_dirtyevict (W6), stream_chase (W10)}.
    #   # <wl> ∈ {cache_dirtyevict (W6), stream_chase (W10)}; the C15 pair
    #   # uses the same command with --l1d_target_field mshr_occupancy and
    #   # the run-id C15-SPAN-<wl>.
    # Then set here:
    #   ("C14", "cache_dirtyevict"): <eligible from the W6 run>,
    #   ("C14", "stream_chase"):    <eligible from the W10 run>,
    #
    # [MDSPEC][R4-5.6] C15 (mshr_occupancy): also DELIBERATELY ABSENT. Its
    # stream is the new-miss allocations that reach the queue's capacity
    # limit (a DIFFERENT stream from C14's releases and from C11's merges /
    # C12's fills). C15 HAS F0 cells (C15-F0-W6/W10), so integration MUST
    # census this pair before either can run; until then they refuse loudly
    # (and are additionally MODEL_BLOCKED):
    #   ("C15", "cache_dirtyevict"): <eligible from the W6 run>,
    #   ("C15", "stream_chase"):    <eligible from the W10 run>,
    # [MDSPEC][R4-5.6 integration] C15 census (tier=F0, warmup=1,
    # span=1000000 pure-census, integration binary 0f39ec559a2cbdb1):
    #   cache_dirtyevict: CHAOS_LSU_TRIGGER tier=F0 attempted=3  eligible=3
    #   stream_chase    : CHAOS_LSU_TRIGGER tier=F0 attempted=11 eligible=11
    # (both with SPAN_UNREACHABLE = census intent). The C15 stream is its
    # own stream (new-miss allocations at the capacity limit), not C14/
    # C11/C12's.
    ("C15", "cache_dirtyevict"): 3,
    ("C15", "stream_chase"): 11,}


def _cache_tier_flags(model, tier, wl_binary=None):
    # Legacy cache models (C01-C10/P07/P09) ride the legacy firstClock
    # mechanism — no LSU trigger flags (byte-identical to the old []).
    if model not in ("C11", "C12", "C14", "C15", "O04", "O05", "O09"):
        return []
    # C11 mshr_merge / C12 mshr_fill_timing / C14 mshr_busy_leak / C15
    # mshr_occupancy / O04 rmw_mux / O05 rmw_order / O09 rmw_latch: a tier
    # is REQUIRED (the injector panics on 'off').
    #
    # [MDSPEC][R4-9-FSMC] The RMW models' eligible stream is the mounted
    # L1D's atomic-RMW COMMITS (BaseCache::satisfyRequest's SwapReq branch,
    # the same event base.cc counts as ChaOSLsuEvent::CasSuccess) — a
    # DIFFERENT stream from C11's merges / C12's fills / C14's releases /
    # C15's capacity allocations, so it is per-(model, workload) measured
    # like every other stream and is DELIBERATELY ABSENT from CACHE_F0_SPAN
    # until integration runs the census (an unmeasured F0 pair must refuse
    # LOUDLY, never silently reuse another model's stream — the
    # R4-1-review-I2 rule):
    #   build/ARM/gem5.opt --outdir=runs/lsu/r4_9_span/<wl> \
    #     configs/se/lsu_proxy.py --cmd workloads/directed/<wl> --cpu O3 \
    #     --chaos_l1d --l1d_target_field rmw_mux --l1d_rmw_rule swap_oldnew \
    #     --l1d_lsu_tier F0 --l1d_warmup_events 1 --l1d_span_events 1000000 \
    #     --l1d_max_faults 1 --l1d_rng_seed 1 \
    #     --chaos_propagation --prop_run_id O04-SPAN-<wl> --prop_sample_run_id s1
    #   # (--l1d_target_field rmw_latch/--l1d_rmw_rule result_old for O09,
    #   #  rmw_order/lost for O05; the teardown CHAOS_LSU_TRIGGER eligible=
    #   #  IS the stream size and the SPAN_UNREACHABLE alarm is the census
    #   #  intent). Then set e.g. ("O04", "<wl>"): <eligible> here.
    if tier == "F0":
        span = CACHE_F0_SPAN.get((model, wl_binary))
        if span is None:
            return None   # resolve_cell turns this into a loud BLOCKED cell
        # warmup=1 + span=N: the TRUE F0-uniform parameterization
        # (LSQFWD_F0_SPAN note above applies verbatim).
        return ["--l1d_lsu_tier", tier,
                "--l1d_warmup_events", "1",
                "--l1d_span_events", str(span)]
    # F2/F4/F5/F6 do not consume span_events (interval/burst/event-based);
    # inert values, lsqfwd convention.
    return ["--l1d_lsu_tier", tier,
            "--l1d_warmup_events", "0",
            "--l1d_span_events", "1000"]


# [MDSPEC][R4-5.4] prefetch family P06 (p06_as_demand): the eligible stream
# is the mounted cache's PREFETCH-OWNED FILLS (Cache::serviceMSHRTargets
# setPrefetched gate, from_pref && !from_core && blk) — per (model,
# workload), to be measured with real runs exactly like LSQFWD_F0_SPAN/
# CACHE_F0_SPAN above (tier=F0 + span=1000000 so the draw never lands;
# the CHAOSPrefetch teardown CHAOS_LSU_TRIGGER eligible= is the stream
# size; SPAN_UNREACHABLE alarm = the census intent). Same loud-refusal
# contract: an unmeasured (model, workload) pair never silently reuses
# another pair's span.
#
# P06 rows are UNMEASURED at landing time (R4-5.4 landed in a worktree
# forbidden from running pilots — integration must run the census and
# fill both entries before any P06-F0 cell runs). Census command per
# workload binary <wl> (mirror of the C12 census shape):
#   build/ARM/gem5.opt --outdir=runs/lsu/r4_t54_span/<wl> \
#     configs/se/lsu_proxy.py --cmd workloads/directed/<wl> --cpu O3 \
#     --chaos_prefetch --prefetch_mode p06_as_demand \
#     --prefetch_lsu_tier F0 --prefetch_warmup_events 1 \
#     --prefetch_span_events 1000000 --prefetch_max_faults 1 \
#     --prefetch_rng_seed 1 \
#     --chaos_propagation --prop_run_id P06-SPAN-<wl> \
#     --prop_sample_run_id s1
PF_F0_SPAN = {
    # (model, workload binary) -> measured eligible event stream size
    #
    # [R4-5.4 integration] MEASURED 2026-10-21 on binary
    # 2c5a03913bebfcae with the census command above (span=1e6 so the F0
    # draw can never land; the teardown `eligible=` is therefore the whole
    # golden stream, and the SPAN_UNREACHABLE alarm confirms the census
    # intent). Raw teardown lines:
    #   cache_dirtyevict: injector=CHAOSPrefetch tier=F0 attempted=56
    #     eligible=56 injected=0 ... ALARM mode=SPAN_UNREACHABLE
    #     draw_next_fire=756413 span=1000000 warmup=1
    #   prefetch_stride : injector=CHAOSPrefetch tier=F0 attempted=32
    #     eligible=32 injected=0 ... ALARM mode=SPAN_UNREACHABLE
    #     draw_next_fire=756413 span=1000000 warmup=1
    # (same seed-1 draw across both, as expected for warmup=1 + span=1e6.)
    # Per-pair keying, not a family constant (R4-1-review-I2).
    ("P06", "cache_dirtyevict"): 56,   # W6
    ("P06", "prefetch_stride"): 32,    # W8
}


def _prefetch_tier_flags(model, tier, wl_binary=None):
    # [MDSPEC][R4-5.4] P06 (p06_as_demand): per-(model, workload) F0 span
    # (PF_F0_SPAN above — R4-1-review-I2 uniform parameterization:
    # warmup=1 + span=N hits each of the N eligible events with
    # probability 1/N). Unmeasured pair -> None -> resolve_cell's loud
    # BLOCKED(F0-span-unmeasured) cell.
    if model == "P06" and tier == "F0":
        span = PF_F0_SPAN.get((model, wl_binary))
        if span is None:
            return None
        return ["--prefetch_lsu_tier", tier,
                "--prefetch_warmup_events", "1",
                "--prefetch_span_events", str(span)]
    # P01-P08 keep the historical tier flags BYTE-IDENTICAL (their F0
    # span convention predates the per-pair census — untouched).
    return ["--prefetch_lsu_tier", tier,
            "--prefetch_warmup_events", "0", "--prefetch_span_events", "50"]


def _fsmc_tier_flags(model, tier, wl_binary=None):
    """[MDSPEC][R4-9-FSMC-A] 多核 FS litmus 上 O01/O02/O03 的 F 档位表达。

    只用 CHAOSExMon **真正消费**的旋钮（源码级事实：CHAOSExMon.cc 的构造函数
    读 probability / firstClock / lastClock / maxFaults / rngSeed / writeLog；
    `lsuTier` / `lsuWarmupEvents` / `lsuSpanEvents` 只在 CHAOSExMon.py 里声明，
    在 .hh/.cc 里 **0 次**出现）。所以：
      F0（单次瞬态）→ --exmon_max_faults 1
      F5（永久）    → --exmon_max_faults 0（无限）
    其余档位在这里**大声拒绝**（返回 None），resolve_cell 会把它变成 blocked
    理由，而不是悄悄用 maxFaults=1 冒充——这正是本轮的纪律要求。
    """
    if tier == "F0":
        # FAMILY_MOUNT 已经给了 --exmon_max_faults 1（单次瞬态）；这里不再
        # 重复一次，免得同一 flag 出现两遍（argparse last-wins 会掩盖笔误）。
        return []
    if tier == "F5":
        return ["--exmon_max_faults", "0"]
    return None


def _fsmc_tier_block_reason(tier):
    """resolve_cell 用的 F 档位门理由（与 _fsmc_tier_flags 同源，不会漂移）。"""
    return ("blocked(fsmc-trigger: %s 的档位语义在 CHAOSExMon 里**未实现**"
            "（lsuTier/lsuWarmupEvents/lsuSpanEvents 在 CHAOSExMon.py 有声明、"
            "在 .hh/.cc 里 0 次出现；inWindow() 只有 firstClock/lastClock 的"
            "**时钟**窗，事件计数只有内部 geometric(0.1) 首跳）；F2 的 "
            "interval 语义（chaos_trigger.hh，260000 cycles）与 F6 的"
            "确定性路径层都没有可落地旋钮 ⇒ 无法诚实表达，保持 BLOCKED"
            "（F0/F5 已可由 maxFaults=1/0 表达）。见 R4-9-FSMC-A 报告 §4)"
            % tier)


FAMILY_TIER_FLAGS = {
    # [MDSPEC][R4-5.8] model-aware since A07: the A07-F0 arm consults
    # ADDRPATH_F0_SPAN (loud refusal on unmeasured pairs, the
    # LSQFWD_F0_SPAN contract); every other addrpath model is
    # byte-identical to the pre-A07 family lambda.
    "addrpath": _addrpath_tier_flags,
    # [MDSPEC][R4-1-review-I2] per-(model, workload) F0 span (see
    # LSQFWD_F0_SPAN above). This lambda appends AFTER FAMILY_MOUNT and
    # argparse takes the LAST occurrence, so the span must be fixed HERE (a
    # FAMILY_MOUNT override would be silently clobbered — verified by
    # experiment in R4-1).
    "lsqfwd": _lsqfwd_tier_flags,
    # [MDSPEC][R4-5.1] C11 mshr_merge is LSU-trigger-native; all other
    # cache models keep the legacy firstClock path (byte-identical []).
    "cache": _cache_tier_flags,
    # [MDSPEC][R4-5.4] P06 needs the per-(model, workload) F0 span
    # (PF_F0_SPAN loud refusal); P01-P08 tier flags stay byte-identical
    # (see _prefetch_tier_flags).
    "prefetch": _prefetch_tier_flags,
    "exmon": lambda model, tier, wl_binary=None: [],   # legacy window path
    # [MDSPEC][R4-9-FSMC-A] 多核 FS litmus 上的 exmon：F 档位**只用
    # CHAOSExMon 真正消费的旋钮**表达，不传 lsuTier（该参数在
    # CHAOSExMon.py 里有声明、在 .hh/.cc 里 0 次出现 ⇒ 传了就是"声称一个
    # 没实现的窗"，正是半接线）。F0 → --exmon_max_faults 1（单次瞬态，与
    # FAMILY_MOUNT 同值，显式重述）；F5 → --exmon_max_faults 0（无限 =
    # 永久）。其余档位在 resolve_cell 里被 F 档位门挡住，走不到这里。
    "exmon-fsmc": _fsmc_tier_flags,
}
FAMILY_MOUNT = {
    "addrpath": ["--chaos_addrpath"],
    "lsqfwd": ["--chaos_lsqfwd"],
    "cache": ["--chaos_l1d", "--l1d_first_clock", "1000", "--l1d_max_faults", "1"],
    # [MDSPEC][H5-fix] span_events=1: default 1000 > eligible events (~133
    # on prefetch_stride) → F0 trigger never fires (P01-W8 root cause).
    # span=1 guarantees injection on first eligible event (mdspec pilot).
    # Full 385-sample campaign should re-tune per workload eligible count.
    "prefetch": ["--chaos_prefetch", "--prefetch_max_faults", "1",
                  "--prefetch_span_events", "1"],
    "exmon": ["--chaos_exmon", "--exmon_first_clock", "1000", "--exmon_max_faults", "1"],
    # [MDSPEC][R4-9-FSMC-A] --exmon_max_faults 在这里是 F0 的默认值；F5 由
    # _fsmc_tier_flags 追加一次覆盖（argparse last-wins，与 lsqfwd 的 span
    # 覆盖同一约定，见 FAMILY_TIER_FLAGS 上方注释）。
    "exmon-fsmc": ["--chaos_exmon", "--exmon_first_clock", "1000",
                    "--exmon_max_faults", "1"],
}
# Seed flag per family (findings lesson: injectors take --<inj>_rng_seed,
# lsqfwd takes the generic --rng_seed).
FAMILY_SEED = {
    "addrpath": "--addrpath_rng_seed",
    "lsqfwd": "--rng_seed",
    "cache": "--l1d_rng_seed",
    "prefetch": "--prefetch_rng_seed",
    "exmon": "--exmon_rng_seed",
    "exmon-fsmc": "--exmon_rng_seed",
}


def load_matrix(path):
    rows = list(csv.reader(open(path, encoding="utf-8")))
    header = rows[0]
    cells = []
    for r in rows[1:]:
        if len(r) > COL_RUNID and r[COL_RUNID].strip():
            cells.append(r)
    return header, cells


def resolve_cell(cell, allow_blocked=False, evidence_pilot=False):
    """Cell -> (flags list, golden, binary) or (None, None, blocked_reason).

    Every cell resolves to exactly one of: runnable flags, or a blocked/
    deferred/N-A reason string. No cell may resolve to 'not mapped' —
    main() asserts this (CLAUDE.md: half-routed components are rejected).
    FS families (armtlb) resolve to an FS flag set with the tlb_probe
    carrier; their golden is the host-computed payload oracle.

    [MDSPEC][R4-6-T08] allow_blocked=True is the EXPLICIT operator opt-in
    (--allow-blocked-models) that lets a MODEL_BLOCKED model run anyway. It
    exists because the MODEL_BLOCKED entry for a landed-but-unasserted model
    is otherwise a deadlock: the block says "remove me only with real-run
    evidence" while the block itself forbids the run that would produce it
    (measured on this exact branch — see the R4-6-T08 report §"integration
    deadlock"). The block reason is NOT hidden: it is echoed to stdout and
    carried in the cell/run JSON as model_blocked_reason.

    evidence_pilot=True is narrower: only landed T05--T08 modes may use it,
    solely to collect trial evidence.  It never changes formal admission.
    """
    model = cell[COL_MODEL].strip()
    freq = cell[COL_FREQ].strip()
    workload = cell[COL_WORKLOAD].strip()

    # 1. workload-level block (FS / multicore-FS / SPEC license). SPEC stays
    #    blocked even for FS-family models — the license gap is workload-real
    #    and a carrier substitution cannot honor it (T6 decision, honest).
    for key, reason in WL_BLOCKED.items():
        if key in workload:
            # [R4-8-INT 语义合并] 两侧意图相同（SPEC 许可阻塞只对 FS/armtlb
            # 家族生效，且必须按**收窄后的身份键** SPEC_WL_IDENTITY 匹配，
            # 否则 T10-F{0,1,2}-W11 会静默改判到 fs:tlb_probe 载体——该回归
            # 由 test_lsu_w11_spec_residual.py A4 钉住）。取并集：家族判据用
            # ARMTLB_MODELS（本文件下方 FS 家族分支已在用），键用 Agent5 的
            # SPEC_WL_IDENTITY 具名常量（防键/比较式漂移）。
            if model in ARMTLB_MODELS and key == SPEC_WL_IDENTITY:
                return None, None, reason
            if model in ARMTLB_MODELS:
                # TLB-AliasPerm (and any remaining non-SPEC key) carrier:
                # NOT a workload-level blocker for a T-model — the FS carrier
                # serves it, so fall through to the model-level check, which
                # carries the PRECISE reason (FS flag set for T01-T04/T10;
                # "mode unimplemented" for T05/T06/T07; MODEL_BLOCKED for T08).
                # [MDSPEC][R4-8-FS] keyed on ARMTLB_MODELS, not on
                # MODEL_FLAGS["…"]=="armtlb": T05/T06/T07 are deliberately
                # ABSENT from MODEL_FLAGS (their modes do not exist in
                # CHAOSArmTLB), so the old test made them report the
                # misleading "fs-infra: TLB workload needs FS" instead of
                # their real blocker.
                continue
            # [MDSPEC][R4-9-FSMC-A] Atomic-Litmus 对 O01/O02/O03 不再是
            # "没有载体"：载体是 2 核 Ruby/CHI + litmus_free（真机端到端
            # 跑通过）。放行到 3a2 分支，由那里的 **F 档位门**决定该格是否
            # 可跑；不能诚实表达的档位（F2/F6）在那里被拒并给出精确理由。
            if key == "Atomic-Litmus" and model in MODEL_FLAGS \
                    and MODEL_FLAGS[model][0] == "exmon-fsmc":
                continue
            return None, None, reason
    # 2. model-level block / deferral / N-A
    if model in MODEL_BLOCKED:
        pilot_only = evidence_pilot and model in EVIDENCE_PILOT_MODELS
        if not allow_blocked and not pilot_only:
            return None, None, MODEL_BLOCKED[model]
        tag = "evidence-pilot" if pilot_only and not allow_blocked else "allow-blocked"
        print(f"[{tag}] {cell[COL_RUNID]}: running a MODEL_BLOCKED model "
              f"only to collect evidence; reason kept in the output: "
              f"{MODEL_BLOCKED[model]}")
    # 3. model must have a mapping
    if model not in MODEL_FLAGS:
        return None, None, f"NOT-MAPPED(model {model})"
    family, extra = MODEL_FLAGS[model]

    # 3a. FS family: B0 platform + checkpoint restore + tlb_probe carrier
    if family == "armtlb":
        flags = ["--kernel", str(fs_asset("vmlinux")),
                 "--disk", str(fs_asset("ubuntu.img")),
                 "--bootloader", str(fs_asset("boot.arm64")), "--cpu", "O3",
                 "--readfile", str(FS_CARRIER_RC), "--ckpt-first-clock",
                 "--chaos_armtlb", "--tlb_first_clock", "1000",
                 "--tlb_probability", "1.0",
                 "--tlb_max_faults", "1"] + extra
        # [MDSPEC][R4-5.9] T08 walk_pairing is event-normalized: arm the tier
        # from the cell's F column (the walk-issue stream is the eligible
        # stream). The lookup modes (T01-T04/T10) carry NO tier (lsuTier
        # stays "off" — byte-equivalent to the pre-R4-5.9 tree).
        # [MDSPEC][R4-6-T08] the F0 window is pinned from the constants above
        # (same values as the config defaults) so the draw index is auditable
        # straight from the flag list — see the constants' comment.
        if any(w in extra for w in WALK_FAULT_TYPES):
            flags += ["--tlb_lsu_tier", freq,
                      "--tlb_lsu_warmup_events",
                      str(ARMTLB_T08_WARMUP_EVENTS),
                      "--tlb_lsu_span_events", str(ARMTLB_T08_SPAN_EVENTS)]
        else:
            # [MDSPEC][R6-FIXTOOLS] LOOKUP modes (T01-T04/T10 / T05-T07). F0 =
            # the legacy chain already in `flags` (--tlb_max_faults 1 +
            # --tlb_probability 1.0 + seed-varied eligible-event skip), byte-
            # for-byte unchanged (no --tlb_lsu_tier). F1-F6 = the real tier flag
            # landed by R6-FIXCPP 6ec7c5aa (the lookup path now polls
            # lsuTrigger). An unknown tier is refused LOUDLY (never an F0
            # re-label; the six first-wave RunIDs collapsed to three conditions
            # exactly that way before R6-FTIER).
            tier_flags = _armtlb_lookup_tier_flags(freq)
            if tier_flags is None:
                return None, None, _armtlb_lookup_tier_block_reason(model, freq)
            flags += tier_flags
        return flags, TLB_PROBE_GOLDEN, "fs:tlb_probe"

    # 3a2. [MDSPEC][R4-9-FSMC-A] FS family: 2-core Ruby/CHI + litmus_free 载体。
    # 与 3a 的 armtlb 并列，但平台不同（lsu_multicore_fs.py，不是 lsu_b0_fs）；
    # 检查点由 FSMC_CHECKPOINT_ENV 提供（缺省是 R4-8-FSMC 生成的那个 /tmp
    # 产物）——**不存在就在 resolve 阶段大声拒绝**，绝不静默跑一个没有检查点
    # 的配置。
    if family == "exmon-fsmc":
        tier_flags = FAMILY_TIER_FLAGS[family](model, freq)
        if tier_flags is None:
            return None, None, _fsmc_tier_block_reason(freq)
        ckpt = os.environ.get(FSMC_CHECKPOINT_ENV, FSMC_DEFAULT_CHECKPOINT)
        if not Path(ckpt).exists():
            return None, None, (
                f"blocked(fsmc-infra: 2 核 Ruby/CHI 检查点 {ckpt} 不在；"
                f"按 R4-8-FSMC §3 的启动臂重新生成（约 16 min）后设 "
                f"{FSMC_CHECKPOINT_ENV} 指向它)")
        flags = ["--kernel", str(fs_asset("vmlinux")),
                 "--disk", str(fs_asset("ubuntu.img")),
                 "--bootloader", str(fs_asset("boot.arm64")),
                 "--num-cores", "2", "--coherence", "chi", "--cpu", "O3",
                 "--readfile", str(FSMC_CARRIER_RC),
                 "--restore-checkpoint", ckpt]
        flags += FAMILY_MOUNT[family] + extra + tier_flags
        return flags, FSMC_GOLDEN_FINAL, "fs:fsmc-litmus"

    # 4. workload must have an SE binary + golden
    binary = None
    for key, bin_name in WL_BINARY.items():
        if key in workload:
            binary = bin_name
            break
    if binary is None:
        return None, None, f"NOT-MAPPED(workload {workload[:40]})"
    golden = GOLDENS[binary]

    flags = ["--cmd", str(wl_binary_path(binary)), "--cpu", "O3"]
    flags += FAMILY_MOUNT[family]
    # [MDSPEC][R4-1-review-I2] tier flags are per (model, tier, workload):
    # an lsqfwd F0 (model, workload) pair whose eligible stream is
    # UNMEASURED is refused LOUDLY here (a family-wide span constant was the
    # silent-bias root cause; a model-only table is unsound where the
    # stream is workload-dependent — L03: 571 on sq_forward, 18681 on
    # sqlite_like).
    tier_flags = FAMILY_TIER_FLAGS[family](model, freq, binary)
    if isinstance(tier_flags, str):
        # [MDSPEC][R4-8-S10] the family helper may return a READY-MADE
        # BLOCKED(...) reason (e.g. the interval-tier reachability refusal
        # LSQFWD_INTERVAL_UNREACHABLE) — an honest, cell-specific loud block
        # rather than the generic F0-span-unmeasured one below.
        return None, None, tier_flags
    if tier_flags is None:
        # [MDSPEC][R4-5.1] name the family's own span table in the refusal
        # (cache/C11-C12 -> CACHE_F0_SPAN; lsqfwd -> LSQFWD_F0_SPAN;
        # [R4-5.4] prefetch/P06 -> PF_F0_SPAN; [R4-5.8] addrpath/A07 ->
        # ADDRPATH_F0_SPAN).
        span_table = {"cache": "CACHE_F0_SPAN",
                      "lsqfwd": "LSQFWD_F0_SPAN",
                      "prefetch": "PF_F0_SPAN",
                      "addrpath": "ADDRPATH_F0_SPAN"}.get(
                          family, "LSQFWD_F0_SPAN")
        return None, None, (
            "BLOCKED(F0-span-unmeasured: model %s on workload %s — measure "
            "its eligible stream with a real run and set "
            "%s[('%s', '%s')] in tools/lsu_campaign.py; "
            "refusing rather than silently reusing another pair's span)"
            % (model, binary, span_table, model, binary))
    flags += tier_flags
    flags += extra
    return flags, golden, binary


# [LSU][R6-CAMPAIGN] An FS run that overruns its timeout is SIGKILLed mid-write
# and leaves a half-written evidence set: an incomplete gzip stream (no
# end-of-stream trailer — gzip.open().read() raises EOFError: "Compressed file
# ended before the end-of-stream marker was reached") and/or a missing/0-byte
# stats.txt. Either is proof the sample never finished. The salvaged
# Z_SYNC_FLUSH-ed prefix is still evidence, but the sample MUST be marked
# LOUDLY and must NEVER be treated as a complete/valid chain (user instruction
# 2026-10-23; real cases: r6_tlb_C_T08-F0-W4 and r6_tlb_negative2 seed1).
def detect_evidence_truncation(outdir):
    """Detect a mid-write-killed sample. Returns (evidence_truncated, reasons).

    reasons is a loud, human-readable list; it is empty iff the evidence set
    is complete (complete gzip stream OR no stream at all, plus a non-empty
    stats.txt). A stream that is absent is handled by write_chain_report as an
    honest `stream_present: false`; only an *incomplete* stream or a
    missing/0-byte stats.txt is truncation.
    """
    import lsu_prop_fields as PF
    outdir = Path(outdir)
    reasons = []
    evt = outdir / "prop_evt.txt.gz"
    plain = outdir / "prop_evt.txt"
    stream = evt if evt.exists() else (plain if plain.exists() else None)
    if stream is not None:
        try:
            _events, truncated = PF.read_events(stream)
        except Exception as e:            # read_events normally swallows these
            truncated = True
            reasons.append("prop_evt %s unreadable (%r)" % (stream.name, e))
        else:
            if truncated:
                reasons.append(
                    "prop_evt %s incomplete gzip stream (EOF before the "
                    "end-of-stream marker; run killed mid-write)"
                    % stream.name)
    stats = outdir / "stats.txt"
    if not stats.exists():
        reasons.append("stats.txt missing (gem5 never finalized stats)")
    elif stats.stat().st_size == 0:
        reasons.append("stats.txt empty (0 bytes; gem5 never wrote it)")
    return (bool(reasons), reasons)


# =========================================================== [R6-SCAL] chain
# `lsu_chain_check._best_ordered_path` walks `_ancestry` + `_ordered_prefix`
# **once per event**, so its cost is Θ(n · depth). The multicore FS stream
# `runs/lsu/r6_mc_O01-F0-W7/O01-F0-W7/seed1` is a single linear consumer chain
# (222,056 events, depth(i)=i+1, Σdepth = 2.47e10, exactly one leaf), so the
# per-cell chain report burned >27 CPU-minutes without ever writing
# chain_results.json — O-series cells were effectively wedged (Lane L30).
#
# Measured before the fix: check_chain prefix scaling 1.19s @1k, 7.31s @2k,
# 30.9s @4k; cProfile(2k) = `_best_ordered_path` 16.27s of 16.30s total.
#
# `_linear_best_ordered_path` below returns the **same path object-for-object**
# in O(n). It exploits that `_ordered_prefix` is a forward greedy scan:
#   ancestry(child) = ancestry(parent) + [child]
#   ⇒ prefix(child)  = step(prefix_state(parent), child)
# where the state is (next-layer index, last tick, selected events). One
# memoised pass over the parent DAG therefore yields the prefix of every
# event's ancestry in O(1) amortised, and the winner is still the FIRST event
# in the original list order attaining the maximum length — so ties (and hence
# `path_event_ids` / the terminal derived from `path[-1]`) break identically.
#
# It reuses `lsu_chain_check`'s own `LAYERS` / `_layer_of` / `_tick`, so the
# layer mapping can never drift; only the search strategy changes. The shipped
# function stays authoritative for cyclic parent graphs (where `_ancestry`'s
# seen-set walk has no steady-state equivalent) — correctness never depends on
# the optimisation being applicable.
_LINEAR_PATH_LOCK = threading.Lock()
_SHIPPED_BEST_PATH = {}          # module name -> shipped _best_ordered_path


def _shipped_best_ordered_path(mod):
    """The module's shipped `_best_ordered_path` (cached; never our fast one)."""
    fn = _SHIPPED_BEST_PATH.get(mod.__name__)
    if fn is None:
        fn = mod._best_ordered_path
        _SHIPPED_BEST_PATH[mod.__name__] = fn
    return fn


class _ChainCycle(Exception):
    """Cyclic parent graph: fall back to the shipped walk."""


def _linear_best_ordered_path(chain_events, family, module=None):
    """Drop-in, linear-time `lsu_chain_check._best_ordered_path`.

    `module` defaults to `lsu_chain_check`. Returns a list of the very same
    event dicts (identity preserved) that the shipped implementation returns.
    """
    if module is None:
        import lsu_chain_check as module
    layers = module.LAYERS
    layer_of = module._layer_of
    tick_of = module._tick
    n_layers = len(layers)

    by_id = {}
    for e in chain_events:
        eid = e.get("event_id", "")
        if eid != "":                 # same by_id rule as the shipped walk
            by_id[eid] = e
    state = {}                        # id(event) -> (want, last_tick, tuple)
    busy = set()

    def resolve(evt):
        """Greedy state after scanning ancestry(evt) root→evt (iterative)."""
        stack = []
        cur = evt
        while True:
            key = id(cur)
            st = state.get(key)
            if st is not None:
                break
            if key in busy:           # cycle: _ancestry would cut here
                raise _ChainCycle()
            busy.add(key)
            stack.append(cur)
            pid = cur.get("parent_event_id", "")
            nxt = by_id.get(pid) if pid != "" else None
            if nxt is None:
                st = (0, -1, ())      # root: _ordered_prefix's initial state
                break
            cur = nxt
        while stack:
            node = stack.pop()
            want, last_tick, sel = st
            if want < n_layers:       # _ordered_prefix breaks at len(LAYERS)
                layer = layer_of(node, family)
                if layer in layers:
                    idx = layers.index(layer)
                    tick = tick_of(node)
                    if idx == want and tick >= last_tick:
                        st = (want + 1, tick, sel + (node,))
            state[id(node)] = st
            busy.discard(id(node))
        return st

    best = []
    for e in chain_events:
        try:
            sel = resolve(e)[2]
        except _ChainCycle:
            return _shipped_best_ordered_path(module)(chain_events, family)
        if len(sel) > len(best):
            best = sel
    return list(best)


class _LinearPathSwap:
    """把 `lsu_chain_check._best_ordered_path` 换成 O(n) 版本的上下文。

    [R6-FIXD] `check_admission` 内部会再跑一次 `check_chain`（shipped 的
    Θ(n·depth) `_best_ordered_path`）。222k 事件的多核流上这会把 cell 卡死
    —— 与 L30 修 `check_chain_fast` 时实测的同一缺陷。因此**门禁调用也必须
    在同一个线性替换下**进行（语义不变：两个实现返回同一条路径）。
    """

    def __enter__(self):
        import lsu_chain_check as CHAIN
        self._mod = CHAIN
        self._shipped = _shipped_best_ordered_path(CHAIN)
        CHAIN._best_ordered_path = (
            lambda ce, fam: _linear_best_ordered_path(ce, fam, CHAIN))
        return CHAIN

    def __exit__(self, *exc):
        self._mod._best_ordered_path = self._shipped
        return False


def check_chain_fast(events, oracle_outcome=None):
    """`lsu_chain_check.check_chain` with the linear best-path scan installed.

    Only `_best_ordered_path` is substituted (for the duration of this call);
    fault grouping, family inference, edge/layer mapping and every terminal
    rule run the shipped implementation verbatim. The lock keeps the module
    global consistent while campaign workers classify in parallel; both
    implementations return the same path, so the critical section only costs
    wall time, never semantics.
    """
    import lsu_chain_check as CHAIN

    with _LINEAR_PATH_LOCK, _LinearPathSwap():
        return CHAIN.check_chain(events, oracle_outcome=oracle_outcome)


def admission_gate(runid, events, activated, oracle_outcome=None, exit_code=None,
                   containment=None):
    """[LSU][MDSPEC][R6-FIXD] binding 硬门禁：调用**唯一**判定源
    `lsu_chain_check.check_admission`。

    真缺陷（实测）：campaign 此前只用 `check_chain` 记录判定，从不调用
    `check_admission` —— 于是被门禁拒绝的样本照样以一条"完整链"呈现
    （`chain_valid: true` + terminal/provable_to），与"只凭 coverage PASS 就判
    READY"是同一类假象。这里让 campaign 的**最终结论**实际过这道门。

    无激活（activated<=0）时门禁不适用，返回 admitted=None（诚实：不适用，
    不是拒绝也不是通过）。检查器抛错时响亮返回 admitted=False + note，
    绝不静默当作通过。
    """
    import lsu_chain_check as CHAIN
    act = 0
    try:
        act = int(activated or 0)
    except (TypeError, ValueError):
        act = 0
    if act <= 0:
        return {"admitted": None, "path": None, "terminal": None,
                "violations": [], "note": "无激活样本（fault_id≠0 的 inj 事件）"
                                          "——门禁不适用"}
    cont = containment
    if cont is None:
        try:
            cont = CHAIN.containment_from_events(events, str(runid))
        except Exception as exc:            # 门禁输入构造失败必须响亮
            return {"admitted": False, "path": None, "terminal": None,
                    "violations": [f"containment_from_events 失败: {exc!r}"],
                    "note": "门禁输入构造失败——绝不默认通过"}
    bundle = {"run_id": str(runid), "activated": act, "events": list(events),
              "rc": (exit_code if exit_code is not None else 0),
              "oracle_outcome": oracle_outcome, "containment": cont}
    try:
        # 与 check_chain_fast 同一 O(n) 路径替换：check_admission 内部会再跑
        # 一次 check_chain，超大流上若不替换会卡死整个 cell（L30 同源缺陷）。
        with _LINEAR_PATH_LOCK, _LinearPathSwap():
            res = CHAIN.check_admission(bundle)
    except Exception as exc:                # 检查器异常不得静默放行
        return {"admitted": False, "path": None, "terminal": None,
                "violations": [f"check_admission 异常: {exc!r}"],
                "note": "检查器异常——绝不默认通过"}
    return {"admitted": bool(res.get("admitted")), "path": res.get("path"),
            "terminal": res.get("terminal"),
            "violations": list(res.get("violations") or []),
            "reasons": list(res.get("reasons") or []), "note": ""}


def evidence_activated(events):
    """该流是否含真实故障注入（kind=inj 且 fault_id≠0）。"""
    for e in events:
        if e.get("kind") == "inj" and str(e.get("fault_id", "")) not in ("", "0"):
            return 1
    return 0


def write_chain_report(outdir, runid, seed, result, exit_code=None):
    """[MDSPEC][C1] per-sample chain report: join the propagation stream with
    this sample's L5 oracle outcome and persist machine-readable verdicts.

    Evidence discipline (user instruction 2026-10-20 §四):
      * a missing chain_end is NOT a reason to drop the stream — the
        per-node Z_SYNC_FLUSH-ed prefix is salvaged and the report is
        flagged `truncated` (Crash / Abort / Timeout all keep their
        evidence);
      * no stream at all is recorded as `stream_present: false` (an honest
        absence, never a fabricated verdict).

    Returns the report dict (also written to <outdir>/chain_report.json).
    """
    import lsu_prop_fields as PF

    oracle = result.get("outcome") if isinstance(result, dict) else None
    # [LSU][R6-CAMPAIGN] truncation is decided up-front and surfaced in EVERY
    # branch (stream present or absent) — a mid-write kill must be LOUD, never
    # a silently-complete chain.
    evidence_truncated, _trunc_reasons = detect_evidence_truncation(outdir)
    # [R6-FIXD] 与事件流同源：propagation_flags 写 --prop_sample_run_id s<seed>，
    # 报告此前写 str(seed)（"1"）——同一份证据出现两个样本 id，下游 join 错配。
    rep = {"run_id": runid, "sample_run_id": "s%d" % int(seed),
           "oracle_outcome": oracle, "exit_code": exit_code,
           "stream_present": False, "truncated": None, "event_count": 0,
           "faults": {}, "terminal": None, "provable_to": None,
           "beyond": None, "summary": "",
           "evidence_truncated": evidence_truncated,
           "truncation_reason": "; ".join(_trunc_reasons),
           "chain_valid": not evidence_truncated,
           # [R6-FIXD] binding 门禁结论：admitted/certified 只有**实际调用**
           # check_admission 后才为布尔；无激活/无流时保持 None（不适用）。
           "admitted": None, "admission": None, "certified": None,
           # [MDSPEC][R6-FIXTOOLS] runtime lookup-tier capability proof result
           # + the loud tool-side block it produces (old binary / mismatch).
           "lookup_tier_capability":
               (result.get("lookup_tier_capability")
                if isinstance(result, dict) else None),
           "blocked": (bool(result.get("blocked"))
                       if isinstance(result, dict) else False),
           "blocked_reason": (result.get("blocked_reason", "")
                              if isinstance(result, dict) else "")}
    _blocked = bool(rep["blocked"])
    _loud = ("EVIDENCE TRUNCATED: %s | " % rep["truncation_reason"]
             if evidence_truncated else "")
    if _blocked:
        _loud = "BLOCKED (lookup-tier capability): %s | " % rep["blocked_reason"]
    evt = Path(outdir) / "prop_evt.txt.gz"
    if evt.exists():
        events, truncated = PF.read_events(evt)
        # [R6-FIXD] 最终结论必须过 binding 门禁（此前从不调用）。
        _act = evidence_activated(events)
        rep["activate"] = "on" if _act else "off"
        gate = admission_gate(runid, events, _act, oracle, exit_code)
        rep["admission"] = gate
        if _act:
            if evidence_truncated:
                # 截断流上不得认证（与 Lane B 的 containment 口径一致）
                gate = dict(gate, admitted=False,
                            note="截断流：证据不完整，不得在截断流上认证"
                                 "（链形完整也不算）")
                rep["admission"] = gate
            rep["admitted"] = bool(gate["admitted"])
            rep["certified"] = bool(gate["admitted"])
        if _blocked:
            # [MDSPEC][R6-FIXTOOLS] a lookup-tier capability failure is a hard
            # tool-side block: never certified, regardless of the chain verdict.
            rep["admitted"] = False
            rep["certified"] = False
        if rep["admitted"] is False:
            _v = "; ".join((gate.get("violations") or [])[:2]) or (gate.get("note") or "")
            _loud = "NOT ADMITTED: %s | " % _v + _loud
        # [R6-SCAL] same verdict as CHAIN.check_chain, linear in event count —
        # a 222k-event multicore consumer chain otherwise wedges the cell (see
        # _linear_best_ordered_path for the measured defect).
        verdict = check_chain_fast(events, oracle_outcome=oracle)
        rep.update({"stream_present": True, "truncated": truncated,
                    "event_count": len(events), "faults": verdict["faults"]})
        if verdict["faults"]:
            # single-fault campaign: surface the (first) chain at top level
            fid = sorted(verdict["faults"])[0]
            f = verdict["faults"][fid]
            rep.update({"terminal": f["terminal"],
                        "provable_to": f["provable_to"],
                        "beyond": f["beyond"]})
        rep["summary"] = (_loud +
            "%s s%s oracle=%s exit=%s stream=%s truncated=%s events=%d "
            "faults=%d terminal=%s provable_to=%s beyond=%s"
            % (runid, seed, oracle, exit_code, True, truncated,
               len(events), len(verdict["faults"]), rep["terminal"],
               rep["provable_to"], rep["beyond"]))
    else:
        rep["summary"] = (_loud + "%s s%s oracle=%s exit=%s stream=absent "
                          "(no prop_evt.txt.gz — injector not wired or run "
                          "died before the tracer opened)"
                          % (runid, seed, oracle, exit_code))
    Path(outdir).mkdir(parents=True, exist_ok=True)
    (Path(outdir) / "chain_report.json").write_text(
        json.dumps(rep, indent=1, ensure_ascii=False), encoding="utf-8")
    return rep


def classify_run(outdir, stdout_file, golden, exit_code, stderr_file=None):
    """Run L5 classifier on one run's output."""
    cmd = ["python3", str(L5),
           "--run-dir", str(outdir),
           "--stdout", str(stdout_file),
           "--golden", golden,
           "--exit", str(exit_code)]
    if stderr_file and Path(stderr_file).exists():
        cmd += ["--stderr", str(stderr_file)]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    if r.returncode == 0 and "LSU_L5:" in r.stdout:
        try:
            json_str = r.stdout.split("LSU_L5: ", 1)[1].strip()
            return json.loads(json_str)
        except (json.JSONDecodeError, IndexError):
            pass
    return {"outcome": "Unclassified", "error": r.stderr[:200] if r.stderr else "unknown"}


# [R4-6-T08] armtlb injection counting: the injector log carries T08
# one-shot DIAGNOSTIC lines ("Site: arm_tlb_walk_issue_probe" = the walk hook
# was reached; "Site: arm_tlb_lookup_hit_skipped" = the walk-issue-only model
# deliberately did NOT consume the lookup hit). Neither is an injection, so
# counting every "Site: " line overstated T08-F0-W9 as activated=3 when the
# real injection count was 1. Count only lines that record an applied fault.
_ARMTLB_DIAG_SITES = ("arm_tlb_walk_issue_probe",
                      "arm_tlb_lookup_hit_skipped")


def count_armtlb_injections(ilog_path):
    """Number of APPLIED faults in armtlb_injections.log (diagnostics excluded)."""
    try:
        lines = Path(ilog_path).read_text(errors="replace").splitlines()
    except OSError:
        return 0
    return sum(1 for ln in lines
               if "Site: " in ln
               and not any(d in ln for d in _ARMTLB_DIAG_SITES))


def classify_fs_run(outdir, run_stdout, exit_code):
    """L5 classification for one FS (armtlb) run.

    Channels (T3 smoke-verified physics):
      Crash: kernel Oops — guest terminal 'Internal error: Oops' or the gem5
             log 'Kernel oops in guest' (crash_kind=kernel_oops)
      SDC:   tlb_probe oracle line present but wrong — md5 != host-computed
             golden (b6d81...) or rounds ok<10 (some round mismatched)
      Masked: oracle line with golden md5 AND ok==10
      Timeout: driver-killed (handled by caller)
    Injected: armtlb_injections.log 'Site: ' lines (the injector logs
    'Tick: ..., Site: arm_tlb_lookup_hit, ...'); activated=injected
    (near-tautological proxy, same documented class as other injectors).
    """
    import re as _re
    terminal = ""
    tf = outdir / "board.terminal"
    if tf.exists():
        terminal = tf.read_text(errors="replace")
    injected = 0
    ilog = outdir / "armtlb_injections.log"
    if ilog.exists():
        injected = count_armtlb_injections(ilog)
    out = {"injected": injected, "activated": injected,
           "attempted": None, "eligible": None, "checksum": None}
    if "Oops" in terminal or "Kernel oops in guest" in run_stdout:
        out.update(outcome="Crash", crash_kind="kernel_oops")
    else:
        m = _re.findall(r"\[tlb_probe\.rcS\] ([0-9a-f]{32}) rounds ok=(\d+)/10",
                        terminal)
        if m:
            md5, ok = m[-1]
            out["checksum"] = md5
            out["rounds_ok"] = int(ok)
            if md5 != TLB_PROBE_GOLDEN or int(ok) < 10:
                out["outcome"] = "SDC"
            else:
                out["outcome"] = "Masked"
        elif exit_code != 0:
            out.update(outcome="Crash", crash_kind="guest_or_unknown")
        else:
            # clean exit but no oracle line — the guest died between restore
            # and payload (unclassifiable without more evidence; honest)
            out["outcome"] = "Unclassified"
    oc = out["outcome"]
    classes = {k: 0 for k in ("Masked", "Detected/Contained", "SDC",
                              "Crash", "Timeout")}
    if oc in classes and injected:
        classes[oc] = injected
    out["classes"] = classes
    out["mode"] = "FS"
    return out


def count_fsmc_injections(ilog_path):
    """[MDSPEC][R4-9-FSMC-A] CHAOSExMon 的注入计数。

    CHAOSExMon 的每一行注入日志都以 `..., Site: <site>, mode=...` 收尾
    （见 CHAOSExMon.cc 的 write_log 分支），所以按 `Site: ` 计数与 injector
    自身的 faults_injected_count 一致。文件缺失 = 0（注入器未挂载或没触发）。
    """
    p = Path(ilog_path)
    if not p.exists():
        return 0
    n = 0
    for line in p.read_text(errors="replace").splitlines():
        if "Site: " in line:
            n += 1
    return n


def classify_fsmc_run(outdir, run_stdout, exit_code):
    """[MDSPEC][R4-9-FSMC-A] L5 classification for one FS-multicore litmus run.

    通道（与 tools/lsu_campaign.py 的 FS 口径一致，只是 oracle 换成
    litmus_free 的自报行）：
      Crash:        guest 内核 Oops / gem5 报 Kernel oops
      SDC:          出现 **禁出现结果** —— SB forbidden(00) > 0，或 MP
                    flag1_x0_violations > 0，或 atomic violations > 0，或
                    任一 bad>0；或 FINAL 存在但不等于 golden
      Masked:       FINAL == golden（三条禁出现计数全 0）
      Unclassified: 干净退出但没有 FINAL 行（诚实：没有 oracle 就不分类）
    Injected: exmon_injections.log 的 `Site: ` 行数（与其它注入器同一类
    "近同义"代理，见 classify_fs_run 的说明）。
    """
    import re as _re
    terminal = ""
    tf = outdir / "board.terminal"
    if tf.exists():
        terminal = tf.read_text(errors="replace")
    injected = count_fsmc_injections(outdir / "exmon_injections.log")
    out = {"injected": injected, "activated": injected,
           "attempted": None, "eligible": None, "checksum": None}

    def _num(pat, text):
        m = _re.search(pat, text)
        return int(m.group(1)) if m else None

    sb_forb = _num(r"LITMUS free sb hist .*forbidden\(00\)=(\d+)", terminal)
    sb_bad = _num(r"LITMUS free sb hist .*bad=(\d+)", terminal)
    mp_viol = _num(r"LITMUS free mp flag1_x0_violations=(\d+)", terminal)
    at_viol = _num(r"LITMUS free atomic ctr_expect=\d+ violations=(\d+)",
                   terminal)
    finals = _re.findall(r"FINAL=([0-9a-f]{16})", terminal)
    out["oracle_lines"] = {"sb_forbidden": sb_forb, "sb_bad": sb_bad,
                           "mp_violations": mp_viol,
                           "atomic_violations": at_viol,
                           "final": finals[-1] if finals else None}
    if "Oops" in terminal or "Kernel oops in guest" in run_stdout:
        out.update(outcome="Crash", crash_kind="kernel_oops")
    else:
        viol = [v for v in (sb_forb, sb_bad, mp_viol, at_viol)
                if v is not None and v > 0]
        if viol:
            out["outcome"] = "SDC"
        elif finals:
            out["checksum"] = finals[-1]
            out["outcome"] = ("Masked" if finals[-1] == FSMC_GOLDEN_FINAL
                              else "SDC")
        elif exit_code != 0:
            out.update(outcome="Crash", crash_kind="guest_or_unknown")
        else:
            out["outcome"] = "Unclassified"
    oc = out["outcome"]
    classes = {k: 0 for k in ("Masked", "Detected/Contained", "SDC",
                              "Crash", "Timeout")}
    if oc in classes and injected:
        classes[oc] = injected
    out["classes"] = classes
    out["mode"] = "FS"
    return out


# [LSU][R6-CAMPAIGN] A timed-out gem5 child must actually be KILLED and REAPED
# (no orphans holding the checkpoint/outdir), with exit code / signal recorded.
# subprocess.run's TimeoutExpired path killed but left the signal unrecorded;
# this Popen-based helper makes the kill auditable and reaps unconditionally.
# The child leads its own process group (start_new_session=True) so SIGTERM /
# SIGKILL reach any grandchildren too.
def run_gem5(cmd, timeout, out_file, err_file, grace=10):
    """Run gem5, capturing stdout/stderr to files.

    Returns {timed_out, exit_code, signal, stdout, stderr, pid}.
    On timeout: SIGTERM the process group, wait `grace` s, then SIGKILL if it
    survives; wait() to reap either way. `signal` is the signum actually sent
    (None on a clean run); `exit_code` is the (negative) wait status when killed.
    """
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            text=True, start_new_session=True)
    timed_out, used_sig = False, None
    try:
        out, err = proc.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        timed_out = True
        used_sig = int(signal.SIGTERM)
        try:
            os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
        except (ProcessLookupError, PermissionError):
            pass
        try:
            out, err = proc.communicate(timeout=grace)
        except subprocess.TimeoutExpired:
            used_sig = int(signal.SIGKILL)
            try:
                os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
            except (ProcessLookupError, PermissionError):
                pass
            out, err = proc.communicate()
    if proc.returncode is None:          # never leave it unreaped
        proc.wait()
    Path(out_file).write_text(out or "")
    Path(err_file).write_text(err or "")
    return {"timed_out": timed_out, "exit_code": proc.returncode,
            "signal": used_sig, "stdout": out or "", "stderr": err or "",
            "pid": proc.pid}


def run_single_cell(cell, args, seed, outdir):
    """Run one gem5 invocation for a single cell×seed. Returns classification dict."""
    runid = cell[COL_RUNID]
    model = cell[COL_MODEL].strip()

    flags, golden, _binary = resolve_cell(
        cell, allow_blocked=getattr(args, "allow_blocked_models", False),
        evidence_pilot=(getattr(args, "phase", None) == "trial" and
                        model in EVIDENCE_PILOT_MODELS))
    if flags is None:
        return {"outcome": "Blocked", "error": golden}

    family = MODEL_FLAGS[model][0]
    outdir.mkdir(parents=True, exist_ok=True)
    # [MDSPEC][H0] every sample carries the propagation trace + identity
    prop = propagation_flags(runid, seed)
    g5 = str(resolve_g5())

    # ---- FS families (armtlb / exmon-fsmc): checkpoint restore + carrier ----
    # [MDSPEC][R4-9-FSMC-A] exmon-fsmc 与 armtlb 共用这条"FS 跑一趟"的骨架，
    # 差别只有三处：平台 config、检查点来源、注入日志名 —— 全在这里显式分派，
    # 免得两份几乎相同的 subprocess 代码各自漂移。
    if family in ("armtlb", "exmon-fsmc"):
        if family == "armtlb":
            if not args.fs_checkpoint:
                return {"outcome": "Blocked",
                        "error": "FS cells need --fs-checkpoint (B0 cpt)"}
            fs_config = FS_CONFIG
            ckpt_extra = ["--restore-checkpoint", args.fs_checkpoint]
            seed_flag = "--tlb_rng_seed"
            inj_log = "armtlb_injections.log"
        else:
            # 检查点已在 resolve_cell 的 flags 里（来自 FSMC_CHECKPOINT_ENV，
            # 且那里已经确认它存在）；这里不再要求 --fs-checkpoint。
            fs_config = FSMC_CONFIG
            ckpt_extra = []
            seed_flag = FAMILY_SEED[family]
            inj_log = "exmon_injections.log"
        require_fs_assets()   # loud SystemExit + LSU_FS_DIR hint if absent
        cmd = [g5, "--outdir", str(outdir), str(fs_config)]
        cmd += ckpt_extra
        cmd += flags
        cmd += [seed_flag, str(seed)]
        cmd += prop
        # [MDSPEC][R6-FIXTOOLS] requested lookup tier (from the resolved flags):
        # only F1-F6 lookup runs require the runtime capability marker.
        _req_tier = None
        if family == "armtlb" and "--tlb_lsu_tier" in flags:
            _req_tier = flags[flags.index("--tlb_lsu_tier") + 1]
        _cap_required = _req_tier in ARMTLB_LOOKUP_TIERED_TIERS
        # [MDSPEC][C1] FS timeout bookkeeping was the one path that could lose
        # evidence: the outer `timeout` must stay well ABOVE --fs-timeout so
        # the inner cap produces a real campaign-visible Timeout WITH its
        # salvaged prefix (see the except branch below).
        # T03 stuck0/stuck1 alternate by seed parity (both sub-modes sampled)
        if model == "T03":
            i = cmd.index("--tlb_fault_type")
            cmd[i + 1] = "stuck_at_zero" if seed % 2 else "stuck_at_one"
        _r = run_gem5(cmd, args.fs_timeout, outdir / "run.out",
                      outdir / "run.err")
        # [MDSPEC][R6-FIXTOOLS] runtime lookup-tier capability proof. An F1-F6
        # lookup run is only trustworthy if the binary itself printed the
        # CHAOS_LSU_TIER_CAP startup marker with effective == requested and the
        # lookup tier enabled. Missing (old binary) / mismatched / disabled is
        # refused LOUDLY below — never a silent F0-degenerate dataset under an
        # F2/F6 label.
        _cap = (lookup_tier_capability_gate(_req_tier, _r.get("stdout", ""))
                if _cap_required else None)
        _cap_block = bool(_cap and not _cap["ok"])
        if _r["timed_out"]:
            (outdir / "run.err").write_text(
                "TIMEOUT signal=%d exit=%s (process group killed + reaped)"
                % (_r["signal"], _r["exit_code"]))
            # Evidence-preserving timeout (the 6e0dcd52 family): a killed
            # run may already carry injections — read the log and classify
            # Timeout WITH the activated count. The T01 anchor trial hid
            # 2/5 runs per cell this way (injected bit-63 corruptions that
            # survived as slow-progress runs; killed at the 30-min cap with
            # injected=0 — the Timeout channel was silently empty).
            inj = 0
            ilog = outdir / inj_log
            if ilog.exists():
                inj = (count_armtlb_injections(ilog) if family == "armtlb"
                       else count_fsmc_injections(ilog))
            classes = {k: 0 for k in ("Masked", "Detected/Contained", "SDC",
                                      "Crash", "Timeout")}
            classes["Timeout"] = inj
            # [MDSPEC][C1] FS Timeout keeps its evidence: the killed run's
            # Z_SYNC_FLUSH-ed prefix is salvaged and the oracle-joined chain
            # report is written BEFORE returning (user instruction §一.3: a
            # Timeout must still yield prop_evt.txt.gz + chain_report.json;
            # losing it because there is no chain_end is evidence loss).
            _to = {"outcome": "Timeout", "injected": inj, "activated": inj,
                   "classes": classes, "mode": "FS",
                   "timeout_seconds": args.fs_timeout,
                   # auditable reap record: which signal killed it, its status
                   "timeout_signal": _r["signal"],
                   "timeout_exit_code": _r["exit_code"]}
            _to["lookup_tier_capability"] = _cap
            if _cap_block:
                _to["blocked"] = True
                _to["blocked_reason"] = _cap["reason"]
            _to["chain_report"] = write_chain_report(
                outdir, runid, seed, _to, exit_code=None)
            return _to
        exit_code = _r["exit_code"]
        _fsres = (classify_fs_run(outdir, _r["stdout"], exit_code)
                  if family == "armtlb"
                  else classify_fsmc_run(outdir, _r["stdout"], exit_code))
        _fsres["timeout_seconds"] = args.fs_timeout   # effective budget, visible
        _fsres["lookup_tier_capability"] = _cap
        if _cap_block:
            _fsres["blocked"] = True
            _fsres["blocked_reason"] = _cap["reason"]
        _fsres["chain_report"] = write_chain_report(
            outdir, runid, seed, _fsres, exit_code=exit_code)
        return _fsres

    # ---- SE families ----
    cmd = [g5, "--outdir", str(outdir), str(LSU_PROXY)]
    cmd += flags
    cmd += [FAMILY_SEED[family], str(seed)]
    cmd += prop
    # A03 stuck0/stuck1 alternate by seed parity (both sub-modes sampled);
    # swap the mode VALUE in place — the flag sits mid-list, before the
    # seed flag (the first version clobbered --addrpath_rng_seed by writing
    # cmd[-2], losing per-seed variation for A03; caught in code review).
    if model == "A03":
        i = cmd.index("--addrpath_mode")
        cmd[i + 1] = "a03_stuck0" if seed % 2 else "a03_stuck1"

    stdout_file = outdir / "run.out"
    stderr_file = outdir / "run.err"
    # [MDSPEC][R4-8-W1] W1 (MiBench-TC23) gets lsu_runner's frozen SE_W1
    # budget; every other SE carrier keeps the operator's --timeout.
    _se_timeout = (SE_W1_TIMEOUT if str(_binary).endswith("w1_all")
                   else args.timeout)
    _r = run_gem5(cmd, _se_timeout, stdout_file, stderr_file)
    if _r["timed_out"]:
        stderr_file.write_text(
            "TIMEOUT signal=%d exit=%s (process group killed + reaped)"
            % (_r["signal"], _r["exit_code"]))
        # [MDSPEC][C1] a killed run keeps its flushed prefix: build the chain
        # report BEFORE returning, so a Timeout is not evidence loss.
        _to = {"outcome": "Timeout", "injected": 0, "activated": 0,
               "timeout_seconds": _se_timeout,
               "timeout_signal": _r["signal"],
               "timeout_exit_code": _r["exit_code"]}
        _crep = write_chain_report(outdir, runid, seed, _to, exit_code=None)
        _to["chain_report"] = _crep
        return _to
    exit_code = _r["exit_code"]

    # C-series: CHAOSCache logs to cache_injections.log, not stdout — read
    # it for the injection count (223e4b12 fix).
    cache_log = outdir / "cache_injections.log"
    cache_inj = 0
    if cache_log.exists():
        for line in cache_log.read_text(errors="replace").splitlines():
            if "Tick: " in line or "Cycle: " in line:
                cache_inj += 1

    result = classify_run(outdir, stdout_file, golden, exit_code, stderr_file)
    result["timeout_seconds"] = _se_timeout   # effective SE budget, visible
    # [MDSPEC][R4-1-review-I2] surface the injector's LOUD F0 span alarms
    # (CHAOS_LSU_TRIGGER_ALARM, chaos_lsu_trigger.hh summary) into the
    # per-run result so the cell summary prints them — the alarm must be
    # visible in the run's summary, not buried in run.out.
    _alarms = [ln.strip() for ln in
               stdout_file.read_text(errors="replace").splitlines()
               if "CHAOS_LSU_TRIGGER_ALARM" in ln]
    if _alarms:
        result["trigger_alarm"] = _alarms
    if cache_inj > 0 and result.get("injected", 0) == 0:
        # CHAOSCache logs "Tick:"/"Cycle:" lines (no "Site: " lines and no
        # CHAOS_LSU_TRIGGER stdout funnel — the legacy firstClock mechanism),
        # so the classifier's fallback misses it. Recover the FULL L0/L5
        # record from the log count: injected = activated (near-tautological
        # activation, same documented approximation as the other injectors)
        # and the whole run's outcome lands in one class (04 L5 single-run
        # verdict) so the conservation identity holds.
        result["injected"] = cache_inj
        result["activated"] = cache_inj
        oc = result.get("outcome", "Masked")
        if isinstance(result.get("classes"), dict):
            result["classes"][oc] = cache_inj
        result["injection_source"] = "cache_injections.log"
    # [MDSPEC][C1] oracle-joined chain report for this sample (after the
    # cache-log fixup so the oracle is final).
    result["chain_report"] = write_chain_report(
        outdir, runid, seed, result, exit_code=exit_code)
    return result


def build_parser():
    """[LSU][R6-CAMPAIGN] Construct the CLI parser (split out of main() so the
    timeout defaults — FS 2700 / SE 300 — are directly inspectable in tests)."""
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    p.add_argument("--matrix", required=True)
    p.add_argument("--outdir", default="runs/lsu")
    p.add_argument("--max-parallel", type=int, default=4)
    p.add_argument("--cells", help="comma-separated RunIDs to run (default: all)")
    p.add_argument("--allow-blocked-models", action="store_true",
                   help="[MDSPEC][R4-6-T08] explicit opt-in to run cells whose "
                        "MODEL is still in MODEL_BLOCKED (a landed-but-"
                        "unasserted model is otherwise unrunnable by "
                        "construction — the block demands real-run evidence "
                        "while forbidding the run). The block reason is "
                        "echoed to stdout and kept in the cell JSON as "
                        "model_blocked_reason; this flag never unblocks "
                        "anything, it only lets the operator produce the "
                        "evidence.")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--phase", default="trial", choices=["trial", "screening", "main"])
    p.add_argument("--max-seeds-per-cell", type=int, default=10,
                   help="seed cap per cell (05 r13-r15: adaptive targets govern; "
                        "the cap bounds compute when activation is sparse)")
    p.add_argument("--n-seeds", type=int, default=None,
                   help="[deprecated alias] sets --max-seeds-per-cell")
    # Adaptive-sampling knobs (05 r13-r15). Defaults are the spec values;
    # toy-grid verification lowers them explicitly.
    p.add_argument("--trial-target", type=int, default=30,
                   help="trial-phase activated target (05 r13)")
    p.add_argument("--screening-target", type=int, default=385,
                   help="screening-phase activated target (05 r14)")
    p.add_argument("--main-target", type=int, default=5000,
                   help="main-phase activated cap (05 r15)")
    p.add_argument("--wilson-stop-hw", type=float, default=0.02,
                   help="main-phase Wilson 95%% half-width stop (05 r15)")
    p.add_argument("--timeout", type=int, default=SE_TIMEOUT_DEFAULT,
                   help="per-run wall-clock seconds — absolute cap (05 r17; all "
                         "SE workloads run 10-40s, so 300s > 10x any golden)")
    # ---- FS (armtlb family / M3) ----
    p.add_argument("--fs-checkpoint", default=None,
                   help="B0 checkpoint dir — required for T-cell runs. "
                        "[R4-5.9] the previously-cited path "
                        "runs/fs_lsu/boot_b0/cpt.* does NOT exist; the real "
                        "checkpoints on this host are "
                        "runs/lsu/fs_cpt_boot/cpt.237949797015 and "
                        "runs/h7formal/mkckpt/cpt.90000000 (see "
                        "tests/test_lsu_fs_infra.py)")
    p.add_argument("--fs-timeout", type=int, default=FS_TIMEOUT_DEFAULT,
                   help="FS per-run wall-clock cap. [LSU][R6-CAMPAIGN] default "
                        "2700 s = the KNOWN-GOOD budget (1800 s silently killed "
                        "runs that needed longer; runs given 2700 terminated "
                        "cleanly with a complete stream + stats.txt)")
    return p


def main():
    a = build_parser().parse_args()
    if a.n_seeds is not None:
        a.max_seeds_per_cell = a.n_seeds

    header, cells = load_matrix(a.matrix)
    print(f"Loaded {len(cells)} cells from {a.matrix}")

    if a.cells:
        wanted = set(a.cells.split(","))
        cells = [c for c in cells if c[COL_RUNID] in wanted]
        print(f"Filtered to {len(cells)} cells")

    # ---- resolution audit: every cell resolves or is honestly blocked ----
    counts = {}
    unrunnable = []
    runnable = []
    for cell in cells:
        flags, _g, reason = resolve_cell(
            cell, allow_blocked=a.allow_blocked_models,
            evidence_pilot=(a.phase == "trial" and
                            cell[COL_MODEL].strip() in EVIDENCE_PILOT_MODELS))
        if flags is None:
            key = reason.split("(")[0].split(":")[0]
            counts[key] = counts.get(key, 0) + 1
            unrunnable.append((cell[COL_RUNID], reason))
        else:
            runnable.append(cell)
    counts["runnable"] = len(runnable)
    print(f"Resolution: {counts}")
    not_mapped = [r for r in unrunnable if r[1].startswith("NOT-MAPPED")]
    if not_mapped:
        for runid, why in not_mapped[:20]:
            print(f"  NOT-MAPPED: {runid}: {why}", file=sys.stderr)
        sys.exit("REFUSED: unmapped cells present (half-routed grid)")
    if a.dry_run:
        for runid, reason in unrunnable[:80]:
            print(f"  [blocked] {runid}: {reason}")
        print(f"dry-run: runnable={len(runnable)} blocked/deferred/na={len(unrunnable)}")
        return

    outroot = Path(a.outdir)

    def work(cell):
        return run_cell_adaptive(cell, a, outroot)

    # Parallel slots: CLAUDE.md hard cap 4 concurrent gem5 processes (29GB
    # host OOM discipline). Cells run in parallel; the adaptive loop within
    # a cell is sequential (each seed's stop-rule check needs prior results).
    slots = max(1, min(4, a.max_parallel))
    with ThreadPoolExecutor(max_workers=slots) as pool:
        for _runid, line in pool.map(work, runnable):
            print(line)


def run_cell_adaptive(cell, args, outroot):
    """Three-phase adaptive sampling for one cell (05 r13-r15, r16, r19/r20).

    trial:      stop at --trial-target activated (injector-error discovery)
    screening:  stop at --screening-target activated (cell pass/fail)
    main:       stop at Wilson 95% half-width <= --wilson-stop-hw or the
                --main-target activated cap
    All phases additionally respect --max-seeds-per-cell (compute bound;
    stop_reason records which bound fired — never silent).
    F1-F4 cells: multi-activated runs are one cluster (05 r19/r20) — the
    Wilson interval is computed per-RUN (runs-with-SDC / runs); F0/F5/F6
    are per-activated (SDC/activated, 05 r12).
    Seeds are 1..N per cell — common random numbers across cells by
    construction (same seed = same injection-point RNG draws, 05 r16).
    """
    runid = cell[COL_RUNID]
    model = cell[COL_MODEL].strip()
    freq = cell[COL_FREQ].strip()
    clustered = freq in ("F1", "F2", "F3", "F4")
    target = {"trial": args.trial_target,
              "screening": args.screening_target,
              "main": args.main_target}[args.phase]
    classes = {k: 0 for k in ("Masked", "Detected/Contained", "SDC",
                              "Crash", "Timeout")}
    runs, attempted, activated = [], 0, 0
    seed, stop_reason = 0, None
    cell_out = outroot / runid

    while True:
        if activated >= target:
            stop_reason = "%s-target-met" % args.phase
            break
        if seed >= args.max_seeds_per_cell:
            stop_reason = "seed-cap(%d)" % args.max_seeds_per_cell
            break
        if args.phase == "main" and activated > 0:
            hw, _lo, _hi = _wilson_stats(classes, activated, runs, clustered)
            if hw <= args.wilson_stop_hw:
                stop_reason = "wilson-halfwidth(%.4f<=%.2f)" % (hw,
                                                            args.wilson_stop_hw)
                break
        seed += 1
        r = run_single_cell(cell, args, seed, cell_out / f"seed{seed}")
        act = int(r.get("activated", 0) or 0)
        # [MDSPEC][R4-6-T08] the opt-in's honesty trail: a sample of a
        # MODEL_BLOCKED model carries its block reason in the cell JSON.
        _chain = r.get("chain_report") or {}
        _entry = {"seed": seed, "cluster_id": "%s#%d" % (runid, seed),
                  "activated": act,
                  "outcome": r.get("outcome", "Unclassified"),
                  "chain": r.get("chain_report"),
                  # [LSU][R6-CAMPAIGN] loud per-sample truncation flag (also in
                  # the nested chain report; surfaced here so it is greppable
                  # without opening the chain).
                  "evidence_truncated": _chain.get("evidence_truncated"),
                  "truncation_reason": _chain.get("truncation_reason", ""),
                  # [R6-FIXD] binding 门禁结论（来自 write_chain_report，真调
                  # check_admission）；None=无激活/不适用。
                  "admitted": _chain.get("admitted"),
                  # effective wall-clock budget this sample actually got
                  "timeout_seconds": r.get("timeout_seconds"),
                  "trigger_alarm": r.get("trigger_alarm")}
        _model = cell[COL_MODEL].strip()
        _evidence_pilot = (getattr(args, "phase", None) == "trial" and
                           _model in EVIDENCE_PILOT_MODELS)
        if getattr(args, "allow_blocked_models", False) or _evidence_pilot:
            _mb = MODEL_BLOCKED.get(_model)
            if _mb:
                _entry["model_blocked_reason"] = _mb
                _entry["admission_status"] = "BLOCKED"
                _entry["evidence_pilot_only"] = bool(_evidence_pilot)
        runs.append(_entry)
        attempted += int(r.get("attempted", 0) or 0)
        activated += act
        oc = r.get("outcome")
        if oc in classes:
            classes[oc] += act

    hw, lo, hi = _wilson_stats(classes, activated, runs, clustered)
    # [R6-FIXD] 分母为 0 的"率"绝不静默报 0.0。attempted=0 而 activated>0 本身
    # 就是计数矛盾（activated 不可能超过 attempted）：必须响亮说出，不得伪装
    # 成一个"0 激活率"。activated=0 时 sdc_rate 同理（None = 不适用）。
    count_contradiction = bool(attempted == 0 and activated > 0)
    if attempted > 0:
        act_rate = round(activated / attempted, 4)
    elif activated == 0:
        act_rate = 0.0                      # 真零（无矛盾）
    else:
        act_rate = None                     # 矛盾：不报数
    sdc_rate = (round(classes["SDC"] / activated, 4) if activated else None)
    rate_note = ""
    if count_contradiction:
        rate_note = (f"计数矛盾：attempted=0 而 activated={activated}"
                     f"（activated 不可能超过 attempted）——activation_rate "
                     f"不适用，绝不报 0.0")
    if not activated:
        rate_note = ((rate_note + "；") if rate_note else "") + \
            "activated=0 → sdc_rate 不适用（n/a），非 0.0"
    cons = (activated == sum(classes.values()))
    result = {
        "runid": runid, "phase": args.phase, "seed_batches": seed,
        "clustered": clustered, "n_runs": len(runs),
        "attempted": attempted, "activated": activated,
        "classes": classes, "sdc_rate": sdc_rate,
        "activation_rate": act_rate,
        "activation_rate_note": rate_note,
        "count_contradiction": count_contradiction,
        "wilson": {"lo": round(lo, 4), "hi": round(hi, 4)},
        "stop_reason": stop_reason, "conservation": "OK" if cons else "VIOLATION",
        # [LSU][R6-CAMPAIGN] the effective budgets this cell ran under (visible,
        # never silently lowered).
        "timeout_budget": {"fs_timeout": getattr(args, "fs_timeout",
                                                  FS_TIMEOUT_DEFAULT),
                           "se_timeout": getattr(args, "timeout",
                                                 SE_TIMEOUT_DEFAULT)},
        "runs": runs,
    }
    if model in MODEL_BLOCKED:
        result["admission_status"] = "BLOCKED"
        result["model_blocked_reason"] = MODEL_BLOCKED[model]
        result["evidence_pilot_only"] = bool(
            getattr(args, "phase", None) == "trial" and
            model in EVIDENCE_PILOT_MODELS)
    cell_out.mkdir(parents=True, exist_ok=True)
    # [MDSPEC][C1] auditable chain artefacts for the cell: the machine-
    # readable array (one entry per sample) plus a human summary. Written
    # even when every sample lacks a stream — "absent" is recorded, not
    # silently omitted.
    chains = [r["chain"] for r in runs if r.get("chain")]
    (cell_out / "chain_report.json").write_text(
        json.dumps({"runid": runid, "samples": chains}, indent=1,
                   ensure_ascii=False), encoding="utf-8")
    lines = ["# chain summary — %s" % runid, "",
             "| seed | oracle | admitted | stream | truncated | evid_truncated | "
             "events | terminal | provable_to | beyond |",
             "|---|---|---|---|---|---|---|---|---|---|"]
    for c in chains:
        lines.append("| %s | %s | %s | %s | %s | %s | %s | %s | %s | %s |" % (
            c.get("sample_run_id"), c.get("oracle_outcome"), c.get("admitted"),
            c.get("stream_present"), c.get("truncated"),
            c.get("evidence_truncated"), c.get("event_count"),
            c.get("terminal"), c.get("provable_to"), c.get("beyond")))
    (cell_out / "chain_summary.md").write_text("\n".join(lines) + "\n",
                                               encoding="utf-8")
    # [MDSPEC][R4-1-review-I2] per-cell alarm roll-up: any seed's
    # CHAOS_LSU_TRIGGER_ALARM lines print on the campaign console summary
    # and persist in cell_results.json — the loud, unburied drift signal.
    alarm_msgs = ["seed%d: %s" % (rr["seed"], a)
                  for rr in runs
                  for a in (rr.get("trigger_alarm") or [])]
    result["trigger_alarms"] = alarm_msgs
    # [LSU][R6-CAMPAIGN] loud roll-up of mid-write-killed samples (incomplete
    # stream / missing stats.txt): the cell summary must SHOUT, never bury it.
    trunc_msgs = ["seed%d: %s" % (rr["seed"], rr.get("truncation_reason", ""))
                  for rr in runs if rr.get("evidence_truncated")]
    result["evidence_truncated_samples"] = trunc_msgs
    # [R6-FIXD] cell 级门禁结论：由**实际调用的** check_admission 结论汇总，
    # 绝不由 chain 形状推断。截断证据优先（不完整流不得认证）。
    _act_samples = [e for e in runs if int(e.get("activated") or 0) > 0]
    if not _act_samples:
        _gate_status = "NO-ACTIVATION"
    elif any(e.get("evidence_truncated") for e in _act_samples):
        _gate_status = "EVIDENCE-TRUNCATED"
    elif all(e.get("admitted") is True for e in _act_samples):
        _gate_status = "ADMITTED"
    else:
        _gate_status = "GATE-REFUSED"
    # 模型级阻塞（MODEL_BLOCKED）是**独立**的上游阻塞，门禁汇总不得覆盖它；
    # 两者分列（admission_status 记上游阻塞，admission_gate_status 记门禁）。
    result["admission_gate_status"] = _gate_status
    if result.get("admission_status") != "BLOCKED":
        result["admission_status"] = _gate_status
    (cell_out / "cell_results.json").write_text(json.dumps(result, indent=1))
    line = ("  %s: phase=%s n_runs=%d attempted=%s activated=%d sdc=%s "
            "act_rate=%s stop=%s cons=%s budget[fs=%ss se=%ss]" %
            (runid, args.phase, len(runs), attempted, activated,
             classes["SDC"] if activated else "n/a",
             act_rate if act_rate is not None else "n/a（不适用）",
             stop_reason, result["conservation"],
             result["timeout_budget"]["fs_timeout"],
             result["timeout_budget"]["se_timeout"]))
    if count_contradiction:
        # 响亮：绝不把计数矛盾静默成一个"0 激活率"
        line += "\n  COUNT-CONTRADICTION %s: %s" % (runid, rate_note)
    if alarm_msgs:
        line += "\n  ALARM %s: %d trigger alarm(s): %s" % (
            runid, len(alarm_msgs), " | ".join(alarm_msgs))
    if trunc_msgs:
        line += "\n  EVIDENCE-TRUNCATED %s: %d sample(s) killed mid-write " \
                "(NOT a complete chain): %s" % (
                    runid, len(trunc_msgs), " | ".join(trunc_msgs))
    return runid, line


def _wilson_stats(classes, activated, runs, clustered):
    """Wilson 95% on the SDC rate; F1-F4 clusters per-run (05 r19/r20)."""
    if clustered:
        k = sum(1 for r in runs if r["outcome"] == "SDC")
        n = len(runs)
    else:
        k, n = classes["SDC"], activated
    lo, hi, _p = wilson_ci(k, n)
    return (hi - lo) / 2, lo, hi


if __name__ == "__main__":
    main()
