#!/usr/bin/env python3
"""Minimal manifest runner for the ARM64 CHAOS SDC campaign (plan §5.1, §13.1).

Flow (plan §13.1): validate manifest/hashes -> start simulator -> deterministic
inject -> collect oracle -> classify -> assert faults_injected in {0,1}.

This runner is the honest baseline: it accepts a single manifest, maps its
fields to the arm_chaos.py config args, runs gem5 once, and classifies the
outcome against a golden (no-injection) reference hash. It does NOT yet do
checkpoint restore or ROI symbol resolution (deferred). The classification
implements the plan §9.1 mutually-exclusive order.

Usage: python3 tools/runner.py <manifest.yaml> <golden_stdout_hash>
"""
import sys, os, json, subprocess, hashlib, argparse, tempfile, gzip

# Shared honest classifier (plan §9.1; report issue #4 fix).
sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
from classify import classify_run  # noqa: E402

try:
    import yaml
except ImportError:
    sys.exit("ERROR: pip install pyyaml  (needed for manifest parsing)")

# jsonschema is optional; if absent, we do a light manual check.
try:
    import jsonschema
    HAVE_SCHEMA = True
except ImportError:
    HAVE_SCHEMA = False

REPO = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
# NOTE: scons builds gem5.opt to the REPO-ROOT build/ARM on this host
# (NOT CHAOS/gem5/build/ARM — that path holds a stale/duplicate file).
G5 = os.path.join(REPO, "build/ARM/gem5.opt")
CFG = os.path.join(REPO, "configs/se/arm_chaos.py")

# Platform config family (design doc §1.1) -> the SE .py harness to run.
# C0 = arm_chaos.py (baseline). C2 = kp920_proxy.py (Kunpeng V110 proxy, E3).
# The campaign driver picks this from the campaign/manifest config_family;
# runner.py defaults to C0 so single-manifest runs are unchanged.
CONFIG_FAMILY = {
    "C0": os.path.join(REPO, "configs/se/arm_chaos.py"),
    "C2": os.path.join(REPO, "configs/se/kp920_proxy.py"),
    # OoO north-star platform (docs/gem5-fi/ooo): vec48 PRF, ROB128, 2.6GHz
    "C3": os.path.join(REPO, "configs/se/ooo_proxy.py"),
    # LSU north-star platform (docs/gem5-fi/lsu): B0 = O3_ARM_v7a_3 基线
    # + DTLB=32 (TC'23), L1D 32KiB/2-way, L2 StridePrefetcher; S1-S4 variants
    "C4-LSU": os.path.join(REPO, "configs/se/lsu_proxy.py"),
    # §2.7 cache injector harness (CHAOSCache mounts via _pre_instantiate)
    "C0-CACHE": os.path.join(REPO, "configs/se/arm_chaos_cache.py"),
    # §2.10 FS harness (CHAOSArmTLB/CHAOSArmSysReg; needs gem5-fs deps)
    "C0-FS": os.path.join(REPO, "configs/se/arm_chaos_fs.py"),
    # §1.1 FS V110 proxy (delegates to arm_chaos_fs; V110 params TODO)
    "C2-FS": os.path.join(REPO, "configs/fs/kp920_proxy_fs.py"),
}

# manifest oracle.golden_id -> the workload's golden (no-injection) checksum.
# These are the no-injection reference outputs (native == gem5, deterministic).
GOLDEN_IDS = {
    "regchain-golden-v1":   "f247ef3fe6f02cfd",  # reg_chain
    # LSU 负载 W0 MiniCheck (W9.1): gem5-SE golden == native (07568da9f3ad5665,
    # C4-LSU 实证 2026-09-25). HONEST: gem5-SE ignores mprotect -> the PROT_NONE
    # guard page stays RW in SE, so the guard-page probe detects corruption via
    # checksum (SDC channel) instead of SIGSEGV (Crash channel); the Crash
    # channel works natively and in FS.
    "minicheck-golden-v1":   "07568da9f3ad5665",  # mini_check
    # LSU W9 SE workloads (all gem5==native, 2026-09-26 verified)
    "agu-addmodes-golden-v1": "728e604ffcec539d",  # agu_addrmodes
    "sq-forward-golden-v1":   "1f4cbf14327717df",  # sq_forward
    "cache-dirtyevict-golden-v1": "062e5124df3667f9",  # cache_dirtyevict
    "prefetch-stride-golden-v1": "629727c0ad9ca8ef",  # prefetch_stride
    "stream-chase-golden-v1": "50ab96a7fe8f6ec2",  # stream_chase
    "beebs-kernels-golden-v1": "a10b9827edd8a9fb",  # beebs_kernels
    "gap-bfs-golden-v1":     "030921682b3731f2",  # gap_bfs
    "sqlite-like-golden-v1": "33f836327a416d35",  # sqlite_like
    # LSU W8 O-series SE verification probe (gem5==native, 2026-09-26).
    # NOT a grid workload — O-cells run on Atomic-Litmus/PARSEC (multicore
    # FS, blocked); this probe is the functional-verification vehicle for
    # the CHAOSExMon O01/O02 modes. Final-data-state checksum by design:
    # monitor faults => transient reservation loss => Masked, not fake-SDC.
    "atomics-probe-golden-v1": "40f6ec03d95241ca",  # atomics_probe
    "l1dreduce-golden-v1":  "f44d2b9cd4a173cd",  # l1d_reduce
    "l1iloop-golden-v1":    "bb0b1c4cb661236e",  # l1i_loop
    "stuckpersist-golden-v1": "00000000dee1f5d0",  # stuck_persist
    # S1 §2.2 method1 anchor + controls (cross-ISA consistent golden):
    "cholesky-golden-v1":   "37621bc0a633976f",  # cholesky_numeric
    "purefma-golden-v1":    "98433fcf09968e6a",  # method1_controls pure_fma
    "purespmv-golden-v1":   "57b2c160bf2c92ad",  # method1_controls pure_spmv
    "puregather-golden-v1": "e4481fb960ff6465",  # method1_controls pure_gather
    "trisolve-golden-v1":   "39d61425aae92434",  # method1_controls tri_solve
    "movheavy-golden-v1":   "61e8a946ed50ae1f",  # mov_heavy (move-elimination)
    "branchyreduce-golden-v1": "d47587240e6f0a83",
    "neon-golden-v1":     "00000000526925fe",
    "fwdchecksum-golden-v1": "ac70ef3a46fd0825",
    "raschecksum-golden-v1": "bcf20e1df7bb0535",
    "spinlockchecksum-golden-v1": "0891b007b53c4869",
    "maddchain-golden-v1": "9e8050e1503c34ab",
    "crcstate-golden-v1": "d27806e62c9d3869",
    "structfield-golden-v1": "afebbd4c86e8cfdf",
    "svditerative-golden-v1": "4afb95b5b32f3820",
    "gemmfloat-golden-v1": "d74f24ae79deb7d2",
    "depchain-golden-v1": "030f101df841bf6e",
    "ptrchase-golden-v1": "af63bd4c8601b7df",
    # ptr_chase_long (2048-node x 4096 rounds, long-lived pointer) — the
    # checksum coincides with ptr_chase_kernel's but the workloads differ;
    # separate id keeps provenance honest.
    "ptrchaselong-golden-v1": "af63bd4c8601b7df",  # spinlock_checksum  # ras_checksum_kernel  # fwd_checksum_kernel  # neon_lane  # branchy_reduce (§2.3)
    # v1.1 Phase 11 (patch 3a): working-set-aware L2/DRAM probes (both
    # print a 16-hex FINAL= line -> exact_hash).
    "stencil5pt-golden-v1": "6216d7bd62318f00",      # stencil W=160
    "streamtriad-golden-v1": "0a3e17d4e5740000",     # triad N=262144 (6MB)
    # OoO track W1 (docs/gem5-fi/ooo; config family C3, workloads/ooo/):
    "branchmispred-golden-v1": "06e84f119c258fa7",  # W1.5a probe kernel
    "depchainint-golden-v1": "98e5e31e726e383f",   # W1.5b int probe kernel
    "depchainvec-golden-v1": "b1e661a247b95774",   # W1.5b NEON probe kernel
    "robfillint-golden-v1": "19eab7d0de27237e",    # W1.5c int probe kernel
    "robfillfp-golden-v1": "85085fd5686d173b",     # W1.5c fp probe kernel
    "coremark-golden-v1": "000000000000cf56",      # W1.1 EEMBC CoreMark ITERATIONS=35
    # W1.2 Embench subset (upstream 09c2ed8c; nbody/minver from pre-2.0
    # commit 92da124b — Embench-IoT 2.0 deleted all FP benchmarks):
    "embenchcrc32-golden-v1": "b87739d9c40d1798",
    "embenchmd5sum-golden-v1": "973ff8cc9018e79f",
    "embenchmatmult-golden-v1": "e105f98022b761ef",
    "embenchwikisort-golden-v1": "d2cf29655e3e0f06",  # replaces qlsort (never existed upstream)
    "embenchnbody-golden-v1": "f39b4e8804f279c3",     # FP, from 92da124b
    "embenchminver-golden-v1": "9792f3ee24af3023",    # FP, from 92da124b (replaces qrsolve)
    # W1.3 PolyBench/C 4.2.1 (mirror MatthiasJReisinger@3e872547, llvm-test-suite
    # cross-verified; fp32, sizes gemm 88^3 / lu 84 / cholesky 88 / jacobi T=8 N=160):
    "polybenchgemm-golden-v1": "116849d3adf3227b",
    "polybenchlu-golden-v1": "74ffe5eb77ea9257",
    "polybenchcholesky-golden-v1": "ea7e0d0e7c86582d",
    "polybenchjacobi2d-golden-v1": "dc867b5f02998c1e",
    "gap-golden-v1": "2ec8c1e59f2808c5",             # W1.4a GAP semantic proxy (BFS=2/PR=2)
    "libjpeg-golden-v1": "c712f8f6fb9e21ec",         # W1.4b libjpeg-turbo NEON decode (rounds=3)
    # W2.3 (registered for the trace two-pass toy campaign): the W1.0 smoke
    # kernel's no-injection FINAL, byte-identical across native/gem5/2 runs
    # (workloads/ooo/README.md W1.0 record; W2 regression golden per the W2
    # plan Global Constraints).
    "smoke-golden-v1": "45737cc9a76c0dce",           # W1.0 smoke kernel (C3 SE)
}

# v1.1 Phase 8.1: golden ARRAY registry — for workloads whose oracle is
# array_hash / per_element_diff / fp_ulp (design doc §1.7). The kernel
# computes the reference itself (per-element diff / ULP against its own
# golden copy) or the golden ARRAYHASH is recorded here. Keys are distinct
# from GOLDEN_IDS (which carry 16-hex FINAL checksums); a non-exact_hash
# manifest resolves its golden through THIS table (or --golden-array).
GOLDEN_ARRAYS = {
    # populated as the v1.1 per-element kernels land (Phase 9-11):
    # "elemwisefma-golden-v1": "<64-hex ARRAYHASH>",
    # v1.1 Phase 8.1 acceptance carrier (temp smoke kernel, /tmp): the
    # gem5-verified no-injection ARRAYHASH (native == gem5, deterministic).
    "oraclesmoke-golden-v1": "3d7ac29a722e5f64b891c26d91c093c7e797a2af304a0506c6c4c69fd50c1739",
    # v1.1 Phase 9 (patch 1b): elemwise_fma N=8192, gem5-verified no-injection
    # ARRAYHASH (native == gem5, deterministic).
    "elemwisefma-golden-v1": "ced113fdd122842d91a79059d75e2a24f55f78de0e043ff761239d5d989f43e7",
    # v1.1 Phase 10 (patch 2a): spec_leak_probe N=4096 — the no-leak golden
    # (leak would shift ARRAYHASH and light ELEMDIFF n>0).
    "specleakprobe-golden-v1": "7cd81e9377b50593d3256d67f01d59d4a9fba940894b0929920406933d3232cf",
    # v1.2 Phase 13 (patch 3): elemwise_int N=8192 (ARRAYHASH oracle).
    "elemwiseint-golden-v1": "ee7df0384b5599c3f1a3c68c5d92637b4cd4bea1b93e866afaed6fbdbcc83b50",
    # v1.2 Phase 13 (patch 4): stale_plausible N=4096 (F6 stale-value probe).
    "staleplausible-golden-v1": "d882ffba81e935f2df1fa7bc46bb4d759627b39a1d932081129bb6403a074cd0",
}

