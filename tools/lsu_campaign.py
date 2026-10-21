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
import subprocess
import sys
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
# Workload-level structural blocks (README §8.3 — 65 cells on W1/W4/W7/W13,
# plus SPEC-license W11). Matched by keyword on the workload column.
WL_BLOCKED = {
    "MiBench": "blocked(fs-infra: SE has no MiBench FS pipeline)",
    "TLB-AliasPerm": "blocked(fs-infra: TLB workload needs FS)",
    "Atomic-Litmus": "blocked(multicore-fs: litmus needs multi-core FS)",
    "PARSEC": "blocked(multicore-fs: PARSEC needs multi-core FS)",
    "SPEC": "blocked(spec-license: SPEC CPU2017 needs a license)",
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
    # [LSU][MDSPEC][A6] A06（规格名，2026-10-19 计划 §2 裁决）：a06_size =
    # A06-a store 侧安全路径（store 短写架构合法；load 候选 REJECT 留证）。
    # A06 RunID 在 load 侧 + byte-enable 实现并实证前保持 MODEL_BLOCKED；
    # 旧名 a06s_store_size 为被拒别名（不得私改模型 ID，无 A06S RunID 族）。
    "A06": ("addrpath", ["--agu_pre_mode", "a06_size", "--agu_size_to", "2"]),
    "A08": ("addrpath", ["--agu_pre_mode", "a08_subst"]),
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
    "O01": ("exmon", ["--exmon_mode", "o01_monitor_addr_bitflip"]),
    "O02": ("exmon", ["--exmon_mode", "o02_monitor_state_corrupt"]),
    "O03": ("exmon", ["--exmon_mode", "stxr_force_fail"]),  # status-flip semantics
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
}

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
    # [MDSPEC][R4-5.4] P06 removed from this table: the prefetch-as-demand
    # fill-classification marking (P06-a forward arm) is implemented
    # (--prefetch_mode p06_as_demand, CHAOSPrefetch maybeMarkFillAsDemand
    # at Cache::serviceMSHRTargets' setPrefetched gate). UNLIKE C11/C12/L04
    # there is NO real-run evidence yet — this landing is compile-
    # unverified and pilot-pending (integration owns build + campaign);
    # the F0 cells stay loudly blocked on the PF_F0_SPAN census until the
    # spans are measured, so no unmeasured cell silently runs.
    "S10": "deferred(consumer-side: StoreSet SSID corruption event source only)",
    "C14": "deferred(consumer-side: MSHR busy event source only)",
    "C15": "deferred(consumer-side: MSHR occupancy event source only)",
    # no clean hook (documented in injector headers / W4-W8 session notes)
    "A07": "deferred(R4: no clean hook)",
    "O04": "deferred(RMW data path needs cache-side SwapResp hook)",
    "O09": "deferred(RMW operand path needs cache-side hook)",
    # B0 protection rows (09 §6.4): not applicable, never zero-filled
    "S12": "不适用(B0无保护)",
    "T09": "不适用(B0无保护)",
    "C13": "不适用(B0无保护)",
    "O08": "不适用(B0无保护)",
    # TLB models: T05-T08 modes NOT yet implemented in CHAOSArmTLB (W7
    # follow-up — M3 plan Task 7 Step 3); T01-T04/T10 are mapped (armtlb
    # family above), T09 is B0-N/A below. The old blanket T01-T10 block
    # fired before MODEL_FLAGS and masked the new FS routing (dry-run caught).
    "T05": "deferred(mode unimplemented: valid/global/ASID state)",
    "T06": "deferred(mode unimplemented: permission legal-substitution)",
    "T07": "deferred(mode unimplemented: hit fabrication/way select)",
    "T08": "deferred(mode unimplemented: walk pairing)",
}
# O05-O07 are multicore-semantic models — their cells sit on Atomic-Litmus/
# PARSEC (workload-blocked); add the model-level reason for robustness.
MODEL_BLOCKED.update({
    "O05": "blocked(multicore-fs: RMW ordering needs multi-core)",
    "O06": "blocked(multicore-fs: barrier completion needs multi-core)",
    "O07": "blocked(multicore-fs: order-tag swap needs multi-core)",
    # [LSU][MDSPEC][A6] A06 专项裁决（计划 §2.d，2026-10-19）：store 侧安全
    # 路径已实现（a06_size，load 候选 REJECT 留证）；load 侧（定宽完成断言，
    # 需 Request 契约 spike）与 A06-b byte-enable（钩子处 const，需 packet
    # 构建层）未实现未实证——A06 全部 6 RunID 保持 BLOCKED，不得伪装完成。
    # 解除条件：计划 §2.c 至少一条 load 侧路径通过 spike 验证 + 测试。
    "A06": ("BLOCKED(load-side fixed-width completion contract + byte-enable "
            "pending; store-only path implemented — MDSPEC §2 ruling 2026-10-19)"),
})

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