def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1<<16), b""):
            h.update(chunk)
    return h.hexdigest()


# ------------------------- W2.3 trace two-pass helpers -------------------------

def count_trace_lines(path):
    """Count committed-instruction lines in a (gzipped by magic) commit trace.
    Returns None on any read error — honest missing evidence, never a fake 0.
    NOTE: a Crash rep's trace is typically TRUNCATED (gem5 aborts before the
    gzip stream is finalized) — gzip iteration then raises EOFError, which is
    NOT an OSError; both are caught (found live on the bm+rat Crash rep)."""
    try:
        with open(path, "rb") as f:
            magic = f.read(2)
        if magic == b"\x1f\x8b":
            fh = gzip.open(path, "rt", encoding="utf-8", errors="replace")
        else:
            fh = open(path, "rt", encoding="utf-8", errors="replace")
        try:
            return sum(1 for _ in fh)
        finally:
            fh.close()
    except (OSError, EOFError):
        return None


def run_commit_diff(ref_path, run_path):
    """W2.3: diff the run trace against the no-injection ref via
    tools/commit_diff.py (W2.2) and return its five-class JSON dict
    (primary_class / latency_seq / verdict / divergence_counts / ...).

    On ANY failure returns {'l2_error': ...} — never a fabricated verdict:
    the caller merges this dict verbatim into the results.jsonl l2 block, so
    an honest error string is the correct outcome, not a fake no_divergence.
    """
    if not os.path.exists(run_path):
        return {"l2_error": f"run trace missing: {run_path}"}
    if not os.path.exists(ref_path):
        return {"l2_error": f"ref trace missing: {ref_path}"}
    cd = os.path.join(REPO, "tools", "commit_diff.py")
    tmpd = tempfile.mkdtemp(prefix="l2diff-")
    jpath = os.path.join(tmpd, "l2.json")
    env = dict(os.environ)
    env.setdefault("PYTHONHASHSEED", "0")
    try:
        r = subprocess.run([sys.executable, cd, "--ref", ref_path,
                            "--run", run_path, "--json", jpath],
                           capture_output=True, text=True, timeout=600,
                           env=env)
    except subprocess.TimeoutExpired:
        return {"l2_error": "commit_diff exceeded 600s"}
    if r.returncode != 0 or not os.path.exists(jpath):
        return {"l2_error": f"commit_diff exit={r.returncode}",
                "commit_diff_stderr": (r.stderr or "")[-500:]}
    try:
        with open(jpath) as f:
            return json.load(f)
    except (OSError, ValueError) as e:
        return {"l2_error": f"commit_diff json unreadable: {e}"}
    finally:
        try:
            os.unlink(jpath)
        except OSError:
            pass
        try:
            os.rmdir(tmpd)
        except OSError:
            pass

# ------------------------- W2.6 stats / L3-fanout helpers -------------------------

# (stats.txt field, short name) -- the MEASURED gem5 v25.1 stdlib-board key
# names, identical to tools/event_density.py's STATS_KEYS source (re-grepped
# live from a real C3/O3 outdir stats.txt 2026-09-24 before writing this).
# ipc is DERIVED (simInsts / numCycles -- REAL instructions-per-cycle, NOT
# simInsts/simSeconds which is instructions-per-SIMULATED-second, a value in
# the billions that no IPC consumer expects; orchestrator caught 2026-09-24);
# every absent key is listed in the "missing" list -- never fabricated.
RUNNER_STATS_KEYS = [
    ("board.processor.cores.core.commit.branchMispredicts", "branch_mispredicts"),
    ("board.processor.cores.core.commit.commitSquashedInsts", "commit_squashed_insts"),
    ("board.processor.cores.core.rename.renamedInsts", "rename_renamed_insts"),
    ("board.processor.cores.core.numCycles", "num_cycles"),
    ("simInsts", "sim_insts"),
    ("simSeconds", "sim_seconds"),
    ("simTicks", "sim_ticks"),
    ("hostSeconds", "host_seconds"),
]


def _parse_stat_number(tok):
    """int(tok) if possible, else float(tok), else None (not a stat value)."""
    try:
        return int(tok)
    except ValueError:
        pass
    try:
        return float(tok)
    except ValueError:
        return None


def extract_stats_summary(outdir):
    """W2.6 (plan Task 6): parse <outdir>/stats.txt into the runner stats
    summary block (ipc + the microarch event counters W3's occupancy-weighted
    ranking consumes). Returns a dict for the '[runner] STATS: {json}' line.

    Honesty contract: a key absent from stats.txt is NOT invented -- its
    short name goes into "missing" (other families' stats.txt, e.g. C0's
    system.cpu.* naming, will simply report most keys missing). Duplicate
    names with conflicting values (multi-section stats, e.g. checkpoint
    restore) keep the LAST (most recent section) value and are flagged in
    "ambiguous". A missing/unreadable stats.txt returns {"stats_error": ...}.
    """
    if not outdir:
        return {"stats_error": "gem5 outdir unknown (no -d in cmd)"}
    spath = os.path.join(outdir, "stats.txt")
    if not os.path.exists(spath):
        return {"stats_error": f"stats.txt not found: {spath}"}
    raw, ambiguous = {}, []
    try:
        with open(spath, "r", errors="replace") as f:
            for line in f:
                parts = line.split()
                if len(parts) < 2 or parts[0].startswith("#"):
                    continue
                val = _parse_stat_number(parts[1])
                if val is None:
                    continue  # e.g. "----- Begin Simulation Statistics -----"
                name = parts[0]
                if name in raw and raw[name] != val:
                    ambiguous.append(name)
                raw[name] = val
    except OSError as e:
        return {"stats_error": f"stats.txt unreadable: {e}"}
    stats, missing = {}, []
    for key, short in RUNNER_STATS_KEYS:
        if key in raw:
            stats[short] = raw[key]
        else:
            missing.append(short)
    # ipc = simInsts / numCycles (REAL inst-per-cycle). The first cut divided
    # by simSeconds (inst per SIMULATED second, ~3.3e9 -- a mislabeled MIPS);
    # orchestrator caught it in end-to-end review 2026-09-24 and switched to
    # the measured numCycles stat (board.processor.cores.core.numCycles).
    if ("sim_insts" in stats and "num_cycles" in stats
            and stats["num_cycles"] > 0):
        stats["ipc"] = round(stats["sim_insts"] / stats["num_cycles"], 6)
    else:
        missing.append("ipc")
    if missing:
        stats["missing"] = missing
    if ambiguous:
        stats["ambiguous"] = sorted(set(ambiguous))
    return stats