def _addrpath_tier_flags(tier):
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
}


def _lsqfwd_tier_flags(model, tier, wl_binary=None):
    if tier == "F0":
        span = LSQFWD_F0_SPAN.get((model, wl_binary))
        if span is None:
            return None   # resolve_cell turns this into a loud BLOCKED cell
        # warmup=1: see the uniform-parameterization note above.
        return ["--lsqfwd_lsu_tier", tier,
                "--lsqfwd_warmup_events", "1",
                "--lsqfwd_span_events", str(span)]
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
}


def _cache_tier_flags(model, tier, wl_binary=None):
    # Legacy cache models (C01-C10/P07/P09) ride the legacy firstClock
    # mechanism — no LSU trigger flags (byte-identical to the old []).
    if model not in ("C11", "C12"):
        return []
    # C11 mshr_merge / C12 mshr_fill_timing: a tier is REQUIRED (the
    # injector panics on 'off').
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
    # ("P06", "cache_dirtyevict"): <int>,   # W6 — TO BE MEASURED
    # ("P06", "prefetch_stride"): <int>,    # W8 — TO BE MEASURED
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


FAMILY_TIER_FLAGS = {
    "addrpath": lambda model, tier, wl_binary=None: _addrpath_tier_flags(tier),
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
}
# Seed flag per family (findings lesson: injectors take --<inj>_rng_seed,
# lsqfwd takes the generic --rng_seed).
FAMILY_SEED = {
    "addrpath": "--addrpath_rng_seed",
    "lsqfwd": "--rng_seed",
    "cache": "--l1d_rng_seed",
    "prefetch": "--prefetch_rng_seed",
    "exmon": "--exmon_rng_seed",
}


def load_matrix(path):
    rows = list(csv.reader(open(path, encoding="utf-8")))
    header = rows[0]
    cells = []
    for r in rows[1:]:
        if len(r) > COL_RUNID and r[COL_RUNID].strip():
            cells.append(r)
    return header, cells