def run_fanout(trace_path, phys_id):
    """W2.6 (plan Task 6): measure the L3 fanout of phys_id on the run's
    commit trace via tools/fanout.py (liveness windows + val changes; the
    honest upper-bound proxy -- source reads are not in the trace). Returns
    fanout.py's JSON dict, or an honest {'l3_error': ...} on any failure
    (modeled on run_commit_diff; the caller merges it verbatim into the
    results.jsonl l3 block)."""
    if not os.path.exists(trace_path):
        return {"l3_error": f"trace missing: {trace_path}"}
    fo = os.path.join(REPO, "tools", "fanout.py")
    tmpd = tempfile.mkdtemp(prefix="l3fan-")
    jpath = os.path.join(tmpd, "l3.json")
    env = dict(os.environ)
    env.setdefault("PYTHONHASHSEED", "0")
    try:
        r = subprocess.run([sys.executable, fo, "--trace", trace_path,
                            "--phys", str(phys_id), "--json", jpath],
                           capture_output=True, text=True, timeout=600,
                           env=env)
    except subprocess.TimeoutExpired:
        return {"l3_error": "fanout exceeded 600s"}
    if r.returncode != 0 or not os.path.exists(jpath):
        return {"l3_error": f"fanout exit={r.returncode}",
                "fanout_stderr": (r.stderr or "")[-500:]}
    try:
        with open(jpath) as f:
            return json.load(f)
    except (OSError, ValueError) as e:
        return {"l3_error": f"fanout json unreadable: {e}"}
    finally:
        try:
            os.unlink(jpath)
        except OSError:
            pass
        try:
            os.rmdir(tmpd)
        except OSError:
            pass


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("manifest")
    ap.add_argument("--config", default="C0", choices=list(CONFIG_FAMILY),
                    help="platform config family (design doc §1.1): C0 = "
                         "arm_chaos.py baseline, C2 = kp920_proxy.py (V110 "
                         "proxy). The campaign driver passes this from the "
                         "campaign's `config` field; the manifest's "
                         "platform.config_family overrides if present.")
    ap.add_argument("--golden-checksum",
                    help="workload oracle checksum (e.g. reg_chain's 16-hex "
                         "value) from a no-injection run. If omitted, the "
                         "manifest's oracle.golden_id is resolved via the "
                         "runner's GOLDEN_IDS table.")
    # v1.1 Phase 8.1: explicit override for non-exact_hash oracles
    # (array_hash golden ARRAYHASH; per_element_diff/fp_ulp ignore it — the
    # kernel diffs against its own golden copy — but the flag exists so a
    # golden reference can always be pinned on the command line).
    ap.add_argument("--golden-array",
                    help="golden value for non-exact_hash oracles (e.g. the "
                         "64-hex ARRAYHASH from a no-injection run). "
                         "Overrides the GOLDEN_ARRAYS registry lookup of "
                         "oracle.golden_id for array_hash manifests.")
    ap.add_argument("--binary", required=True, help="path to the workload binary")
    # §3.2 FS checkpoint pipeline (Phase 5.4): FS deps + checkpoint restore.
    # The checkpoint is made ONCE by boot_ckpt.rcS (kp920_proxy_fs --cpu
    # Atomic --readfile ...); every rep then restores from it (fast path).
    ap.add_argument("--kernel", default="gem5-fs/vmlinux",
                    help="FS kernel path (C0-FS/C2-FS families)")
    ap.add_argument("--disk", default="gem5-fs/ubuntu.img",
                    help="FS disk image path")
    ap.add_argument("--bootloader", default="gem5-fs/boot.arm64",
                    help="FS bootloader path")
    ap.add_argument("--root-partition", default="/dev/vda1",
                    help="root partition in the disk (virtio_blk -> vda)")
    ap.add_argument("--fs-cpu", default="Atomic", choices=["Atomic", "O3", "TIMING"],
                    help="CPU type for the FS run (the checkpoint pipeline "
                         "boots Atomic; restore may switch)")
    ap.add_argument("--restore-checkpoint", default=None,
                    help="checkpoint dir to restore from (Phase 5.2 pipeline)")
    # ---- W2.3 trace two-pass (plan Task 3): L2 commit-trace replay pass ----
    ap.add_argument("--ctrace", default=None, metavar="PATH",
                    help="W2.3: enable the L2 commit trace — passes "
                         "--chaos_ctrace --ctrace_file PATH to the config "
                         "(C3/ooo_proxy.py only; the path is made absolute so "
                         "the trace lands exactly here).")
    ap.add_argument("--ctrace-ref", default=None, metavar="REF.csv.gz",
                    help="W2.3: after the run, diff the produced trace "
                         "against this no-injection reference via "
                         "tools/commit_diff.py and print the five-class "
                         "result as an '[runner] L2RESULT: {json}' line "
                         "(requires --ctrace).")
    ap.add_argument("--no-inject", action="store_true",
                    help="W2.3: no-injection REFERENCE run — run the same "
                         "manifest/workload/seed with every injector flag "
                         "omitted (the per-cell fault-free trace baseline; "
                         "the manifest's fault block is validated but NOT "
                         "mapped to any --chaos_* flag).")
    # ---- W2.6 (plan Task 6): stats.txt summary + L3 fanout ----
    ap.add_argument("--stats", action="store_true",
                    help="W2.6: after the run, parse <outdir>/stats.txt and "
                         "print a '[runner] STATS: {json}' summary line "
                         "(ipc = simInsts/numCycles, branch_mispredicts, "
                         "commit_squashed_insts, rename_renamed_insts, "
                         "sim_insts/sim_seconds/sim_ticks, host_seconds). "
                         "Keys absent from stats.txt are listed in "
                         "stats.missing — never fabricated.")
    ap.add_argument("--fanout-phys", type=int, default=None, metavar="ID",
                    help="W2.6: after the run, measure the L3 fanout of this "
                         "physical register id on the produced --ctrace via "
                         "tools/fanout.py (liveness windows until the next "
                         "overwrite of the same phys id + val change count; "
                         "source reads are not traced, so the window is an "
                         "upper-bound proxy) and print it as an "
                         "'[runner] L3RESULT: {json}' line (requires "
                         "--ctrace).")
    args = ap.parse_args()

    with open(args.manifest) as f:
        m = yaml.safe_load(f)

    # resolve config family: manifest platform.config_family overrides the
    # --config CLI default (so a C2 manifest runs on kp920_proxy.py without
    # the caller needing --config C2). Falls back to the --config arg.
    cfg_family = m.get("platform", {}).get("config_family") or args.config
    if cfg_family not in CONFIG_FAMILY:
        sys.exit(f"[runner] unknown config_family '{cfg_family}'. Known: "
                 f"{list(CONFIG_FAMILY)}. Aborting.")
    cfg_path = CONFIG_FAMILY[cfg_family]
    print(f"[runner] config_family: {cfg_family} -> {os.path.basename(cfg_path)}")

    # W2.3 trace two-pass: validate the trace flag surface EARLY (before any
    # gem5 run) so a mis-scoped campaign fails loudly at the runner, not
    # silently inside gem5's argparse.
    if args.ctrace and cfg_family not in ("C3", "C4-LSU"):
        sys.exit(f"[runner] --ctrace requires C3/C4-LSU (only "
                 f"configs/se/ooo_proxy.py and configs/se/lsu_proxy.py define "
                 f"--chaos_ctrace/--ctrace_file; config_family={cfg_family}). "
                 f"Aborting.")
    if args.ctrace_ref and not args.ctrace:
        sys.exit("[runner] --ctrace-ref requires --ctrace (the five-class "
                 "diff compares the trace THIS run produces). Aborting.")
    # W2.6: --fanout-phys measures the trace THIS run produces, so it is
    # meaningless without --ctrace; a negative id is a typo, not an id.
    if args.fanout_phys is not None and not args.ctrace:
        sys.exit("[runner] --fanout-phys requires --ctrace (the L3 fanout "
                 "measures the commit trace THIS run produces). Aborting.")
    if args.fanout_phys is not None and args.fanout_phys < 0:
        sys.exit("[runner] --fanout-phys must be a non-negative integer. "
                 "Aborting.")

    # platform.config_params (optional dict): microarch knob overrides passed
    # through to the config script (Phase 3 H2 window sweep — ROB/PhysInt
    # sizing). Whitelist-checked: only keys the target config's argparse
    # actually defines, so a typo fails loudly at the runner, not silently
    # inside gem5 (the lsqfwd argparse lesson, 79f32b1).
    cfg_params = m.get("platform", {}).get("config_params") or {}
    if cfg_params:
        if cfg_family == "C4-LSU":
            supported = {"variant"}  # lsu_proxy.py S-variant knob
        else:
            supported = {"rob", "phys_int", "phys_float", "lq", "sq"}  # kp920_proxy.py knobs
        unsupported = set(cfg_params) - supported
        if unsupported:
            sys.exit(f"[runner] platform.config_params keys {sorted(unsupported)} "
                     f"not in supported set {sorted(supported)} for family "
                     f"{cfg_family}. Aborting.")
        if cfg_family not in ("C2", "C4-LSU"):
            sys.exit(f"[runner] platform.config_params is C2/C4-LSU-only "
                     f"(microarch knobs); config_family={cfg_family}. Aborting.")

    # resolve oracle kind + tolerance (v1.1 Phase 8.1): the manifest's
    # oracle.kind selects the comparison; workload.oracle_kind is the
    # campaign-side spelling (campaign.py writes it under workload because
    # the campaign schema's oracle block is the runner's manifest oracle).
    # Default exact_hash = the legacy behavior, byte for byte.
    oracle_kind = (m.get("oracle", {}).get("kind")
                   or m.get("workload", {}).get("oracle_kind")
                   or "exact_hash")
    if oracle_kind not in ("exact_hash", "array_hash", "per_element_diff",
                           "fp_ulp"):
        sys.exit(f"[runner] oracle.kind='{oracle_kind}' not supported. "
                 f"Known: exact_hash, array_hash, per_element_diff, fp_ulp. "
                 f"Aborting.")
    oracle_tol = (m.get("oracle", {}).get("tol")
                  or m.get("workload", {}).get("oracle_tol") or 0)
    try:
        oracle_tol = int(oracle_tol)
    except (TypeError, ValueError):
        sys.exit(f"[runner] oracle.tol='{oracle_tol}' is not an integer. "
                 f"Aborting.")
    if oracle_kind != "exact_hash":
        print(f"[runner] oracle: kind={oracle_kind} tol={oracle_tol}")

    # resolve golden checksum: explicit arg, else manifest golden_id.
    # Non-exact_hash oracles resolve through GOLDEN_ARRAYS (or the
    # --golden-array override); per_element_diff/fp_ulp kernels compute the
    # reference themselves so the golden value is unused (empty string).
    golden = args.golden_checksum
    if not golden:
        gid = m.get("oracle", {}).get("golden_id")
        if oracle_kind == "array_hash":
            golden = args.golden_array
            if not golden:
                if gid and gid in GOLDEN_ARRAYS:
                    golden = GOLDEN_ARRAYS[gid]
                    print(f"[runner] resolved golden_id '{gid}' (array) -> "
                          f"{golden}")
                else:
                    sys.exit(f"[runner] oracle.kind=array_hash but no "
                             f"--golden-array and oracle.golden_id '{gid}' "
                             f"not in GOLDEN_ARRAYS. Aborting.")
        elif oracle_kind in ("per_element_diff", "fp_ulp"):
            # kernel-side reference: the ELEMDIFF/ULP line is self-verdict
            golden = ""
        else:
            if gid and gid in GOLDEN_IDS:
                golden = GOLDEN_IDS[gid]
                print(f"[runner] resolved golden_id '{gid}' -> {golden}")
            else:
                sys.exit(f"[runner] no --golden-checksum and oracle.golden_id "
                         f"'{gid}' unknown. Aborting.")
    args.golden_checksum = golden

    # schema validation. jsonschema (full draft-07) if available; else the
    # dependency-free light validator (tools/manifest_validate.py) — the v2
    # §1.6 extension is ENFORCED even on hosts without jsonschema (this host
    # has pip offline; the light validator is the runtime enforcer, not a
    # silent skip). Prefer jsonschema when present for full draft-07 coverage.
    if HAVE_SCHEMA:
        sp = os.path.join(REPO, "schemas/manifest.schema.json")
        with open(sp) as sf:
            schema = json.load(sf)
        try:
            jsonschema.validate(m, schema)
        except jsonschema.ValidationError as e:
            sys.exit(f"manifest schema validation FAILED: {e.message}")
        print("[runner] manifest schema: OK (jsonschema)")
    else:
        from manifest_validate import validate as light_validate
        ok, errs = light_validate(m)
        if not ok:
            sys.exit(f"manifest schema validation FAILED (light validator): "
                     f"{'; '.join(errs)}")
        print("[runner] manifest schema: OK (light validator)")

    # validate binary hash
    if m["workload"].get("binary_sha256"):
        actual = sha256_file(args.binary)
        expected = m["workload"]["binary_sha256"]
        if actual != expected:
            sys.exit(f"[runner] binary sha256 MISMATCH: {actual} != {expected}")
        print(f"[runner] binary sha256: OK ({actual[:12]}...)")

    # G5 single-fault contract. v1.1 Phase 8.4 (task_plan 0d): the
    # recurring_result_stuck model is EXEMPT — it is a PERMANENT fault
    # (every opClass-eligible FSU result gets the same fixed mask, modeling
    # a stuck multiplier partial-product bit) and runs with max_faults=0
    # (unlimited). Everything else still requires max_faults in {0,1}.
    _recurring = (m["fault"]["model"] == "recurring_result_stuck")
    if _recurring:
        if m["limits"]["max_faults"] != 0:
            sys.exit("[runner] fault.model=recurring_result_stuck requires "
                     "limits.max_faults==0 (the fault recurs on every "
                     "eligible event). Aborting.")
        print("[runner] recurring_result_stuck: single-fault contract "
              "relaxed (max_faults=0, recurring permanent fault)")
    else:
        assert m["limits"]["max_faults"] in (0,1), "formal runs require max_faults in {0,1}"

    # map manifest -> arm_chaos.py args (report issue #5: the manifest's
    # target.index / fault.bit_indices / trigger MUST take effect, not be
    # ignored for generic --bits_to_change=1).
    t = m["trigger"]
    inj = m["fault"]
    tgt = m["target"]
    comp = tgt["component"]
    layer = tgt.get("layer", "architectural")
    idx = tgt.get("index")              # may be None for random sampling
    width = tgt.get("width_bits", 64)
    bits = inj.get("bit_indices") or []  # explicit bit positions, e.g. [20]
    field = tgt.get("field", "value")

    # trigger mode: only 'cycle'/'tick' are honored by the current config
    # (first_clock). pc/committedInst/event need G6 work (deferred) — reject
    # with a clear error so a manifest isn't silently mis-triggered.
    tmode = t.get("mode", "cycle")
    if tmode not in ("cycle", "tick"):
        sys.exit(f"[runner] trigger.mode='{tmode}' not supported yet "
                 f"(needs G6 pc/committedInst/event hooks). Use 'cycle' "
                 f"with value = first_clock. Aborting — not silently "
                 f"mis-triggering.")

    # v1.1 Phase 8.2 uniform event sampling: the manifest's optional
    # `sampling` block carries the driver-computed fixed skip (from
    # chaosPickSkip(seed, N_eligible) — cpu/o3/chaos_event_sample.hh) and
    # the countOnly dry-run flag. Absent block = legacy geometric(0.1)
    # in-injector draw (every existing campaign unchanged).
    sampling = m.get("sampling", {}) or {}
    s_skip = sampling.get("events_to_skip")
    s_count = sampling.get("count_only", False)
    if s_skip is not None and (not isinstance(s_skip, int)
                               or isinstance(s_skip, bool) or s_skip < 0):
        sys.exit(f"[runner] sampling.events_to_skip='{s_skip}' must be a "
                 f"non-negative integer. Aborting.")

    # fault model -> --fault_type
    model_map = {"transient_bit_flip": "bit_flip",
                 "stuck_at_zero": "stuck_at_zero",
                 "stuck_at_one": "stuck_at_one",
                 "local_mbu": "bit_flip",       # MBU = multi-bit flip (bits_to_change>1)
                 "intermittent_burst": "bit_flip",
                 "legal_domain_sub": "bit_flip",
                 "delay_omission": "bit_flip",
                 # v1.1 Phase 8.4: recurring permanent fault — same fixed
                 # mask on EVERY eligible event (max_faults=0 = unlimited;
                 # the dedicated CHAOSFPU recurring MODE lands in Phase 9
                 # patch 1a; until then the unlimited-fault bit_flip path
                 # carries the contract, with the recurring pairing check
                 # above enforcing max_faults==0).
                 "recurring_result_stuck": "bit_flip"}
    if inj["model"] not in model_map:
        sys.exit(f"[runner] fault.model='{inj['model']}' not mapped yet. Aborting.")
    fault_type = model_map[inj["model"]]

    # fault mask: if bit_indices given, build the OR mask (now 64-bit).
    # bits_to_change defaults to the number of explicit bits, or 1 if random.
    if bits:
        mask = 0
        for b in bits:
            if b < 0 or b >= width:
                sys.exit(f"[runner] bit {b} outside width {width}. Aborting.")
            mask |= (1 << b)
        fault_mask = str(mask)
        bits_to_change = str(len(bits))
    else:
        fault_mask = "0"   # random mask
        bits_to_change = "1"

    # FS families (C0-FS / C2-FS) have a completely different arg surface
    # (kernel/disk/bootloader, no --cmd/--first_clock; injector knobs carry
    # the window). Checkpoint pipeline (Phase 5.2/5.4): every rep restores
    # from the one-time boot_ckpt checkpoint (fast path ~4min vs ~30min boot).
    if cfg_family in ("C0-FS", "C2-FS"):
        cmd = [G5, "--quiet", "-d", tempfile.mkdtemp(prefix="man-"), cfg_path,
               "--kernel", args.kernel, "--disk", args.disk,
               "--bootloader", args.bootloader,
               "--root-partition", args.root_partition,
               "--cpu", args.fs_cpu]
        if args.restore_checkpoint:
            cmd += ["--restore-checkpoint", args.restore_checkpoint,
                    "--ckpt-first-clock"]
    else:
        cmd = [G5, "--quiet", "-d", tempfile.mkdtemp(prefix="man-"), cfg_path,
               "--cmd", args.binary, "--cpu", "O3",
               "--first_clock", str(t["value"]),
               "--max_faults", str(m["limits"]["max_faults"]),
               "--rng_seed", str(m["rng"]["selection_seed"]),
               "--fault_type", fault_type]
    # §2.7: arm_chaos_cache.py has NO --fault_mask/--bits_to_change args
    # (different param surface than arm_chaos.py), and neither do the FS
    # configs (arm_chaos_fs.py — SE-only knobs). Pass them only on the SE
    # arm_chaos.py-family configs.
    if not args.no_inject and cfg_family not in ("C0-CACHE", "C0-FS", "C2-FS"):
        cmd += ["--fault_mask", fault_mask, "--bits_to_change", bits_to_change]
    # W2.3 --no-inject: no-injection REFERENCE run — the manifest's fault
    # block was validated above but is intentionally NOT mapped to any
    # --chaos_* flag (same workload, same seed, zero injectors). This is the
    # per-cell fault-free baseline the trace two-pass diffs against; anything
    # below this branch is the injection mapping and is skipped whole.
    if args.no_inject:
        print("[runner] NO-INJECT reference run: injector flags omitted")
    # target component + layer -> the right injector + index knob
    elif comp == "gpr":
        cmd += ["--chaos_reg"]
        if idx is not None:
            # Report #5: manifest target.index MUST take effect. CHAOSReg now
            # has a targetRegIdx directed knob (patch: G1 directed-reg) — force
            # the fault onto the manifest's reg index, not RNG luck.
            cmd += [f"--target_reg_idx={idx}"]
        # max_reg_idx still bounds random sampling when idx is None (random cell)
    elif comp == "physreg":
        cmd += ["--chaos_phys"]
        # v1.3 Phase 20 §8: vector-lane axis — fault.vec_lane selects the
        # lane within a vector physreg (with reg_class=vector).
        if inj.get("vec_lane") is not None:
            cmd += ["--phys_reg_class", "vector",
                    "--vec_lane_offset", str(inj["vec_lane"])]
        if layer == "physical":
            cmd += ["--phys_mode", "phys"]
            if idx is not None:
                cmd += [f"--phys_target_idx={idx}"]
        else:  # architectural
            cmd += ["--phys_mode", "arch_frontend"]
            if idx is not None:
                cmd += [f"--phys_target_arch={idx}"]
    elif comp == "memory":
        # §1.2 protection-aware: CHAOSMem's protectionModel (DRAM = 'secded'
        # per Huawei DDR ECC proxy). arm_chaos.py/kp920_proxy.py accept
        # --protection_model; default "none" = raw escape (regression-safe).
        cmd += ["--chaos_mem", "--protection_model",
                inj.get("protection_model", "none")]
        # v1.1 Phase 11 (task_plan 3b): fault.addr_window {start, end} ->
        # the directed physical DRAM window (streaming workloads put their
        # arrays far from the image; the default whole-memory draw hits
        # never-touched frames — the first-round DRAM 'all Masked' artifact).
        aw = inj.get("addr_window") or {}
        if aw.get("start") is not None:
            cmd += ["--addr_start", str(aw["start"])]
        if aw.get("end") is not None:
            cmd += ["--addr_end", str(aw["end"])]
        # v1.2 Phase 14 (plan item 6): §2.17 ecc_logic_fault — the SECDED
        # logic itself mis-corrects (1-bit err -> wrong-bit fix). Pairs with
        # protection_model=secded.
        if inj.get("ecc_logic_fault"):
            cmd += ["--ecc_logic_fault"]
        # §2.17 addr_map_sub (F5, Phase 4.6): manifest fault.model
        # stuck_at_one -> displaced-write mode (the displaced 8B write is
        # effectively a 'stuck' wrong-location copy).
        if inj["model"] == "stuck_at_one":
            cmd += ["--addr_map_sub"]
    elif comp == "rat":
        # §2.2 CHAOSRenameMap (S1 patch 1). Manifest fault.model maps to the
        # --rename_mode (map_bitflip / f5_substitute / f4_field_stuck). The
        # v2 schema's fault.model enum has legal_domain_sub for F5; map it.
        cmd += ["--chaos_rename"]
        # W7.2 (ooo 04-design-matrix D62-D71 merged rows): register-class
        # axis. The v2 target.sub_field carries the class via a "_vec"
        # suffix (free-form string per schema — e.g. "map_bitflip_vec",
        # "swap_to_active_vec", "hb_bitflip2_vec"): the suffix is stripped
        # for the mode discriminator below and routes
        # --rename_target_class vec. Plain sub_field (no suffix) keeps
        # targetClass=int — every pre-W7 manifest is unaffected. Platform
        # fact (W1.2): AArch64 scalar FP renames via VecRegClass, so the
        # scalar-FP rows D62-66 are merged into the vec class (there is no
        # "float" route); scalar-FP vs SIMD producer attribution is post-hoc
        # via the commit trace (documented in CHAOSRenameMap.hh).
        rcls = "int"
        rsf = str(tgt.get("sub_field", ""))
        if rsf.endswith("_vec"):
            rcls = "vec"
            rsf = rsf[:-len("_vec")]
        # fault model -> rename_mode
        # intermittent_burst -> spec_leak (§2.3 Phase 4.1, method1 speculative
        # leak): one squash-rollback suppression — the wrong-path µop's dest
        # stays mapped, its value leaks into the correct path.
        # local_mbu -> map_bitflip2 (W4.1 D12, ooo 04-design-matrix R13):
        # MBU = multi-bit upset — the RAT map-field 2-bit flip. The 1-bit
        # model stays reachable via transient_bit_flip.
        rm = {"transient_bit_flip": "map_bitflip",
              "local_mbu": "map_bitflip2",
              "intermittent_burst": "spec_leak",
              "legal_domain_sub": "f5_substitute",
              "stuck_at_zero": "f4_field_stuck",
              "stuck_at_one": "f4_field_stuck"}.get(inj["model"], "map_bitflip")
        # W4.2a D13 swap_to_active (ooo 04-design-matrix R14, 换值·固定间隔):
        # the structured "swap the mapping to a random ROB in-flight dest
        # physReg" model. Selected by the v2 target.sub_field discriminator
        # on legal_domain_sub ("substitute with a legal IN-USE value");
        # plain legal_domain_sub keeps the §2.2 f5_substitute random-
        # allocated semantics (nothing orphaned, additive v2 key).
        if (inj["model"] == "legal_domain_sub"
                and rsf == "swap_to_active"):
            rm = "swap_to_active"
        # W4.3 D15 f5_rat_stuck (ooo 04-design-matrix R16, RAT映射字段·卡死,
        # F5 permanent): ONE RAT entry + ONE physReg-index bit stuck-at-0/1,
        # write-path mask on every write to that entry. Selected by the v2
        # target.sub_field discriminator on stuck_at_zero/one (the §2.2
        # whole-value pin f4_field_stuck keeps the plain models).
        if (inj["model"] in ("stuck_at_zero", "stuck_at_one")
                and rsf == "f5_rat_stuck"):
            rm = "f5_rat_stuck"
        # W4.4 D16 stale_read (ooo 04-design-matrix R17, RAT映射字段·读到
        # 旧数据): the next rename overwrite of the entry silently fails
        # once — the entry keeps the old (legal) mapping, downstream readers
        # read stale data. Selected by the v2 target.sub_field discriminator
        # on delay_omission ("the update that should have happened never
        # landed"); rat + plain delay_omission is not otherwise mapped.
        if (inj["model"] == "delay_omission"
                and rsf == "stale_read"):
            rm = "stale_read"
        # W4 final D14 swap_mispred_event (ooo 04-design-matrix R15,
        # RAT映射字段·换值·误预测事件触发): the D13 swap_to_active model,
        # but eligible ONLY inside a branch-misprediction squash-restore
        # window (the event-triggered variant — the fixed-interval vs
        # event-trigger comparison is the methodology check). Selected by
        # the v2 target.sub_field discriminator on legal_domain_sub (plain
        # legal_domain_sub keeps D13 swap_to_active; the §2.2
        # f5_substitute random-allocated semantics stay on the plain model
        # via the map above only when sub_field is absent).
        if (inj["model"] == "legal_domain_sub"
                and rsf == "swap_mispred_event"):
            rm = "swap_mispred_event"
        # W4 final D23/D24 hb_bitflip(_2) (ooo 04-design-matrix R24/R25,
        # 重命名检查点·单/双比特翻转): gem5 has no separate RAT-checkpoint
        # array — the recovery checkpoint IS the historyBuffer entry
        # (RenameHistory, rename.hh:301, mechanism-verified N1). The
        # injector flips 1 bit (transient_bit_flip + sub_field) / 2
        # distinct random bits (local_mbu + sub_field) of one field's
        # physReg index at the checkpoint's creation; the fault stays
        # dormant until doSquash/removeFromHistory consumes the WRONG phys.
        if (inj["model"] == "transient_bit_flip"
                and rsf == "hb_bitflip"):
            rm = "hb_bitflip"
        if (inj["model"] == "local_mbu"
                and rsf == "hb_bitflip2"):
            rm = "hb_bitflip2"
        cmd += ["--rename_mode", rm, "--rename_first_clock", str(t["value"]),
                "--rename_max_faults", str(m["limits"]["max_faults"]),
                "--rename_rng_seed", str(m["rng"]["selection_seed"]),
                "--rename_fault_mask", fault_mask, "--rename_target_arch",
                str(idx) if idx is not None else "-1",
                "--rename_target_class", rcls]
    elif comp == "freelist":
        # §2.2 CHAOSFreeList (S1 patch 2). mark_free / pop_wrong via fault.model.
        cmd += ["--chaos_freelist"]
        # W7.3 (ooo 04-design-matrix D72-D77 merged rows): register-class
        # axis, same "_vec" sub_field suffix convention as the rat block
        # (e.g. "mark_free_vec", "mark_free_event_vec", "drop_release_vec")
        # — suffix stripped for the mode discriminator, remainder routes
        # --freelist_target_class vec. Plain sub_field keeps targetClass=
        # int. Scalar-FP rows D72/73/76 are merged into D74/75/77 (W1.2:
        # AArch64 scalar FP renames via VecRegClass). D75's vec threshold
        # re-derivation (≤6 -> 0, the initial-free-4 calibration) lives in
        # CHAOSFreeList.hh/.py + ooo_proxy's default.
        fcls = "int"
        fsf = str(tgt.get("sub_field", ""))
        if fsf.endswith("_vec"):
            fcls = "vec"
            fsf = fsf[:-len("_vec")]
        fm = {"transient_bit_flip": "mark_free",
              "local_mbu": "mark_free",
              "legal_domain_sub": "pop_wrong"}.get(inj["model"], "mark_free")
        # W4.5 D18 mark_free_event (ooo 04-design-matrix R19, 空闲表·重复分配
        # ·事件触发): same duplicate allocation as D17 mark_free, but fires
        # only while the int freelist remaining count <= threshold (default
        # 8). Selected by the v2 target.sub_field discriminator on the
        # transient models (plain models keep the D17 fixed-interval
        # mark_free semantics).
        if (inj["model"] in ("transient_bit_flip", "local_mbu")
                and fsf == "mark_free_event"):
            fm = "mark_free_event"
        # W4 final D19 drop_release (ooo 04-design-matrix R20, 空闲表·丢失
        # 释放, F1): a release that should have happened does not — the
        # freed physReg is not pushed back (UnifiedFreeList::addReg hook);
        # the int pool permanently shrinks by one. Selected by the v2
        # target.sub_field discriminator on delay_omission (the timing
        # "lost event" class — plain delay_omission keeps mark_free).
        if (inj["model"] == "delay_omission"
                and fsf == "drop_release"):
            fm = "drop_release"
        # W4 final D20/D21 head_bitflip(_2) (ooo 04-design-matrix R21/R22,
        # 空闲表头/尾指针·单/双比特翻转) — HONEST APPROXIMATION (spike B:
        # gem5 SimpleFreeList is a std::queue with no explicit head/tail
        # pointer): the popped-front idx has 1 (D20) / 2 distinct random
        # (D21, F0) bits flipped — the id handed out is what a corrupted
        # head read would have returned. Plain transient/local_mbu keep the
        # D17 mark_free fixed-interval semantics.
        if (inj["model"] == "transient_bit_flip"
                and fsf == "head_bitflip"):
            fm = "head_bitflip"
        if (inj["model"] == "local_mbu"
                and fsf == "head_bitflip2"):
            fm = "head_bitflip2"
        # W4 final D22 head_stuck (ooo 04-design-matrix R23, 空闲表头/尾
        # 指针·卡死, F5) — HONEST APPROXIMATION (same std::queue finding):
        # "反复返回同项不真正 pop（头卡死）" — every getReg returns the SAME
        # stuck id and the queue never advances. Selected by the v2
        # target.sub_field discriminator on stuck_at_zero/one (plain stuck
        # models are not otherwise mapped for freelist).
        if (inj["model"] in ("stuck_at_zero", "stuck_at_one")
                and fsf == "head_stuck"):
            fm = "head_stuck"
        cmd += ["--freelist_mode", fm, "--freelist_first_clock", str(t["value"]),
                "--freelist_max_faults", str(m["limits"]["max_faults"]),
                "--freelist_rng_seed", str(m["rng"]["selection_seed"]),
                "--freelist_target_class", fcls]
    elif comp == "rob":
        # §2.3 CHAOSROB (S1 patch 1). entry_bitflip/exc_suppress via fault.model.
        cmd += ["--chaos_rob"]
        rm = {"transient_bit_flip": "entry_bitflip",
              "local_mbu": "entry_bitflip",
              "legal_domain_sub": "exc_suppress"}.get(inj["model"], "entry_bitflip")
        # W7.4 (ooo 04-design-matrix FP/SIMD Dispatch/ROB, the D87-
        # prerequisite dest-id twins at the rob_insert site): register-class
        # axis, the rat-block "_vec" suffix convention — sub_field
        # "destid_bitflip_vec" etc. strips the suffix for the
        # discriminators below and routes --rob_target_class vec
        # (VecRegClass dest domain [0, numVecPhysRegs); the swap_active
        # pool collects vec dests). Only meaningful for the destid_*
        # sub_fields; PC / done / pointer families stay class-agnostic
        # (unified ROB — TC'23). Plain sub_field keeps targetClass=int —
        # every pre-W7 manifest is unaffected.
        rbcls = "int"
        rsf = str(tgt.get("sub_field", ""))
        if rsf.endswith("_vec"):
            rbcls = "vec"
            rsf = rsf[:-len("_vec")]
        # W5.1-W5.3 (ooo 04-design-matrix D25-D31, Int Dispatch/ROB): the
        # ROB-entry WRITE-path modes (ROB::insertInst site — the TC'23
        # site). Selected by the v2 target.sub_field discriminator; plain
        # models keep the legacy retireHead-site mapping above.
        #   pc_bitflip/pc_bitflip2 (D25/D26): 1/2 random bits of the
        #     entry's PC field (transient_bit_flip / local_mbu).
        #   pc_stuck (D27, F5): one entry's PC bit stuck-at 0/1
        #     (stuck_at_zero/one + write-path mask + retire readback).
        #   destid_bitflip/destid_bitflip2 (D28/D29): 1/2 random bits of
        #     the entry's int dest physReg identifier.
        #   destid_swap_active (D30): swap it with another ROB-resident
        #     in-flight dest physReg (legal_domain_sub, bypasses the
        #     dependency check by design).
        #   destid_stuck (D31, F5): one entry's dest-id bit stuck-at 0/1.
        if (inj["model"] == "transient_bit_flip"
                and str(tgt.get("sub_field", "")) == "pc_bitflip"):
            rm = "pc_bitflip"
        if (inj["model"] == "local_mbu"
                and str(tgt.get("sub_field", "")) == "pc_bitflip2"):
            rm = "pc_bitflip2"
        if (inj["model"] in ("stuck_at_zero", "stuck_at_one")
                and str(tgt.get("sub_field", "")) == "pc_stuck"):
            rm = "pc_stuck"
        if (inj["model"] == "transient_bit_flip" and rsf == "destid_bitflip"):
            rm = "destid_bitflip"
        if (inj["model"] == "local_mbu" and rsf == "destid_bitflip2"):
            rm = "destid_bitflip2"
        if (inj["model"] == "legal_domain_sub"
                and rsf == "destid_swap_active"):
            rm = "destid_swap_active"
        if (inj["model"] in ("stuck_at_zero", "stuck_at_one")
                and rsf == "destid_stuck"):
            rm = "destid_stuck"
        # W5.4 done-bit family (ooo 04-design-matrix D32-D35, Int
        # Dispatch/ROB — the done/completed CanCommit bit at the
        # Commit::markCompletedInsts gate): done_early(_event) forces the
        # bit (plus the required setExecuted assert bypass) on a
        # not-yet-completed entry; done_delay(_event) skips one
        # setCanCommit permanently. delay_omission = the timing/state-
        # update-wrong bucket (the D16 stale_read precedent); the
        # sub_field discriminator selects the exact model.
        if (inj["model"] == "delay_omission"
                and str(tgt.get("sub_field", "")) == "done_early"):
            rm = "done_early"
        if (inj["model"] == "delay_omission"
                and str(tgt.get("sub_field", "")) == "done_early_event"):
            rm = "done_early_event"
        if (inj["model"] == "delay_omission"
                and str(tgt.get("sub_field", "")) == "done_delay"):
            rm = "done_delay"
        if (inj["model"] == "delay_omission"
                and str(tgt.get("sub_field", "")) == "done_delay_event"):
            rm = "done_delay_event"
        # W5.6 D40 rob_stale_read (R41, ROB项整体·读到旧数据): the insert-
        # site whole-record stale overwrite (previous occupant's record
        # retained; commit reads it — STALE_RECORD_COMMITTED evidence).
        if (inj["model"] == "delay_omission"
                and str(tgt.get("sub_field", "")) == "rob_stale_read"):
            rm = "rob_stale_read"
        # W5.6 D36-D39 old-phys family (R37-R40, ROB的旧物理寄存器字段):
        # gem5's old-phys lives in the rename historyBuffer checkpoint
        # (W4 N1), so the modes are implemented in CHAOSRenameMap and
        # routed through --rob_mode (ooo_proxy instantiates the rename
        # injector for oldphys_*). 1-bit / 2-bit flip of prevPhysReg
        # (transient_bit_flip / local_mbu), swap to another ROB-active
        # dest physReg (legal_domain_sub, the D13/D30 pattern), F5 stuck
        # bit on the field cell (stuck_at_zero/one).
        if (inj["model"] == "transient_bit_flip"
                and str(tgt.get("sub_field", "")) == "oldphys_bitflip"):
            rm = "oldphys_bitflip"
        if (inj["model"] == "local_mbu"
                and str(tgt.get("sub_field", "")) == "oldphys_bitflip2"):
            rm = "oldphys_bitflip2"
        if (inj["model"] == "legal_domain_sub"
                and str(tgt.get("sub_field", "")) == "oldphys_swap_active"):
            rm = "oldphys_swap_active"
        if (inj["model"] in ("stuck_at_zero", "stuck_at_one")
                and str(tgt.get("sub_field", "")) == "oldphys_stuck"):
            rm = "oldphys_stuck"
        # W5.8-W5.9 (D41-D46, ooo 04-design-matrix R42-R47): ROB head/tail
        # pointer family — HONEST APPROXIMATIONS at the rob_insert site
        # (gem5 ROB = std::list, no pointer registers): head_ptr_* =
        # commit-side entry-selection misalignment (the offset entry's
        # record lands on the head entry — the skip/repeat-commit
        # observable), tail_ptr_* = allocation-side alias (the new entry's
        # record clobbers the in-use entry at the flip offset behind the
        # tail — the "覆盖仍在用的项" duplicate-allocation analog).
        if (inj["model"] == "transient_bit_flip"
                and str(tgt.get("sub_field", "")) == "head_ptr_bitflip"):
            rm = "head_ptr_bitflip"
        if (inj["model"] == "local_mbu"
                and str(tgt.get("sub_field", "")) == "head_ptr_bitflip2"):
            rm = "head_ptr_bitflip2"
        if (inj["model"] in ("stuck_at_zero", "stuck_at_one")
                and str(tgt.get("sub_field", "")) == "head_ptr_stuck"):
            rm = "head_ptr_stuck"
        if (inj["model"] == "transient_bit_flip"
                and str(tgt.get("sub_field", "")) == "tail_ptr_bitflip"):
            rm = "tail_ptr_bitflip"
        if (inj["model"] == "local_mbu"
                and str(tgt.get("sub_field", "")) == "tail_ptr_bitflip2"):
            rm = "tail_ptr_bitflip2"
        if (inj["model"] in ("stuck_at_zero", "stuck_at_one")
                and str(tgt.get("sub_field", "")) == "tail_ptr_stuck"):
            rm = "tail_ptr_stuck"
        cmd += ["--rob_mode", rm, "--rob_first_clock", str(t["value"]),
                "--rob_max_faults", str(m["limits"]["max_faults"]),
                "--rob_rng_seed", str(m["rng"]["selection_seed"]),
                # W7.4: destid-family register class (_vec suffix above).
                "--rob_target_class", rbcls]
    elif comp == "iq":
        # §2.5 CHAOSIQ. wake_omit (F6, default) / src_ready_bitflip (F5,
        # wrong-source wakeup — legal_domain_sub) / wake_phase (F6 phase
        # delay — intermittent_burst; bit_indices[0] = offset in cycles).
        cmd += ["--chaos_iq"]
        im = {"legal_domain_sub": "src_ready_bitflip",
              "intermittent_burst": "wake_phase"}.get(inj["model"], "wake_omit")
        # W5.10-W5.12 (ooo 04-design-matrix D47-D55, Int Dispatch/ROB):
        # the Int-IQ ready-bit (D47-D49), source-tag (D50-D54) and
        # dispatch-port FU-misroute (D55) modes — selected by the v2
        # target.sub_field discriminator (the rob-block pattern); plain
        # models keep the legacy mappings above.
        sf = str(tgt.get("sub_field", ""))
        # W7.4 (ooo 04-design-matrix D86-D91, FP/SIMD Dispatch/ROB):
        # register-class axis + the D86 opClass scoping, the rat-block
        # suffix convention. "_vec" (e.g. "tag_swap_vec", "tag_bitflip_vec",
        # "tag_bitflip2_vec", "tag_stuck_vec", "tag_stale_read_vec",
        # "ready_early_vec") strips the suffix for the discriminators below
        # and routes --iq_target_class vec — the FP/SIMD twins on the
        # VecRegClass rename domain (scalar FP + FP SIMD + integer SIMD all
        # rename onto VecRegClass, W1.2; tag domain [0, numVecPhysRegs)).
        # "_fp" (the three §2.5 wake modes only: "wake_omit_fp" /
        # "src_ready_bitflip_fp" / "wake_phase_fp") keeps the class-agnostic
        # mode and adds --iq_fp_only — the D86 "FP/SIMD 队列版" opClass
        # filter (Float* ∪ SimdFloat*). Plain sub_field keeps
        # targetClass=int + fpOnly off — every pre-W7 manifest unaffected.
        icls = "int"
        ifp = False
        if sf.endswith("_vec"):
            icls = "vec"
            sf = sf[:-len("_vec")]
        elif sf.endswith("_fp"):
            ifp = True
            sf = sf[:-len("_fp")]
        if (inj["model"] == "delay_omission" and sf == "ready_early"):
            im = "ready_early"
        if (inj["model"] == "delay_omission" and sf == "ready_never"):
            im = "ready_never"
        if (inj["model"] == "delay_omission" and sf == "ready_never_event"):
            im = "ready_never_event"
        if (inj["model"] == "legal_domain_sub" and sf == "tag_swap"):
            im = "tag_swap"
        if (inj["model"] == "transient_bit_flip" and sf == "tag_bitflip"):
            im = "tag_bitflip"
        if (inj["model"] == "local_mbu" and sf == "tag_bitflip2"):
            im = "tag_bitflip2"
        if (inj["model"] in ("stuck_at_zero", "stuck_at_one")
                and sf == "tag_stuck"):
            im = "tag_stuck"
        if (inj["model"] == "delay_omission" and sf == "tag_stale_read"):
            im = "tag_stale_read"
        if (inj["model"] == "legal_domain_sub" and sf == "dispatch_misroute"):
            im = "dispatch_misroute"
        cmd += ["--iq_mode", im]
        if im == "wake_phase":
            offset = bits[0] if bits else 1
            cmd += ["--iq_phase_offset", str(offset)]
        cmd += ["--iq_first_clock", str(t["value"]),
                "--iq_max_faults", str(m["limits"]["max_faults"]),
                "--iq_rng_seed", str(m["rng"]["selection_seed"])]
        # W7.4: class axis + D86 fpOnly (suffix convention above).
        if icls == "vec":
            cmd += ["--iq_target_class", "vec"]
        if ifp:
            cmd += ["--iq_fp_only"]
        # v1.1 Phase 8.2: fixed uniform skip / countOnly dry-run.
        if s_skip is not None:
            cmd += ["--iq_events_to_skip", str(s_skip)]
        if s_count:
            cmd += ["--iq_count_only"]
    elif comp == "lsq_fwd":
        # §2.4 CHAOSLSQFwd structured ext. byte_flip / byte_lane_skew / all_zero.
        cmd += ["--chaos_lsqfwd"]
        sm = {"transient_bit_flip": "byte_flip",
              "local_mbu": "byte_lane_skew",
              "intermittent_burst": "byte_lane_skew",
              "delay_omission": "phase_offset",
              "stuck_at_zero": "fwd_source_sub",
              "legal_domain_sub": "all_zero"}.get(inj["model"], "byte_flip")
        # phase_offset: the manifest bit_indices[0] is the offset in
        # cycles (passed to --lsq_lane_skew_k), mirroring the IQ
        # wake_phase convention.
        if sm == "phase_offset":
            offset = bits[0] if bits else 1
            cmd += ["--lsq_lane_skew_k", str(offset)]
        cmd += ["--lsq_struct_mode", sm, "--first_clock", str(t["value"]),
                "--max_faults", str(m["limits"]["max_faults"]),
                "--rng_seed", str(m["rng"]["selection_seed"]),
                "--probability", "1.0",
                "--fault_type", fault_type, "--fault_mask", fault_mask]
        # v1.1 Phase 8.2: fixed uniform skip / countOnly dry-run.
        if s_skip is not None:
            cmd += ["--lsq_events_to_skip", str(s_skip)]
        if s_count:
            cmd += ["--lsq_count_only"]
    elif comp == "exec":
        # §2.12 CHAOSExec (integer execution-unit result XOR).
        cmd += ["--chaos_exec", "--exec_first_clock", str(t["value"]),
                "--exec_max_faults", str(m["limits"]["max_faults"]),
                "--exec_fault_mask", fault_mask,
                "--exec_rng_seed", str(m["rng"]["selection_seed"])]
        # v1.1 Phase 8.2: fixed uniform skip / countOnly dry-run.
        if s_skip is not None:
            cmd += ["--exec_events_to_skip", str(s_skip)]
        if s_count:
            cmd += ["--exec_count_only"]
        # v1.2 Phase 13: fault.exec_mode sub-object routes the CHAOSExec
        # modes (bitseg / recurring_stuck / f3_dependent + val range).
        em_mode = inj.get("exec_mode") or {}
        if em_mode.get("bitseg"):
            cmd += ["--exec_bitseg", str(em_mode["bitseg"])]
        if em_mode.get("recurring_stuck"):
            cmd += ["--exec_recurring_stuck"]
        if em_mode.get("f3_dependent"):
            cmd += ["--exec_f3_dependent"]
        if em_mode.get("val_lo") is not None and em_mode.get("val_hi") is not None:
            cmd += ["--exec_val_range",
                    f"{em_mode['val_lo']},{em_mode['val_hi']}"]
    elif comp == "fsu":
        # §2.6 CHAOSFPU (FP/vector execution-unit result XOR).
        cmd += ["--chaos_fpu", "--fpu_first_clock", str(t["value"]),
                "--fpu_max_faults", str(m["limits"]["max_faults"]),
                "--fpu_fault_mask", fault_mask,
                "--fpu_rng_seed", str(m["rng"]["selection_seed"])]
        # v1.1 Phase 8.2: fixed uniform skip / countOnly dry-run.
        if s_skip is not None:
            cmd += ["--fpu_events_to_skip", str(s_skip)]
        if s_count:
            cmd += ["--fpu_count_only"]
        # v1.1 Phase 9 (task_plan 1c): fault.fpu_mode sub-object routes the
        # six CHAOSFPU modes (bitseg / fma_intermediate / recurring /
        # rounding_sub / f3 / fpsr) from the manifest.
        fm_mode = inj.get("fpu_mode") or {}
        if fm_mode.get("bitseg"):
            cmd += ["--fpu_bitseg", str(fm_mode["bitseg"])]
        if fm_mode.get("fma_weighted"):
            cmd += ["--fpu_fma_weighted"]
        if fm_mode.get("recurring_stuck"):
            cmd += ["--fpu_recurring_stuck"]
        if fm_mode.get("rounding_sub"):
            cmd += ["--fpu_rounding_sub"]
        if fm_mode.get("f3_dependent"):
            cmd += ["--fpu_f3_dependent"]
        if fm_mode.get("exp_lo") is not None and fm_mode.get("exp_hi") is not None:
            cmd += ["--fpu_exp_range",
                    f"{fm_mode['exp_lo']},{fm_mode['exp_hi']}"]
        if fm_mode.get("fpsr_suppress"):
            cmd += ["--fpu_fpsr_suppress"]
    elif comp == "l1d_fwd":
        # §2.7 CHAOSL1DForward (post-check escape).
        cmd += ["--chaos_l1dfwd", "--l1dfwd_first_clock", str(t["value"]),
                "--l1dfwd_max_faults", str(m["limits"]["max_faults"]),
                "--l1dfwd_fault_mask", fault_mask,
                "--l1dfwd_rng_seed", str(m["rng"]["selection_seed"])]
        # v1.1 Phase 8.2: fixed uniform skip / countOnly dry-run.
        if s_skip is not None:
            cmd += ["--l1dfwd_events_to_skip", str(s_skip)]
        if s_count:
            cmd += ["--l1dfwd_count_only"]
    elif comp == "bpu":
        # §2.13 CHAOSBPU (dir_flip / target_flip F5).
        cmd += ["--chaos_bpu"]
        bm = {"transient_bit_flip": "dir_flip",
              "local_mbu": "target_flip",
              "legal_domain_sub": "target_flip",
              # v1.2 Phase 16 (item 1): return-stack F5.
              "delay_omission": "ras_flip"}.get(inj["model"], "dir_flip")
        cmd += ["--bpu_mode", bm, "--bpu_first_clock", str(t["value"]),
                "--bpu_max_faults", str(m["limits"]["max_faults"]),
                "--bpu_rng_seed", str(m["rng"]["selection_seed"])]
    elif comp == "decode":
        # §2.14 CHAOSDecode (dest_reg_sub F5, per-inst via _flatDestIdx).
        # W6 D01-D07 (ooo 04-design-matrix R2-R8 Int Decode): the
        # encoding-corruption modes at the FETCH decode output (flip bits
        # of the raw A64 encoding, re-decode cache-bypassing, replace the
        # fetch-local staticInst). Selected by the v2 target.sub_field
        # discriminator (the W5 ROB pc_bitflip/destid_* pattern); a decode
        # manifest WITHOUT sub_field keeps the legacy dest_reg_sub mapping
        # (backward compatible):
        #   opcode_bitflip/opcode_bitflip2 (D01/D02): 1/2 random bits of
        #        the opcode region {31,30,29,28-24,21} (transient_bit_flip/
        #        local_mbu) — may land legal OR illegal (illegal -> Unknown
        #        -> SIGILL, the expected Crash baseline).
        #   opcode_swap (D03, legal_domain_sub 换值): format-compatible
        #        LEGAL opcode pair (ADD<->SUB, AND<->ORR, MOVZ<->MOVN,
        #        LDR<->STR, ...; GNU-as verified table).
        #   reg_bitflip/reg_bitflip2 (D04/D05): 1/2 bits of the reg-number
        #        positions Rd[4:0]/Rn[9:5]/Rm[20:16], semantically
        #        verified (mnemonic unchanged AND a reg operand moved).
        #   imm_bitflip/imm_bitflip2 (D06/D07): 1/2 bits of the immediate
        #        region [21:10], semantically verified (mnemonic and reg
        #        operands unchanged — value-only change).
        #   W6 batch 2 (D08-D10, R9-R11):
        #   sign_ext_bit (D08): flip EXACTLY the format-located sign/top
        #        bit of the immediate's encoding (per-format GNU-as-verified
        #        table: imm12 bit21 / imms bit20 / imm9 bit20 / imm19 bit23 /
        #        imm14 bit18 / imm26 bit25 / adrp immhi bit23 / imm16 bit20);
        #        the re-decode's own sign-extension consumes the flip.
        #   imm_subfield_shift (D09): transpose two equal-width named
        #        subfields of the immediate encoding (imms<->immr,
        #        immlo<->immhi[1:0], hw<->imm16[15:14], sh<->imm12[11:10]);
        #        single-contiguous-field formats honestly skipped + logged.
        #   crack_ctrl (D10, exploratory): on macroop (cracked) LDP/STP
        #        decodes, flip the addressing-mode field enc[24:23] within
        #        {post,offset,pre} — ±1 µop (spurious/lost writeback µop)
        #        or composition swap, µop counts logged; non-macroop
        #        instructions honestly skipped (force-crack blocker).
        #   W7 batch 1 (D56-D61, R57-R62 FP/SIMD Decode): same engine
        #        gated by fpOnly (opClass in scalar Float* ∪ SimdFloat* —
        #        the CHAOSFPU.cc:88-98 scope; integer SIMD out of scope,
        #        documented honesty limitation):
        #   fp_opcode_bitflip/fp_opcode_bitflip2 (D56/D57): 1/2 random bits
        #        of the FP/SIMD opcode region enc[23:10] — may land legal
        #        OR illegal (illegal -> Unknown -> SIGILL, Crash baseline).
        #   fp_opcode_swap (D58, legal_domain_sub 换值): format-compatible
        #        LEGAL FP pair (FADD<->FSUB, FMUL<->FDIV, FMAX<->FMIN,
        #        FMAXNM<->FMINNM, FMADD<->FMSUB, FNMADD<->FNMSUB,
        #        FCMP<->FCMPE + SIMD mirrors; GNU-as closed-loop verified
        #        table).
        #   fp_reg_bitflip/fp_reg_bitflip2 (D59/D60): 1/2 bits of the
        #        V-reg-number positions Vd[4:0]/Vn[9:5]/Vm[20:16] — the W6
        #        reg_bitflip machinery unchanged, semantically verified
        #        (mnemonic unchanged AND a reg operand moved).
        #   fp_route_bit (D61): 1 bit of the top-level A64 class field
        #        enc[28:24] with an opClass-change predicate (the honest
        #        gem5 approximation of the int-vs-FP/SIMD queue routing
        #        bit; observable = FU/latency effect); no effective bit ->
        #        honest skip.
        dm = "dest_reg_sub"
        dsf = str(tgt.get("sub_field", ""))
        if dsf in ("opcode_bitflip", "opcode_bitflip2", "opcode_swap",
                   "reg_bitflip", "reg_bitflip2",
                   "imm_bitflip", "imm_bitflip2", "dest_reg_sub",
                   "sign_ext_bit", "imm_subfield_shift", "crack_ctrl",
                   "fp_opcode_bitflip", "fp_opcode_bitflip2",
                   "fp_opcode_swap", "fp_reg_bitflip",
                   "fp_reg_bitflip2", "fp_route_bit"):
            dm = dsf
        cmd += ["--chaos_decode", "--decode_mode", dm,
                "--decode_first_clock", str(t["value"]),
                "--decode_max_faults", str(m["limits"]["max_faults"]),
                "--decode_rng_seed", str(m["rng"]["selection_seed"])]
    elif comp in ("l1d", "l1i", "l2"):
        # §2.7/§2.8/§2.11 CHAOSCache (field-level: data/valid/dirty/coh).
        # Routes through arm_chaos_cache.py (C0-CACHE family) — the CHAOSCache
        # mounts via _pre_instantiate, not via arm_chaos.py's cpu-attached
        # injectors. l1i additionally carries --l1i_semantic_field (§2.11:
        # the tag-vs-data semantic distinction; fault.model stuck_at_zero ->
        # tag field, stuck_at_one -> data field as the two semantic arms).
        # The manifest must use config_family C0-CACHE.
        if cfg_family != "C0-CACHE":
            sys.exit(f"[runner] component '{comp}' requires platform."
                     f"config_family='C0-CACHE' (arm_chaos_cache.py). "
                     f"Aborting.")
        cmd += ["--target", comp, "--first_clock", str(t["value"]),
                "--max_faults", str(m["limits"]["max_faults"]),
                "--rng_seed", str(m["rng"]["selection_seed"]),
                "--fault_type", fault_type,
                # §1.2 protection-aware: CHAOSCache's protectionModel (none |
                # sed | secded | secded_poison). Manifest carries it via
                # fault.protection_model (campaign.py Phase 2.1); default
                # "none" preserves the raw-sensitivity cell semantics.
                "--protection_model", inj.get("protection_model", "none")]
        # v1.1 Phase 11 (task_plan 3b): fault.target_block_addr pins the
        # fault to one cache block (directed L2/L1D injection on the
        # working-set-aware kernels).
        if inj.get("target_block_addr") is not None:
            cmd += ["--target_block_addr", str(inj["target_block_addr"])]
        # v1.2 Phase 14: fault.target_field (l1d/l2 field-level arm:
        # data/valid/dirty/coh/tag — tag = the F5 legal alias).
        if inj.get("target_field"):
            cmd += ["--target_field", str(inj["target_field"])]
        # v1.2 Phase 14 (item 2): victim/writeback-path fault.
        if inj.get("victim_fault"):
            cmd += ["--victim_fault"]
        # v1.3 Phase 20 §23: L3 paired-sector fault-domain proxy.
        if inj.get("paired"):
            cmd += ["--paired"]
        # v1.1 Phase 11 (open item): L2 capacity sweep axis.
        if inj.get("l2_size"):
            cmd += ["--l2_size", str(inj["l2_size"])]
        # §2.11 L1I A64 field stratification (Phase 3 closure): the
        # semantic axis is the INSTRUCTION-ENCODING field corrupted in the
        # fetched bytes — opcode (wrong-opcode arm) vs rn (wrong-register
        # arm). fault.model stuck_at_zero -> opcode, stuck_at_one -> rn.
        if comp == "l1i":
            sf = {"stuck_at_zero": "opcode",
                  "stuck_at_one": "rn"}.get(inj["model"], "none")
            # v1.2 Phase 16 (item 3): direct field override (imm/rm/rd/cond
            # arms beyond the opcode/rn model mapping).
            if inj.get("l1i_field"):
                sf = str(inj["l1i_field"])
            cmd += ["--l1i_semantic_field", sf]
    elif comp == "l1_tlb":
        # §2.10 CHAOSArmTLB (D-TLB pfn, FS-only). Requires config_family
        # C0-FS (arm_chaos_fs.py + gem5-fs kernel/disk/bootloader).
        if cfg_family != "C0-FS":
            sys.exit("[runner] component 'l1_tlb' requires platform."
                     "config_family='C0-FS' (arm_chaos_fs.py, needs gem5-fs "
                     "kernel/disk/bootloader). Aborting.")
        # §2.10 F5 (Phase 4.4): legal_domain_sub -> pfn_to_mapped_page
        # (substitute with another mapped entry's pfn — silent wrong-page
        # access; the method2 silent-SDC pathway). Default bit_flip.
        tf = {"legal_domain_sub": "pfn_to_mapped_page"}.get(
            inj["model"], "bit_flip")
        cmd += ["--chaos_armtlb", "--tlb_probability", "1.0",
                "--tlb_fault_type", tf,
                "--tlb_first_clock", str(t["value"]),
                "--tlb_max_faults", str(m["limits"]["max_faults"]),
                "--tlb_rng_seed", str(m["rng"]["selection_seed"])]
    elif comp == "sysreg":
        # §2.10 CHAOSArmSysReg (MRS read-path, FS-only).
        if cfg_family != "C0-FS":
            sys.exit("[runner] component 'sysreg' requires platform."
                     "config_family='C0-FS'. Aborting.")
        # §2.10 F5 (Phase 4.5): legal_domain_sub -> value_to_legal
        # (substitute the MRS-read value with another whitelisted sysreg's
        # current value — silent misconfiguration). Default bit_flip.
        sf = {"legal_domain_sub": "value_to_legal"}.get(
            inj["model"], "bit_flip")
        # §2.10 whitelist (design doc): the §2.10 C spec set. value_to_legal
        # needs >=2 entries (cross-reg substitution); bit_flip runs on the
        # same whitelist for the contrast arm.
        wl = ("sctlr_el1,ttbr0_el1,tcr_el1,mair_el1,vbar_el1,"
              "contextidr_el1,nzcv")
        cmd += ["--chaos_sysreg", "--sysreg_probability", "1.0",
                "--sysreg_fault_type", sf,
                "--sysreg_target_regs", wl,
                "--sysreg_first_clock", str(t["value"]),
                "--sysreg_max_faults", str(m["limits"]["max_faults"]),
                "--sysreg_rng_seed", str(m["rng"]["selection_seed"])]
    elif comp == "exmon":
        # §2.4 CHAOSExMon (exclusive monitor, stxr_force_success/fail).
        cmd += ["--chaos_exmon", "--exmon_mode", "stxr_force_fail",
                "--exmon_first_clock", str(t["value"]),
                "--exmon_max_faults", str(m["limits"]["max_faults"]),
                "--exmon_rng_seed", str(m["rng"]["selection_seed"]),
                "--probability", "1.0"]
    elif comp == "ras":
        # §2.18 CHAOSRAS (exc_suppress at commit fault-check).
        cmd += ["--chaos_ras", "--ras_first_clock", str(t["value"]),
                "--ras_max_faults", str(m["limits"]["max_faults"]),
                "--ras_rng_seed", str(m["rng"]["selection_seed"]),
                "--probability", "1.0"]
    elif comp == "addr_path":
        # §2.4 CHAOSAddrPath (AGU address-path, SE-inert, FS-only).
        cmd += ["--chaos_addrpath", "--addrpath_mode", "byte7_zero",
                "--addrpath_first_clock", str(t["value"]),
                "--addrpath_max_faults", str(m["limits"]["max_faults"]),
                "--addrpath_rng_seed", str(m["rng"]["selection_seed"])]
    elif comp == "ptw":
        # §2.10 CHAOSPTW (page-table-walker, FS-only). Phase 5.3: arm_chaos_fs.py
        # now mounts CHAOSPTW (--chaos_ptw + the ptw_* knobs). Requires
        # config_family C0-FS. clear_valid (H7) maps from stuck_at_zero;
        # single_bit_xor (default) from transient_bit_flip. ptw_ecc follows the
        # manifest's protection_model: 'none' -> ECC OFF (spurious>0), anything
        # else -> ECC ON (the H7 ECC-on arm).
        if cfg_family != "C0-FS":
            sys.exit("[runner] component 'ptw' requires platform."
                     "config_family='C0-FS' (arm_chaos_fs.py with --chaos_ptw). "
                     "Aborting.")
        pm = {"stuck_at_zero": "clear_valid"}.get(inj["model"], "single_bit_xor")
        ecc_on = str(inj.get("protection_model", "secded") != "none").lower()
        cmd += ["--chaos_ptw", "--ptw_mode", pm,
                "--ptw_first_clock", str(t["value"]),
                "--ptw_max_faults", str(m["limits"]["max_faults"]),
                "--ptw_rng_seed", str(m["rng"]["selection_seed"]),
                "--ptw_ecc", ecc_on]
    else:
        # §1.6 v2 honest-reject contract: the v2 schema forward-declares S1
        # components (rob/iq/rat/freelist/lsq_fwd/sysreg/ptw/l3/...), but their
        # runner.py mapping + CHAOS injector do not exist yet (S1/S2/S4
        # patches). Without this reject, an unmapped component would fall
        # through and run gem5 with NO --chaos_* flag -> golden run ->
        # mis-classified as Masked (a silent mis-run, not a real FI outcome).
        # Reject clearly so the manifest is never silently mis-triggered.
        # NOTE: l1i/l2 cache components route through arm_chaos_cache.py (a
        # separate config), not this arm_chaos.py harness — call that out too.
        if comp in ("l1i", "l2"):
            sys.exit(f"[runner] target.component='{comp}' is a cache component "
                     f"that routes through configs/se/arm_chaos_cache.py, not "
                     f"this arm_chaos.py harness. Use the cache config / the "
                     f"CHAOSCache mount. Aborting — not silently mis-running.")
        sys.exit(f"[runner] target.component='{comp}' is forward-declared in "
                 f"the v2 schema but NOT mapped in runner.py yet (needs the "
                 f"corresponding CHAOS injector: rob->CHAOSROB §2.3, "
                 f"iq->CHAOSIQ §2.5, rat/freelist->CHAOSRenameMap/CHAOSFreeList "
                 f"§2.2, lsq_fwd->CHAOSLSQFwd F5/F6 §2.4, sysreg/ptw->§2.10, "
                 f"l3->CHAOSCHI §2.9, etc. — all S1/S2/S4 patches). Aborting "
                 f"— not silently mis-running an unmapped component.")

    print(f"[runner] manifest target: layer={layer} comp={comp} idx={idx} "
          f"bits={bits} width={width} field={field}")
    # platform.config_params -> config-script microarch knobs (H2 sweep)
    if cfg_params:
        for k, v in cfg_params.items():
            cmd += [f"--{k}", str(v)]
        print(f"[runner] config_params: {cfg_params}")
    # W2.3 L2 commit trace: C3-only (validated above). An ABSOLUTE path pins
    # the trace to this exact location regardless of the config's --outdir
    # handling (ooo_proxy resolves a relative --ctrace_file against its
    # --outdir, which is the runner's private man-* tempdir).
    if args.ctrace:
        ctrace_path = os.path.abspath(args.ctrace)
        cmd += ["--chaos_ctrace", "--ctrace_file", ctrace_path]
        note = f" (diff vs ref {os.path.abspath(args.ctrace_ref)})" if args.ctrace_ref else ""
        print(f"[runner] ctrace: {ctrace_path}{note}")
    print("[runner] running:", " ".join(cmd[:4]), "...")
    # Hang timeout (plan §13.2): a normal sim completes in well under the
    # wall budget; a Hang = no completion within this. Default 600s; the
    # manifest may specify limits.max_ticks but we bound on wall time here.
    HANG_TIMEOUT = 600
    timed_out = False
    # W2.3 determinism (W1.3 cross-environment micro-difference lesson): pin
    # PYTHONHASHSEED for the gem5 child. setdefault — an explicitly inherited
    # value (e.g. campaign.py's pinned 0) wins; standalone invocations get a
    # fixed 0 instead of a per-process random seed.
    child_env = dict(os.environ)
    child_env.setdefault("PYTHONHASHSEED", "0")
    try:
        r = subprocess.run(cmd, capture_output=True, text=True,
                           timeout=HANG_TIMEOUT, env=child_env)
    except subprocess.TimeoutExpired as e:
        timed_out = True
        # Build a pseudo-result from whatever was captured. e.stdout/stderr may
        # be bytes even with text=True under some py versions — normalize.
        def _to_str(x):
            if isinstance(x, bytes):
                return x.decode("utf-8", errors="replace")
            return x or ""
        r = subprocess.CompletedProcess(
            cmd, returncode=-1, stdout=_to_str(e.stdout), stderr=_to_str(e.stderr))

    # collect faults_injected from the injection log(s).
    # CHAOSReg log: "Cycle: ..., Register: integer[9], FaultType: bit_flip, ..."
    # CHAOSMem log: "...faults_injected: N" (explicit count)
    # CHAOSCache log: per-injection line. We count NON-Inactive/Error lines as
    # valid injections (an XZR-Inactive or "Error:" line does not count).
    # CHAOSPhysReg log: a "Cycle:" line with "PhysReg[" is a real injection;
    #   the "ReadTracePoll:" / "ReadTraceFinal:" lines are NOT.
    outdir = None
    for i, a in enumerate(cmd):
        if a == "-d" and i+1 < len(cmd):
            outdir = cmd[i+1]
    faults = 0
    for logname in ("fault_injections.log","main_mem_injections.log","cache_injections.log","rename_injections.log","freelist_injections.log","rob_injections.log","iq_injections.log","exec_injections.log","fpu_injections.log","l1d_fwd_injections.log","bpu_injections.log","addrpath_injections.log","decode_injections.log","ras_injections.log","exmon_injections.log","ptw_injections.log","noc_injections.log","chi_injections.log","lsq_fwd_injections.log","armtlb_injections.log","sysreg_injections.log"):
        p = os.path.join(outdir, logname) if outdir else None
        if p and os.path.exists(p):
            with open(p) as lf:
                for line in lf:
                    # explicit count (CHAOSMem G5 evidence log)
                    if "faults_injected:" in line:
                        try:
                            faults = int(line.split("faults_injected:")[1].split()[0])
                        except Exception:
                            pass
                        continue
                    # CHAOSPhysReg: exclude ReadTrace* poll lines (not injections)
                    if line.startswith("ReadTracePoll") or line.startswith("ReadTraceFinal"):
                        continue
                    # CHAOSReg: exclude the DIRECTED info line (it's an advisory,
                    # not an injection; the actual injection is the next "Cycle:"
                    # line with "Register:"/"FaultType:").
                    if "DIRECTED reg:" in line:
                        continue
                    # CHAOSCache protection-outcome line ("    protection:
                    # model=... -> Raw/Corrected/..."): an annotation of the
                    # injection ABOVE it, not a second injection. Counting it
                    # double-reported every cache injection as faults=2 (found
                    # via the L2 pilot; the L1D formal's 384 reps all carry
                    # faults=2 — classification unaffected (classify uses
                    # faults>=1 boolean) but the G5 evidence value was wrong.
                    if line.lstrip().startswith("protection:"):
                        continue
                    # CHAOSFreeList D17/D18/D74/D75: the DUPLICATE_ALLOCATION
                    # watcher line is the EVIDENCE that the re-added idx was
                    # re-handed-out (the second allocation of the ONE injected
                    # duplicate) — not a second injection. Counting it
                    # double-reported every mark_free(_event) run whose
                    # duplicate re-fired within the run as faults=2 (found in
                    # the W7.3 vec E2E; same class as the "protection:" fix
                    # above — classification unaffected, G5 evidence wrong).
                    if "DUPLICATE_ALLOCATION:" in line:
                        continue
                    # count valid injection lines: exclude Inactive/Error
                    if ("Inactive" in line) or line.startswith("Error"):
                        continue
                    if line.strip():
                        faults += 1
            break
    # G5 assertion: exactly 0 or 1 valid injection — EXCEPT the v1.1
    # Phase 8.4 recurring_result_stuck model, whose permanent fault
    # legitimately corrupts every eligible event (N>1 by design).
    if faults not in (0,1) and not _recurring:
        print(f"[runner] G5 VIOLATION: faults_injected={faults} (not in {{0,1}}) "
              f"— run invalid")
    if _recurring:
        print(f"[runner] recurring model: faults_injected={faults} "
              f"(N>1 expected for the permanent recurring fault)")

    stdout_text = r.stdout if r.stdout else ""
    cls, reason = classify_run(stdout_text, r.stderr or "", r.returncode,
                               faults, args.golden_checksum, timed_out,
                               fs_mode=(cfg_family in ("C0-FS", "C2-FS")),
                               oracle_kind=oracle_kind,
                               oracle_tol=oracle_tol)
    print(f"[runner] RESULT: run_id={m['run_id']} classification={cls} "
          f"faults_injected={faults} exit={r.returncode} "
          f"timed_out={timed_out} oracle={oracle_kind}")
    print(f"[runner]   reason: {reason}")
    # ---- W2.6 (plan Task 6): stats.txt summary consumption ----
    # Parsed by campaign.py's parse_runner_result into the rep's results.jsonl
    # `stats` block. Opt-in (--stats) so legacy invocations keep their exact
    # stdout (the W2.3 regression contract: no new flag, no new line).
    if args.stats:
        stats = extract_stats_summary(outdir)
        print("[runner] STATS: " + json.dumps(stats, ensure_ascii=False))
    # ---- W2.3: L2 commit-trace evidence + five-class merge (commit_diff) ----
    # CTRACE prints where the trace landed and how many committed instructions
    # it holds (parsed by campaign.py's parse_runner_result). L2RESULT carries
    # the commit_diff five-class JSON (or an honest l2_error dict) printed as
    # ONE line so the campaign can merge it into the rep's results.jsonl l2.
    if args.ctrace:
        ctrace_path = os.path.abspath(args.ctrace)
        if os.path.exists(ctrace_path):
            nbytes = os.path.getsize(ctrace_path)
            nlines = count_trace_lines(ctrace_path)
            # None = unreadable (typically a truncated trace from a Crash
            # rep: gem5 aborts before the gzip stream is finalized)
            print(f"[runner] CTRACE: file={ctrace_path} "
                  f"lines={nlines if nlines is not None else 'unreadable'} "
                  f"bytes={nbytes}")
        else:
            print(f"[runner] CTRACE: file={ctrace_path} MISSING")
        if args.ctrace_ref:
            l2 = run_commit_diff(os.path.abspath(args.ctrace_ref),
                                 ctrace_path)
            print("[runner] L2RESULT: " + json.dumps(l2, ensure_ascii=False))
        # ---- W2.6 (plan Task 6): L3 fanout of --fanout-phys on this run's
        # trace (tools/fanout.py; liveness windows + val changes). Parsed by
        # campaign.py into the rep's results.jsonl `l3` block. The honest
        # metric is documented in fanout.py: source reads are not traced, so
        # the liveness window is an upper-bound proxy for consumer reads.
        if args.fanout_phys is not None:
            l3 = run_fanout(ctrace_path, args.fanout_phys)
            print("[runner] L3RESULT: " + json.dumps(l3, ensure_ascii=False))
    return 0

if __name__ == "__main__":
    sys.exit(main())