def resolve_cell(cell):
    """Cell -> (flags list, golden, binary) or (None, None, blocked_reason).

    Every cell resolves to exactly one of: runnable flags, or a blocked/
    deferred/N-A reason string. No cell may resolve to 'not mapped' —
    main() asserts this (CLAUDE.md: half-routed components are rejected).
    FS families (armtlb) resolve to an FS flag set with the tlb_probe
    carrier; their golden is the host-computed payload oracle.
    """
    model = cell[COL_MODEL].strip()
    freq = cell[COL_FREQ].strip()
    workload = cell[COL_WORKLOAD].strip()

    # 1. workload-level block (FS / multicore-FS / SPEC license). SPEC stays
    #    blocked even for FS-family models — the license gap is workload-real
    #    and a carrier substitution cannot honor it (T6 decision, honest).
    for key, reason in WL_BLOCKED.items():
        if key in workload:
            if model in MODEL_FLAGS and MODEL_FLAGS[model][0] == "armtlb" \
                    and key == "SPEC":
                return None, None, reason
            if model in MODEL_FLAGS and MODEL_FLAGS[model][0] == "armtlb":
                # MiBench / TLB-AliasPerm / GAP carriers: runnable via FS
                continue
            return None, None, reason
    # 2. model-level block / deferral / N-A
    if model in MODEL_BLOCKED:
        return None, None, MODEL_BLOCKED[model]
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
        return flags, TLB_PROBE_GOLDEN, "fs:tlb_probe"

    # 4. workload must have an SE binary + golden
    binary = None
    for key, bin_name in WL_BINARY.items():
        if key in workload:
            binary = bin_name
            break
    if binary is None:
        return None, None, f"NOT-MAPPED(workload {workload[:40]})"
    golden = GOLDENS[binary]

    flags = ["--cmd", str(REPO / "workloads/directed" / binary), "--cpu", "O3"]
    flags += FAMILY_MOUNT[family]
    # [MDSPEC][R4-1-review-I2] tier flags are per (model, tier, workload):
    # an lsqfwd F0 (model, workload) pair whose eligible stream is
    # UNMEASURED is refused LOUDLY here (a family-wide span constant was the
    # silent-bias root cause; a model-only table is unsound where the
    # stream is workload-dependent — L03: 571 on sq_forward, 18681 on
    # sqlite_like).
    tier_flags = FAMILY_TIER_FLAGS[family](model, freq, binary)
    if tier_flags is None:
        # [MDSPEC][R4-5.1] name the family's own span table in the refusal
        # (cache/C11-C12 -> CACHE_F0_SPAN; lsqfwd -> LSQFWD_F0_SPAN;
        # [R4-5.4] prefetch/P06 -> PF_F0_SPAN).
        span_table = {"cache": "CACHE_F0_SPAN",
                      "lsqfwd": "LSQFWD_F0_SPAN",
                      "prefetch": "PF_F0_SPAN"}.get(
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
    import lsu_chain_check as CHAIN
    import lsu_prop_fields as PF

    oracle = result.get("outcome") if isinstance(result, dict) else None
    rep = {"run_id": runid, "sample_run_id": str(seed),
           "oracle_outcome": oracle, "exit_code": exit_code,
           "stream_present": False, "truncated": None, "event_count": 0,
           "faults": {}, "terminal": None, "provable_to": None,
           "beyond": None, "summary": ""}
    evt = Path(outdir) / "prop_evt.txt.gz"
    if evt.exists():
        events, truncated = PF.read_events(evt)
        verdict = CHAIN.check_chain(events, oracle_outcome=oracle)
        rep.update({"stream_present": True, "truncated": truncated,
                    "event_count": len(events), "faults": verdict["faults"]})
        if verdict["faults"]:
            # single-fault campaign: surface the (first) chain at top level
            fid = sorted(verdict["faults"])[0]
            f = verdict["faults"][fid]
            rep.update({"terminal": f["terminal"],
                        "provable_to": f["provable_to"],
                        "beyond": f["beyond"]})
        rep["summary"] = (
            "%s s%s oracle=%s exit=%s stream=%s truncated=%s events=%d "
            "faults=%d terminal=%s provable_to=%s beyond=%s"
            % (runid, seed, oracle, exit_code, True, truncated,
               len(events), len(verdict["faults"]), rep["terminal"],
               rep["provable_to"], rep["beyond"]))
    else:
        rep["summary"] = ("%s s%s oracle=%s exit=%s stream=absent "
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
        injected = sum(1 for ln in ilog.read_text(errors="replace").splitlines()
                       if "Site: " in ln)
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


def run_single_cell(cell, args, seed, outdir):
    """Run one gem5 invocation for a single cell×seed. Returns classification dict."""
    runid = cell[COL_RUNID]
    model = cell[COL_MODEL].strip()

    flags, golden, _binary = resolve_cell(cell)
    if flags is None:
        return {"outcome": "Blocked", "error": golden}

    family = MODEL_FLAGS[model][0]
    outdir.mkdir(parents=True, exist_ok=True)
    # [MDSPEC][H0] every sample carries the propagation trace + identity
    prop = propagation_flags(runid, seed)
    g5 = str(resolve_g5())

    # ---- FS family (armtlb): lsu_b0_fs + checkpoint restore + carrier ----
    if family == "armtlb":
        if not args.fs_checkpoint:
            return {"outcome": "Blocked",
                    "error": "FS cells need --fs-checkpoint (B0 cpt)"}
        require_fs_assets()   # loud SystemExit + LSU_FS_DIR hint if absent
        cmd = [g5, "--outdir", str(outdir), str(FS_CONFIG)]
        cmd += ["--restore-checkpoint", args.fs_checkpoint]
        cmd += flags
        cmd += ["--tlb_rng_seed", str(seed)]
        cmd += prop
        # [MDSPEC][C1] FS timeout bookkeeping was the one path that could lose
        # evidence: the outer `timeout` must stay well ABOVE --fs-timeout so
        # the inner cap produces a real campaign-visible Timeout WITH its
        # salvaged prefix (see the except branch below).
        # T03 stuck0/stuck1 alternate by seed parity (both sub-modes sampled)
        if model == "T03":
            i = cmd.index("--tlb_fault_type")
            cmd[i + 1] = "stuck_at_zero" if seed % 2 else "stuck_at_one"
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True,
                                  timeout=args.fs_timeout)
            (outdir / "run.out").write_text(proc.stdout)
            (outdir / "run.err").write_text(proc.stderr)
            exit_code = proc.returncode
        except subprocess.TimeoutExpired:
            (outdir / "run.out").write_text("")
            (outdir / "run.err").write_text("TIMEOUT")
            # Evidence-preserving timeout (the 6e0dcd52 family): a killed
            # run may already carry injections — read the log and classify
            # Timeout WITH the activated count. The T01 anchor trial hid
            # 2/5 runs per cell this way (injected bit-63 corruptions that
            # survived as slow-progress runs; killed at the 30-min cap with
            # injected=0 — the Timeout channel was silently empty).
            inj = 0
            ilog = outdir / "armtlb_injections.log"
            if ilog.exists():
                inj = sum(1 for ln in
                          ilog.read_text(errors="replace").splitlines()
                          if "Site: " in ln)
            classes = {k: 0 for k in ("Masked", "Detected/Contained", "SDC",
                                      "Crash", "Timeout")}
            classes["Timeout"] = inj
            # [MDSPEC][C1] FS Timeout keeps its evidence: the killed run's
            # Z_SYNC_FLUSH-ed prefix is salvaged and the oracle-joined chain
            # report is written BEFORE returning (user instruction §一.3: a
            # Timeout must still yield prop_evt.txt.gz + chain_report.json;
            # losing it because there is no chain_end is evidence loss).
            _to = {"outcome": "Timeout", "injected": inj, "activated": inj,
                   "classes": classes, "mode": "FS"}
            _to["chain_report"] = write_chain_report(
                outdir, runid, seed, _to, exit_code=None)
            return _to
        _fsres = classify_fs_run(outdir, proc.stdout, exit_code)
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
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True,
                              timeout=args.timeout)
        stdout_file.write_text(proc.stdout)
        stderr_file.write_text(proc.stderr)
        exit_code = proc.returncode
    except subprocess.TimeoutExpired:
        stdout_file.write_text("")
        stderr_file.write_text("TIMEOUT")
        # [MDSPEC][C1] a killed run keeps its flushed prefix: build the chain
        # report BEFORE returning, so a Timeout is not evidence loss.
        _to = {"outcome": "Timeout", "injected": 0, "activated": 0}
        _crep = write_chain_report(outdir, runid, seed, _to, exit_code=None)
        _to["chain_report"] = _crep
        return _to

    # C-series: CHAOSCache logs to cache_injections.log, not stdout — read
    # it for the injection count (223e4b12 fix).
    cache_log = outdir / "cache_injections.log"
    cache_inj = 0
    if cache_log.exists():
        for line in cache_log.read_text(errors="replace").splitlines():
            if "Tick: " in line or "Cycle: " in line:
                cache_inj += 1

    result = classify_run(outdir, stdout_file, golden, exit_code, stderr_file)
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


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--matrix", required=True)
    p.add_argument("--outdir", default="runs/lsu")
    p.add_argument("--max-parallel", type=int, default=4)
    p.add_argument("--cells", help="comma-separated RunIDs to run (default: all)")
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
    p.add_argument("--timeout", type=int, default=300,
                   help="per-run wall-clock seconds — absolute cap (05 r17; all "
                         "SE workloads run 10-40s, so 300s > 10x any golden)")
    # ---- FS (armtlb family / M3) ----
    p.add_argument("--fs-checkpoint", default=None,
                   help="B0 checkpoint dir (runs/fs_lsu/boot_b0/cpt.*) — "
                        "required for T-cell runs")
    p.add_argument("--fs-timeout", type=int, default=1800,
                   help="FS per-run wall-clock cap (05 r17 FS: restore+payload "
                        "~4 min measured, 30 min absolute cap)")
    a = p.parse_args()
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
        flags, _g, reason = resolve_cell(cell)
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
        runs.append({"seed": seed, "cluster_id": "%s#%d" % (runid, seed),
                     "activated": act,
                     "outcome": r.get("outcome", "Unclassified"),
                     "chain": r.get("chain_report"),
                     "trigger_alarm": r.get("trigger_alarm")})
        attempted += int(r.get("attempted", 0) or 0)
        activated += act
        oc = r.get("outcome")
        if oc in classes:
            classes[oc] += act

    hw, lo, hi = _wilson_stats(classes, activated, runs, clustered)
    sdc_rate = (classes["SDC"] / activated) if activated else 0.0
    act_rate = (activated / attempted) if attempted else 0.0
    cons = (activated == sum(classes.values()))
    result = {
        "runid": runid, "phase": args.phase, "seed_batches": seed,
        "clustered": clustered, "n_runs": len(runs),
        "attempted": attempted, "activated": activated,
        "classes": classes, "sdc_rate": round(sdc_rate, 4),
        "activation_rate": round(act_rate, 4),
        "wilson": {"lo": round(lo, 4), "hi": round(hi, 4)},
        "stop_reason": stop_reason, "conservation": "OK" if cons else "VIOLATION",
        "runs": runs,
    }
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
             "| seed | oracle | stream | truncated | events | terminal | "
             "provable_to | beyond |", "|---|---|---|---|---|---|---|---|"]
    for c in chains:
        lines.append("| %s | %s | %s | %s | %s | %s | %s | %s |" % (
            c.get("sample_run_id"), c.get("oracle_outcome"),
            c.get("stream_present"), c.get("truncated"), c.get("event_count"),
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
    (cell_out / "cell_results.json").write_text(json.dumps(result, indent=1))
    line = ("  %s: phase=%s n_runs=%d activated=%d sdc=%d "
            "stop=%s cons=%s" %
            (runid, args.phase, len(runs), activated, classes["SDC"],
             stop_reason, result["conservation"]))
    if alarm_msgs:
        line += "\n  ALARM %s: %d trigger alarm(s): %s" % (
            runid, len(alarm_msgs), " | ".join(alarm_msgs))
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
