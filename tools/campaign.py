#!/usr/bin/env python3
"""Grid campaign driver for the ARM64 CHAOS SDC fault-injection tool
(design doc `docs/KUNPENG920-故障注入方案详细工程设计.md` §1.5).

A campaign expands a Cartesian product of grid axes into immutable per-rep
single-fault manifests (max_faults=1), runs each rep via the EXISTING
`tools/runner.py` (subprocess), collects the 9-class outcome, and summarizes
per-cell Wilson 95% CI (§1.4) + a 5% replay-consistency check (§1.5).

THIS DRIVER REUSES runner.py — it does NOT reimplement the manifest->gem5
arg mapping, the classifier, or the G5 single-fault assertion. Each rep shells
out to `tools/runner.py <manifest.yaml> --binary <bin>` and parses the
`RESULT: classification=... faults_injected=... exit=...` stdout line. This is
the honest path: one classifier, one mapping, no drift.

It is injector-agnostic by construction: any injector already wired into
runner.py (gpr/physreg/memory/cache/lsqfwd) is campaignable today. Injectors
declared in the schema enum but not yet mapped (rat/rob/iq/...) cause runner.py
to reject with a clear error — the driver surfaces that as a SimulatorError
cell, never silently mis-runs.

Usage:
  python3 tools/campaign.py campaigns/example-prf-pilot.yaml [--jobs N] \\
      [--n_per_cell N] [--replay_pct P] [--dry] [--keep_manifests]

Outputs:
  runs/<campaign_id>/<cell_idx>/<run_id>.yaml   (immutable per-rep manifest)
  runs/<campaign_id>/<cell_idx>/results.jsonl  (one JSON per rep)
  artifacts/<campaign_id>/heatmap.csv          (per-cell point + CI)
  artifacts/<campaign_id>/summary.md           (human-readable + honesty notes)

NOTE (§0.4 honesty): this fault machine (cpu179) takes ~92s/run — formal n=384
campaigns belong on a healthy 2nd machine. This driver is machine-agnostic; the
results it produces on cpu179 are PILOT-only and must be replicated before any
formal claim (§3.1 S6).
"""
import sys, os, json, argparse, tempfile, subprocess, itertools, time, signal

REPO = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
from wilson import cell_stats, ALL_CLASSES  # noqa: E402

try:
    import yaml
except ImportError:
    sys.exit("ERROR: pip install pyyaml  (needed for campaign.yaml parsing)")

# jsonschema optional (runner.py already does light manifest validation; the
# campaign schema check here is best-effort and degrades to a manual review).
try:
    import jsonschema
    HAVE_SCHEMA = True
except ImportError:
    HAVE_SCHEMA = False

RUNNER = os.path.join(REPO, "tools", "runner.py")

# W2.3 determinism (W1.3 cross-environment micro-difference lesson): every
# runner.py child of this campaign — and through it every gem5 and
# commit_diff grandchild — runs with PYTHONHASHSEED pinned to 0. The value is
# FORCED (not setdefault): the campaign contract is one fixed hash seed for
# the whole process tree, whatever the invoking shell happened to export.
CHILD_ENV = dict(os.environ)
CHILD_ENV["PYTHONHASHSEED"] = "0"

# W2.3 ref-provenance guard: the trace two-pass only means anything when the
# ref trace and the replay traces come from the SAME gem5.opt. A rebuild that
# swaps the binary between the ref pass and a replay pass turns the
# commit_diff verdict into garbage (found live 2026-09-24: a parallel W2.4
# rebuild replaced build/ARM/gem5.opt mid-campaign). gem5_sha256() is cached
# per (mtime_ns, size) so the ~3s hash of the 1.1GB binary is recomputed only
# when the file actually changed.
_G5_SHA_STATE = None  # (mtime_ns, size) -> sha256


def gem5_sha256():
    """sha256 of build/ARM/gem5.opt, stat-cached; '<unreadable: ...>' on IO
    error (the caller compares strings, never crashes on a missing binary)."""
    global _G5_SHA_STATE
    p = os.path.join(REPO, "build/ARM/gem5.opt")
    try:
        st = os.stat(p)
    except OSError as e:
        return f"<unreadable: {e}>"
    key = (st.st_mtime_ns, st.st_size)
    if _G5_SHA_STATE is not None and _G5_SHA_STATE[0] == key:
        return _G5_SHA_STATE[1]
    import hashlib
    h = hashlib.sha256()
    try:
        with open(p, "rb") as f:
            for chunk in iter(lambda: f.read(1 << 20), b""):
                h.update(chunk)
    except OSError as e:
        return f"<unreadable: {e}>"
    sha = h.hexdigest()
    _G5_SHA_STATE = (key, sha)
    return sha


# ---------------------------------------------------------------- grid expansion

def _expand_axis(val):
    """A grid axis value is either a scalar or a list-of-scalars. Normalize to
    a list of scalars so itertools.product can consume it."""
    if isinstance(val, list):
        return val
    return [val]


def expand_grid(grid):
    """Cartesian product of grid axes. Returns a list of dicts, one per cell:
    each dict maps axis-name -> chosen scalar value. Order is deterministic
    (Python dict preserves insertion order; itertools.product is ordered).

    An axis whose value list is EMPTY is treated as 'no stratification on this
    axis' (e.g. bit: [] means 'random mask, no specific bit') — it is dropped
    from the product rather than collapsing the product to zero cells. This
    mirrors runner.py's 'faultMask=0 -> randomly generated' convention.
    """
    if not grid:
        return [{}]
    # drop empty-list axes (random/unstratified), keep the rest
    keys = [k for k in grid if len(_expand_axis(grid[k])) > 0]
    value_lists = [_expand_axis(grid[k]) for k in keys]
    cells = []
    for combo in itertools.product(*value_lists):
        cells.append({k: v for k, v in zip(keys, combo)})
    return cells


def cell_id_str(cell_idx, cell):
    """Stable short string identifying a cell for logs, e.g. 'idx3_bit20'."""
    parts = [f"{k}={v}" for k, v in cell.items()]
    return " ".join(parts)


# ---------------------------------------------------------------- manifest write

# v1.1 Phase 8.2: uniform event sampling (design doc §1.7 rule 4). The
# legacy geometric(p=0.1) skip concentrates the single fault in the first
# ~30 eligible events (mean 10, P(<=30)~=96%). The two-step replacement:
#   1. countOnly dry-run: run the cell's manifest with sampling.count_only
#      once; the injector consumes eligible events WITHOUT corrupting and
#      prints CHAOS_ELIGIBLE_COUNT=<n> in its log at teardown.
#   2. the per-rep manifest carries sampling.events_to_skip =
#      chaos_pick_skip(seed, N_eligible) — a seed-derived UNIFORM draw over
#      [0, N) (same LCG as the C++ helper chaos_event_sample.hh so the
#      driver and the injector agree bit-for-bit).
def chaos_pick_skip(seed, n_eligible):
    """Python twin of gem5::chaosPickSkip (cpu/o3/chaos_event_sample.hh):
    one LCG round of the seed, modulo n_eligible."""
    if n_eligible <= 0:
        return 0
    x = (seed ^ 0x9E3779B97F4A7C15) & 0xFFFFFFFFFFFFFFFF
    x = (x * 6364136223846793005 + 1442695040888963407) & 0xFFFFFFFFFFFFFFFF
    return x % n_eligible


# injector component -> (runner resultdir log name with CHAOS_ELIGIBLE_COUNT)
_ELIGIBLE_LOG = {
    "fsu": "fpu_injections.log", "exec": "exec_injections.log",
    "l1d_fwd": "l1d_fwd_injections.log", "iq": "iq_injections.log",
    "lsq_fwd": "lsq_fwd_injections.log",
}


def count_eligible_events(campaign, cell, cell_ordinal, outdir, binary,
                          hang_timeout):
    """v1.1 Phase 8.2 step 1: one countOnly dry-run of the cell's manifest.
    Returns N_eligible (int) or None when the injector has no countOnly
    support (component not in _ELIGIBLE_LOG) — None = legacy geometric
    sampling stays in effect for that campaign."""
    inj = campaign["injector"]
    comp_map = {"gpr": "gpr", "physreg": "physreg", "memory": "memory",
                "cache": "l1d", "lsqfwd": "physreg",
                "rat": "rat", "freelist": "freelist", "rob": "rob", "iq": "iq"}
    comp = comp_map.get(inj, inj)
    if comp not in _ELIGIBLE_LOG:
        return None
    # build the count manifest (rep 0 seed; the count is deterministic in
    # the workload+trigger, independent of the rep seed)
    mpath, man = manifest_for_cell(campaign, dict(cell), cell_ordinal, 0,
                                   outdir)
    man["sampling"] = {"count_only": True}
    with open(mpath, "w") as f:
        yaml.safe_dump(man, f, sort_keys=False, default_flow_style=False)
    # run it through runner.py (single rep, no replay)
    cmd = [sys.executable, RUNNER, mpath, "--binary", binary]
    try:
        import subprocess as _sp
        r = _sp.run(cmd, capture_output=True, text=True,
                    timeout=hang_timeout + 30)
    except Exception:
        return None
    # the injector's log lands in runner's tempfile -d dir; runner prints
    # the command with it. Simpler: find the newest man-* dir's log.
    import tempfile as _tf, glob as _glob, re as _re
    cands = sorted(_glob.glob(os.path.join(_tf.gettempdir(), "man-*")),
                   key=os.path.getmtime, reverse=True)
    for d in cands[:3]:
        lp = os.path.join(d, _ELIGIBLE_LOG[comp])
        if os.path.exists(lp):
            for line in open(lp):
                mm = _re.search(r"CHAOS_ELIGIBLE_COUNT=(\d+)", line)
                if mm:
                    return int(mm.group(1))
    return None


def manifest_for_cell(campaign, cell, cell_ordinal, rep, outdir):
    """Build an arm-chaos-fi/v1 manifest (reuses the EXISTING v1 schema that
    runner.py validates) for one (cell, rep), write it to outdir, return path.

    Seed rule (§1.5): base_seed + cell_ordinal*1000 + rep -> deterministic,
    reproducible across machines.
    """
    wl = campaign["workload"]
    inj = campaign["injector"]
    limits = campaign.get("limits", {})
    base = campaign["base_seed"]
    seed = base + cell_ordinal * 1000 + rep
    run_id = f"{campaign['campaign_id']}-c{cell_ordinal:04d}-r{rep:04d}"

    # H2 microarch axes (rob/phys_int/phys_float/lq/sq) live in the grid
    # alongside fault axes but are config knobs, not fault fields. Pull them
    # out of the cell so they flow to platform.config_params only.
    MICROARCH_AXES = ("rob", "phys_int", "phys_float", "lq", "sq")
    config_params = {k: cell[k] for k in MICROARCH_AXES if k in cell}
    cell = {k: v for k, v in cell.items() if k not in MICROARCH_AXES}

    # target component <-> injector (schema enum is wider than what runner.py
    # maps today; runner.py will reject unmapped ones with a clear error).
    # History note: freelist/rob/iq were once mapped to "rat" as a
    # forward-declaration placeholder from when runner.py only knew rat —
    # that silently re-routed those campaigns' manifests to the RAT
    # injector (rob/iq formals were invalid; found 2026-09-04, fixed here).
    comp_map = {
        "gpr": "gpr", "physreg": "physreg", "memory": "memory",
        "cache": "l1d", "lsqfwd": "physreg",  # cache->l1d; lsqfwd uses physreg
        # runner.py maps these components directly (freelist/rob/iq branches):
        "rat": "rat", "freelist": "freelist", "rob": "rob", "iq": "iq",
    }
    comp = comp_map.get(inj, inj)
    layer = "physical" if (inj == "physreg" and cell.get("phys_mode") == "phys") else "architectural"

    manifest = {
        "schema_version": "arm-chaos-fi/v1",
        "campaign_id": campaign["campaign_id"],
        "run_id": run_id,
        "source": {
            "chaos_commit": campaign.get("chaos_commit", "HEAD"),
            "gem5_commit": "62c7bf284864b83f7308f5e14ca9c80812621c29",
            "patchset_sha256": "TBD",
        },
        "platform": {
            "isa": "ARM64",
            "mode": campaign.get("mode", "SE"),
            "cpu_model": campaign.get("cpu_model", "ArmO3CPU"),
            "config_family": campaign.get("config", "C0"),
        },
        # H2 window sweep: grid axes named rob/phys_int/phys_float/lq/sq are
        # MICROARCH KNOBS, not fault axes — collected into
        # platform.config_params (runner whitelists + passes to the C2
        # config). Added only when non-empty so old manifests are unchanged.
        "workload": {
            "binary_sha256": wl.get("binary_sha256", ""),
            "input_sha256": "",
            "roi": wl.get("roi", {}),
            # v1.1 Phase 8.1 (design doc §1.7): non-hash oracles for the
            # per-element kernels. Omitted when the campaign sets none, so
            # legacy exact_hash manifests are byte-identical to before.
            # runner.py reads workload.oracle_kind/workload.oracle_tol (the
            # manifest oracle block mirrors kind for schema visibility).
            **({"oracle_kind": wl["oracle_kind"]}
               if wl.get("oracle_kind") else {}),
            **({"oracle_tol": wl["oracle_tol"]}
               if wl.get("oracle_tol") is not None else {}),
        },
        "trigger": {
            "mode": wl.get("trigger_mode", "cycle"),
            "value": wl.get("trigger_value", 100000),
        },
        "target": {
            "layer": layer,
            "component": comp,
            "instance": "cpu0.thread0",
            "index": cell.get("target_index") if cell.get("target_index") is not None else None,
            "field": cell.get("field", "value"),
            "width_bits": cell.get("width_bits", 64),
        },
        "fault": {
            "model": cell.get("fault_model", "transient_bit_flip"),
            "bit_indices": [cell["bit"]] if "bit" in cell else [],
            "duration_events": 1,
            "stage": campaign.get("fault_stage", "no_protection_model"),
            # §1.2 protection-aware modeling: the cell's protection_model axis
            # (none | sed | secded | secded_poison | parity_interleaved) flows
            # into the manifest so runner.py can pass --protection_model to the
            # configs that support it (arm_chaos_cache.py CHAOSCache,
            # arm_chaos.py CHAOSMem). The v1 schema has no fault.protection
            # field — use the top-level `protection` extension (light validator
            # ignores unknown top-level keys; jsonschema draft-07 with
            # additionalProperties default also allows it).
            "protection_model": cell.get("protection_model", "none"),
        },
        "rng": {"master_seed": seed, "selection_seed": seed},
        # v1.1 Phase 8.4 (task_plan 0d): the recurring_result_stuck model
        # needs max_faults=0 (the permanent fault recurs on every eligible
        # event). Emit 0 for that model so runner.py's pairing check passes;
        # every other model keeps the single-fault contract (default 1).
        "limits": {"max_faults": (0 if cell.get("fault_model") == "recurring_result_stuck"
                                  else limits.get("max_faults", 1)),
                   "max_ticks": 0},
        # v1.1 Phase 8.1: oracle.kind mirrors the campaign's workload
        # .oracle_kind (default exact_hash = legacy). tol rides along for
        # fp_ulp. Kept in the manifest oracle block (schema-visible) AND in
        # workload (runner reads both, workload spelling wins if both set —
        # they are written from the same source here so they agree).
        "oracle": {"kind": wl.get("oracle_kind", "exact_hash"),
                   "golden_id": wl.get("golden_id", ""),
                   **({"tol": wl["oracle_tol"]}
                      if wl.get("oracle_tol") is not None else {})},
    }
    # v1.1 Phase 9 (task_plan 1c): grid axes named fpu_bitseg / fpu_mode_*
    # flow into fault.fpu_mode (runner routes them to the CHAOSFPU CLI
    # flags). Applied after the dict literal closes.
    _fpu_mode = {}
    if cell.get("fpu_bitseg"):
        _fpu_mode["bitseg"] = cell["fpu_bitseg"]
    for _flag in ("fma_weighted", "recurring_stuck", "rounding_sub",
                  "f3_dependent", "fpsr_suppress"):
        if cell.get(f"fpu_mode_{_flag}"):
            _fpu_mode[_flag] = True
    if (cell.get("fpu_mode_exp_lo") is not None
            and cell.get("fpu_mode_exp_hi") is not None):
        _fpu_mode["exp_lo"] = cell["fpu_mode_exp_lo"]
        _fpu_mode["exp_hi"] = cell["fpu_mode_exp_hi"]
    if _fpu_mode:
        manifest["fault"]["fpu_mode"] = _fpu_mode
    # v1.2 Phase 13: Exec mode axes.
    _exec_mode = {}
    if cell.get("exec_bitseg"):
        _exec_mode["bitseg"] = cell["exec_bitseg"]
    for _flag in ("recurring_stuck", "f3_dependent"):
        if cell.get(f"exec_mode_{_flag}"):
            _exec_mode[_flag] = True
    if _exec_mode:
        manifest["fault"]["exec_mode"] = _exec_mode
    # v1.1 Phase 11 (task_plan 3b): directed DRAM window axes.
    _aw = {}
    if cell.get("mem_addr_start") is not None:
        _aw["start"] = cell["mem_addr_start"]
    if cell.get("mem_addr_end") is not None:
        _aw["end"] = cell["mem_addr_end"]
    if _aw:
        manifest["fault"]["addr_window"] = _aw
    # v1.1 Phase 11: directed cache-block axis + L2 capacity axis.
    if cell.get("target_block_addr") is not None:
        manifest["fault"]["target_block_addr"] = cell["target_block_addr"]
    # v1.2 Phase 14: cache field-level arm (data/valid/dirty/coh/tag).
    if cell.get("target_field"):
        manifest["fault"]["target_field"] = cell["target_field"]
    # v1.2 Phase 14 (item 2): victim-path fault axis.
    if cell.get("victim_fault"):
        manifest["fault"]["victim_fault"] = True
    # v1.3 Phase 20 §23: L3 paired-sector proxy axis.
    if cell.get("paired"):
        manifest["fault"]["paired"] = True
    # v1.2 Phase 16 (item 3): L1I instruction-encoding field axis.
    if cell.get("l1i_field"):
        manifest["fault"]["l1i_field"] = cell["l1i_field"]
    # v1.3 Phase 20 §8: vector-lane axis.
    if cell.get("vec_lane") is not None:
        manifest["fault"]["vec_lane"] = cell["vec_lane"]
    # v1.2 Phase 14: DRAM ECC-logic-fault arm (§2.17).
    if cell.get("ecc_logic_fault"):
        manifest["fault"]["ecc_logic_fault"] = True
    if cell.get("l2_size"):
        manifest["fault"]["l2_size"] = cell["l2_size"]
    # clean None values the v1 schema doesn't want
    for k in list(manifest["target"]):
        if manifest["target"][k] is None:
            del manifest["target"][k]

    # H2 microarch knobs -> platform.config_params (additive; skipped when
    # the campaign has no microarch grid axes)
    if config_params:
        manifest["platform"]["config_params"] = config_params

    os.makedirs(outdir, exist_ok=True)
    path = os.path.join(outdir, f"{run_id}.yaml")
    with open(path, "w") as f:
        yaml.safe_dump(manifest, f, sort_keys=False, default_flow_style=False)
    return path, manifest


# ---------------------------------------------------------------- run one rep

RESULT_PREFIX = "RESULT:"
# W2.3 trace two-pass markers printed by runner.py AFTER the RESULT line.
# NOTE: "RESULT:" is a substring of "L2RESULT:" — the L2 branch below must
# match (and consume) its line first, and the RESULT branch must never see it.
L2_PREFIX = "L2RESULT:"
CTRACE_PREFIX = "CTRACE:"
# W2.6 (plan Task 6) markers, same convention. "L3RESULT:" also contains
# "RESULT:" — like L2RESULT it is matched (and consumed) before the RESULT
# branch. "STATS:" collides with nothing.
L3_PREFIX = "L3RESULT:"
STATS_PREFIX = "STATS:"

def parse_runner_result(stdout):
    """Extract (classification, faults, exit_code) from runner.py's
    `[runner] RESULT: run_id=... classification=X faults_injected=N exit=E timed_out=...`
    line. Returns dict; fields None if the line is missing (counted as a
    SimulatorError by the caller — honest, never a silent Masked).

    runner.py prefixes its prints with "[runner] ", so we search for the
    RESULT marker anywhere in the line (not startswith).

    W2.3: also captures the optional `[runner] CTRACE: file=... lines=N
    bytes=B` evidence line and the `[runner] L2RESULT: {json}` five-class
    commit_diff result that runner.py prints after RESULT (only on
    --ctrace runs) — the scan therefore covers ALL lines instead of
    breaking at the first RESULT."""
    res = {"classification": None, "faults_injected": None, "exit": None,
           "timed_out": False, "run_id": None, "ctrace": None, "l2": None}
    for line in (stdout or "").splitlines():
        line = line.strip()
        if L2_PREFIX in line:
            # five-class commit_diff JSON (or an honest {"l2_error": ...})
            try:
                res["l2"] = json.loads(line.split(L2_PREFIX, 1)[1].strip())
            except ValueError:
                res["l2"] = {"l2_error": "unparseable L2RESULT line"}
            continue
        if CTRACE_PREFIX in line:
            body = line.split(CTRACE_PREFIX, 1)[1].strip()
            ct = {"missing": "MISSING" in body}
            for tok in body.split():
                if "=" in tok:
                    k, v = tok.split("=", 1)
                    ct[k] = v
            for numk in ("lines", "bytes"):
                if numk in ct:
                    try:
                        ct[numk] = int(ct[numk])
                    except ValueError:
                        pass
            res["ctrace"] = ct
            continue
        if RESULT_PREFIX in line:
            body = line.split(RESULT_PREFIX, 1)[1].strip()
            for tok in body.split():
                if "=" in tok:
                    k, v = tok.split("=", 1)
                    if k == "classification":
                        res["classification"] = v
                    elif k == "faults_injected":
                        try:
                            res["faults_injected"] = int(v)
                        except ValueError:
                            pass
                    elif k == "exit":
                        try:
                            res["exit"] = int(v)
                        except ValueError:
                            pass
                    elif k == "timed_out":
                        res["timed_out"] = (v.lower() == "true")
                    elif k == "run_id":
                        res["run_id"] = v
    return res


class _PoolRep:
    """Picklable ProcessPoolExecutor worker: carries the run context and
    calls the module-level run_one_rep on the manifest inside each work
    item (ord_i, cell, rep, mpath, outdir). A plain closure local to
    main() is NOT picklable and crashes --jobs>1 — including the old local
    log_bad; we carry bad_log_path and use the module-level _log_bad."""

    def __init__(self, binary, hang_timeout, keep_manifests, bad_log_path,
                 fs_extra=None):
        self.binary = binary
        self.hang_timeout = hang_timeout
        self.keep_manifests = keep_manifests
        self.bad_log_path = bad_log_path
        # §3.2 FS pipeline (Phase 5.4): extra runner flags for FS campaigns
        # (restore-checkpoint/kernel/disk/bootloader/fs-cpu), from the
        # campaign yaml's `fs:` block. None for SE campaigns (no-op).
        self.fs_extra = fs_extra or []

    def __call__(self, item):
        ord_i, cell, rep, mpath, outdir = item
        res = run_one_rep(mpath, self.binary, self.hang_timeout,
                          self.keep_manifests,
                          _log_bad(self.bad_log_path),
                          fs_extra=self.fs_extra)
        return (mpath, res)


def _log_bad(bad_log_path):
    """Module-level bad-run logger factory (picklable context: just the
    path). Same behavior as the old main()-local closure."""
    def log_bad(stderr, stdout, manifest_path):
        with open(bad_log_path, "a") as f:
            f.write(f"=== {manifest_path} ===\n--- stderr ---\n"
                    f"{stderr[-500:]}\n--- stdout ---\n{stdout[-500:]}\n\n")
    return log_bad


def run_one_rep(manifest_path, binary, hang_timeout, keep_manifests, log_bad,
                fs_extra=None, extra_args=None):
    """Shell out to tools/runner.py for one manifest. Returns a result dict
    (classification etc.) for the results.jsonl line.

    The runner is started in its own process group (start_new_session) so a
    campaign-level timeout kills the WHOLE tree — runner.py AND its gem5
    child. Plain subprocess.run(timeout=...) only kills runner.py; the gem5
    grandchild survives as an orphan (PPID=1) and burns a core per hang
    (found 2026-09-04: 80+ leaked gem5 procs after IQ hang runs).

    W2.3: extra_args appends runner CLI flags AFTER fs_extra — the trace
    two-pass passes --ctrace/--ctrace-ref/--no-inject here. Every child runs
    under CHILD_ENV (PYTHONHASHSEED=0, W1.3 lesson).
    """
    cmd = [sys.executable, RUNNER, manifest_path, "--binary", binary]
    # §3.2 FS pipeline (Phase 5.4): forward FS runner flags (restore-
    # checkpoint etc.) — no-op for SE campaigns (fs_extra=[]).
    if fs_extra:
        cmd += list(fs_extra)
    if extra_args:
        cmd += list(extra_args)
    try:
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                             text=True, start_new_session=True, env=CHILD_ENV)
        try:
            out, err = p.communicate(timeout=hang_timeout + 30)
            r = subprocess.CompletedProcess(cmd, p.returncode, stdout=out, stderr=err)
        except subprocess.TimeoutExpired:
            # kill the WHOLE process group (runner + its gem5 child);
            # plain kill would orphan the gem5 grandchild (PPID=1)
            try:
                os.killpg(os.getpgid(p.pid), signal.SIGKILL)
            except Exception:
                p.kill()
            p.wait()
            res = {"classification": "Hang", "faults_injected": None,
                   "exit": -1, "timed_out": True,
                   "reason": f"runner.py exceeded {hang_timeout+30}s wall budget"}
            return res
    except Exception as e:
        res = {"classification": "Hang", "faults_injected": None,
               "exit": -1, "timed_out": True,
               "reason": f"spawn failure: {e}"}
        return res
    out = r.stdout or ""
    parsed = parse_runner_result(out)
    cls = parsed["classification"]
    if cls is None:
        # runner.py itself crashed/errored before printing RESULT (e.g.
        # unsupported injector mapping, schema fail). Honest: SimulatorError.
        cls = "SimulatorError"
        if log_bad:
            log_bad(r.stderr or "", out, manifest_path)
    res = {
        "classification": cls,
        "faults_injected": parsed["faults_injected"],
        "exit": parsed["exit"],
        "timed_out": parsed["timed_out"],
        "run_id": parsed["run_id"],
    }
    # W2.3: trace-run evidence (CTRACE line) + five-class commit_diff result
    # (L2RESULT line); both None on plain runs (records stay byte-identical
    # to the legacy single-pass format).
    if parsed.get("ctrace") is not None:
        res["ctrace"] = parsed["ctrace"]
    if parsed.get("l2") is not None:
        res["l2"] = parsed["l2"]
    return res


# ---------------------------------------------------------------- summary writers

def write_heatmap(cell_results, campaign_id, artifacts_dir):
    """Per-cell CSV: each axis + counts + P_SDC/P_DUE/Reach point + Wilson CI."""
    os.makedirs(artifacts_dir, exist_ok=True)
    csv = os.path.join(artifacts_dir, "heatmap.csv")
    # collect all axis keys across cells for the header
    axis_keys = []
    for cell in cell_results:
        for k in cell["cell"]:
            if k not in axis_keys:
                axis_keys.append(k)
    header = (axis_keys + ["n_total", "n_valid", "n_inactive", "n_simerror",
                           "P_SDC", "P_SDC_lo", "P_SDC_hi",
                           "P_DUE", "P_DUE_lo", "P_DUE_hi",
                           "Reach", "Reach_lo", "Reach_hi", "frozen"])
    with open(csv, "w") as f:
        f.write(",".join(header) + "\n")
        for cell in cell_results:
            st = cell_stats(dict(cell["counter"]))
            row = []
            for k in axis_keys:
                row.append(str(cell["cell"].get(k, "")))
            row += [str(st["n_total"]), str(st["n_valid"]), str(st["n_inactive"]),
                    str(st["n_simerror"]),
                    f"{st['P_SDC']:.4f}", f"{st['P_SDC_ci'][0]:.4f}", f"{st['P_SDC_ci'][1]:.4f}",
                    f"{st['P_DUE']:.4f}", f"{st['P_DUE_ci'][0]:.4f}", f"{st['P_DUE_ci'][1]:.4f}",
                    f"{st['Reachability']:.4f}", f"{st['Reachability_ci'][0]:.4f}", f"{st['Reachability_ci'][1]:.4f}",
                    "1" if cell["frozen"] else "0"]
            f.write(",".join(row) + "\n")
    return csv


def write_summary(cell_results, campaign, artifacts_dir, wall_s, n_reps_done,
                  n_cells, runs_skipped, n_l2_replayed=0):
    """Human-readable summary.md with per-cell table + honesty notes."""
    md = os.path.join(artifacts_dir, "summary.md")
    lines = []
    lines.append(f"# Campaign `{campaign['campaign_id']}` — summary\n")
    lines.append(f"- injector: `{campaign['injector']}`  config: `{campaign.get('config','C0')}`  mode: `{campaign.get('mode','SE')}`")
    lines.append(f"- cells: {n_cells}  reps done: {n_reps_done}  wall: {wall_s:.0f}s")
    wl = campaign["workload"]
    lines.append(f"- workload: `{wl.get('binary')}`  golden_id: `{wl.get('golden_id')}`")
    lines.append(f"- base_seed: {campaign['base_seed']}  (rep seed = base + cell_ordinal*1000 + rep)")
    # W2.3 trace two-pass provenance
    tc = campaign.get("trace") or {}
    if tc.get("enabled"):
        lines.append(f"- trace two-pass (W2.3): ref_run=`{tc.get('ref_run','once')}` "
                     f"replay_for=`{tc.get('replay_for',['SDC','Crash','Hang'])}` "
                     f"replayed reps: {n_l2_replayed} (five-class commit_diff "
                     f"result + latency in each replayed rep's `l2` block in "
                     f"results.jsonl; ref traces at runs/<cid>/ctrace_ref_cNNNN.csv.gz)")
    if runs_skipped:
        lines.append(f"- **skipped reps**: {runs_skipped} (see log)")
    lines.append("")
    lines.append("## Per-cell (Wilson 95% CI)\n")
    lines.append("| cell | n | n_valid | P_SDC [CI] | P_DUE [CI] | Reach [CI] | frozen |")
    lines.append("|---|---|---|---|---|---|---|")
    for cell in cell_results:
        st = cell_stats(dict(cell["counter"]))
        cid = cell_id_str(cell["ordinal"], cell["cell"])
        def fmt(p, ci):
            return f"{p*100:.1f}% [{ci[0]*100:.1f},{ci[1]*100:.1f}]"
        lines.append(
            f"| {cid} | {st['n_total']} | {st['n_valid']} | "
            f"{fmt(st['P_SDC'], st['P_SDC_ci'])} | "
            f"{fmt(st['P_DUE'], st['P_DUE_ci'])} | "
            f"{fmt(st['Reachability'], st['Reachability_ci'])} | "
            f"{'yes' if cell['frozen'] else 'no'} |"
        )
    lines.append("")
    lines.append("## Honesty notes\n")
    if (campaign.get("trace") or {}).get("enabled"):
        lines.append("- Trace replay determinism relies on gem5 same-environment "
                     "reproducibility (W2.1: two no-injection smoke traces are "
                     "field-identical). A replay classification differing from "
                     "pass 1 is recorded as replay_determinism=MISMATCH in the "
                     "rep's l2 block — that mismatch is a finding, not noise to "
                     "be dropped. All campaign children ran with PYTHONHASHSEED=0.")
    lines.append("- This fault machine (cpu179) takes ~92s/run; formal n=384 belongs "
                 "on a healthy 2nd machine (§0.4, §3.1 S6).")
    lines.append("- `SimulatorError` counts are runs where the tool/simulator broke "
                 "(gem5 panic or runner.py mapping error) — NOT valid FI outcomes; "
                 "excluded from N_valid (§1.4).")
    lines.append("- `frozen` cells failed the §1.5 replay-consistency check "
                 "(same manifest gave different classification on re-run).")
    lines.append("- Rates are conditional probabilities under the gem5 O3 + config "
                 "family; NOT product FIT (§4.3).")
    with open(md, "w") as f:
        f.write("\n".join(lines) + "\n")
    return md


# ---------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser(description="ARM64 CHAOS grid campaign driver (§1.5)")
    ap.add_argument("campaign", help="campaign.yaml path")
    ap.add_argument("--jobs", type=int, default=1,
                    help="concurrent rep workers (gem5 ~1 core ~2GB; this machine "
                         "~92s/run — keep small here). Default 1 (pilot on this fault machine).")
    ap.add_argument("--n_per_cell", type=int, default=0,
                    help="override n_per_cell (0 = use campaign.yaml value). Useful for tiny pilot verify.")
    ap.add_argument("--replay_pct", type=float, default=-1,
                    help="override replay_pct (§1.5). -1 = use campaign.yaml (default 5).")
    ap.add_argument("--dry", action="store_true",
                    help="expand grid + write manifests only, do NOT run gem5.")
    ap.add_argument("--keep_manifests", action="store_true", default=True,
                    help="keep per-rep manifests in runs/ (default on, for provenance).")
    args = ap.parse_args()

    with open(args.campaign) as f:
        campaign = yaml.safe_load(f)

    # campaign schema check (best-effort)
    if HAVE_SCHEMA:
        sp = os.path.join(REPO, "schemas", "campaign.schema.json")
        with open(sp) as sf:
            schema = json.load(sf)
        try:
            jsonschema.validate(campaign, schema)
            print(f"[campaign] schema: OK ({sp})")
        except jsonschema.ValidationError as e:
            sys.exit(f"[campaign] schema validation FAILED: {e.message}")
    else:
        print("[campaign] jsonschema not installed — skipping schema check")

    n_per_cell = args.n_per_cell or campaign["n_per_cell"]
    replay_pct = args.replay_pct if args.replay_pct >= 0 else campaign.get("replay_pct", 5.0)
    hang_timeout = campaign.get("hang_timeout", 600)

    # ---- W2.3 trace two-pass (plan Task 3): the campaign yaml's optional
    # `trace:` block. Absent/enabled:false = the legacy single-pass behavior,
    # byte-identical (regression contract). When enabled, after the
    # production pass each cell gets (a) ONE no-injection reference run with
    # --ctrace (the per-cell fault-free baseline, rep-0 manifest + --no-inject)
    # and (b) a replay run with --ctrace + --ctrace-ref for every rep whose
    # pass-1 classification is in replay_for — same manifest, same seed;
    # runner.py calls tools/commit_diff.py and the five-class result is
    # merged into that rep's results.jsonl record under "l2".
    trace_cfg = campaign.get("trace") or {}
    trace_enabled = bool(trace_cfg.get("enabled", False))
    trace_replay_for = list(trace_cfg.get("replay_for", ["SDC", "Crash", "Hang"]))
    trace_ref_mode = str(trace_cfg.get("ref_run", "once"))
    if trace_enabled:
        if campaign.get("config", "C0") != "C3":
            sys.exit("[campaign] trace.enabled requires config: C3 (only "
                     "configs/se/ooo_proxy.py defines --chaos_ctrace/"
                     "--ctrace_file). Aborting.")
        if trace_ref_mode != "once":
            sys.exit(f"[campaign] trace.ref_run='{trace_ref_mode}' not "
                     f"supported (only 'once' = one no-injection ref run per "
                     f"cell). Aborting.")
        bad_cls = [c for c in trace_replay_for if c not in ALL_CLASSES]
        if bad_cls:
            sys.exit(f"[campaign] trace.replay_for {bad_cls} not in known "
                     f"classes {list(ALL_CLASSES)}. Aborting.")
        if args.dry:
            print("[campaign] trace two-pass ENABLED (ref+replay passes are "
                  "RUN passes — skipped under --dry, which only writes "
                  f"manifests): replay_for={trace_replay_for}")
        else:
            print(f"[campaign] trace two-pass ENABLED: ref_run={trace_ref_mode} "
                  f"replay_for={trace_replay_for} "
                  f"(PYTHONHASHSEED=0 pinned for all children)")
    # §2.2 fix: pass the binary path as RELATIVE (not absolute) — gem5's
    # process image layout / readlink emulation behaves differently with
    # absolute paths (rename injection lands at a different PC → different
    # classification). The runner.py + arm_chaos.py use --cmd=<path> directly;
    # a relative path matches the manual-verify behavior (Crash for rename).
    binary = campaign["workload"]["binary"]

    cells = expand_grid(campaign["grid"])
    print(f"[campaign] {len(cells)} cells x {n_per_cell} reps = {len(cells)*n_per_cell} runs")
    print(f"[campaign] jobs={args.jobs}  hang_timeout={hang_timeout}s  replay_pct={replay_pct}")

    runs_dir = os.path.join(REPO, "runs", campaign["campaign_id"])
    artifacts_dir = os.path.join(REPO, "artifacts", campaign["campaign_id"])
    os.makedirs(runs_dir, exist_ok=True)
    os.makedirs(artifacts_dir, exist_ok=True)

    # bad-run log (runner.py stderr when no RESULT line) for provenance.
    bad_log_path = os.path.join(artifacts_dir, "bad_runs.log")

    def log_bad(stderr, stdout, manifest_path):
        with open(bad_log_path, "a") as f:
            f.write(f"=== {manifest_path} ===\n--- stderr ---\n{stderr[-500:]}\n--- stdout ---\n{stdout[-500:]}\n\n")

    cell_results = []
    total_runs = len(cells) * n_per_cell
    runs_done = 0
    t0 = time.time()

    # build the full rep work-list first (so ProcessPoolExecutor can batch),
    # preserving cell ordering for deterministic cell_ordinal.
    # v1.1 Phase 8.2: when the campaign yaml sets workload.uniform_sampling
    # (true), each cell gets ONE countOnly dry-run first; the per-rep
    # manifests then carry sampling.events_to_skip = chaos_pick_skip(seed,
    # N_eligible) — uniform over the ROI's eligible events (design doc §1.7
    # rule 4). Absent/false = legacy geometric(0.1) sampling, unchanged.
    use_uniform = bool(campaign["workload"].get("uniform_sampling", False))
    work = []  # (cell_ordinal, cell, rep, manifest_path, outdir)
    for ord_i, cell in enumerate(cells):
        outdir = os.path.join(runs_dir, f"c{ord_i:04d}")
        n_eligible = None
        if use_uniform:
            n_eligible = count_eligible_events(campaign, cell, ord_i,
                                               outdir, binary, hang_timeout)
            if n_eligible is None:
                print(f"[campaign] cell {ord_i}: countOnly unsupported or "
                      f"dry-run failed — falling back to legacy geometric "
                      f"sampling for this cell")
            elif n_eligible == 0:
                print(f"[campaign] cell {ord_i}: N_eligible=0 (window "
                      f"empty) — every rep will be Inactive; skip=0")
            else:
                print(f"[campaign] cell {ord_i}: N_eligible={n_eligible} "
                      f"(countOnly dry-run)")
        for rep in range(n_per_cell):
            mpath, man = manifest_for_cell(campaign, cell, ord_i, rep, outdir)
            if use_uniform and n_eligible is not None:
                seed = man["rng"]["selection_seed"]
                man["sampling"] = {
                    "events_to_skip": chaos_pick_skip(seed, n_eligible)}
                with open(mpath, "w") as f:
                    yaml.safe_dump(man, f, sort_keys=False,
                                   default_flow_style=False)
            work.append((ord_i, cell, rep, mpath, outdir))

    if args.dry:
        print(f"[campaign] --dry: wrote {len(work)} manifests to {runs_dir}/, not running gem5.")
        return 0

    # run reps (concurrency optional; default 1 = serial, safe on this machine)
    from concurrent.futures import ProcessPoolExecutor, as_completed
    results_by_cell = {i: [] for i in range(len(cells))}
    cell_of = {}  # manifest_path -> cell_ordinal (for result routing)
    rep_of = {}   # manifest_path -> rep index (W2.3 trace replay naming)
    rep0_manifest = {}  # cell_ordinal -> rep-0 manifest path (W2.3 ref run)
    for (ord_i, cell, rep, mpath, outdir) in work:
        cell_of[mpath] = ord_i
        rep_of[mpath] = rep
        if rep == 0:
            rep0_manifest[ord_i] = mpath

    # The pool worker must be picklable: a closure local to main() fails with
    # "Can't pickle local object 'main.<locals>._do_rep'". The module-level
    # _PoolRep class below carries the run context; the item is the plain
    # (ord_i, cell, rep, mpath, outdir) tuple.
    # §3.2 FS pipeline (Phase 5.4): the campaign yaml's `fs:` block carries
    # the runner's FS flags. Recognized keys -> runner CLI flags:
    #   restore_checkpoint -> --restore-checkpoint (REQUIRED for FS campaigns
    #   that don't want a fresh boot per rep; the one-time boot_ckpt dir)
    #   kernel/disk/bootloader/root_partition/fs_cpu -> the same-named runner
    #   flags (defaults live in runner.py).
    fs_cfg = campaign.get("fs", {}) or {}
    fs_extra = []
    if fs_cfg.get("restore_checkpoint"):
        fs_extra += ["--restore-checkpoint", str(fs_cfg["restore_checkpoint"])]
    for key, flag in (("kernel", "--kernel"), ("disk", "--disk"),
                      ("bootloader", "--bootloader"),
                      ("root_partition", "--root-partition"),
                      ("fs_cpu", "--fs-cpu")):
        if fs_cfg.get(key) is not None:
            fs_extra += [flag, str(fs_cfg[key])]
    if fs_extra:
        print(f"[campaign] FS pipeline flags: {fs_extra}")

    _do_rep = _PoolRep(binary, hang_timeout, args.keep_manifests, bad_log_path,
                       fs_extra=fs_extra)

    if args.jobs <= 1:
        for item in work:
            runs_done += 1
            mpath, res = _do_rep(item)
            results_by_cell[cell_of[mpath]].append((mpath, res))
            if runs_done % 5 == 0 or runs_done == total_runs:
                el = time.time() - t0
                print(f"[campaign] {runs_done}/{total_runs} reps done ({el:.0f}s, "
                      f"~{el/runs_done:.0f}s/rep)")
    else:
        with ProcessPoolExecutor(max_workers=args.jobs) as ex:
            futs = {ex.submit(_do_rep, item): item for item in work}
            for fut in as_completed(futs):
                runs_done += 1
                mpath, res = fut.result()
                results_by_cell[cell_of[mpath]].append((mpath, res))
                if runs_done % 5 == 0 or runs_done == total_runs:
                    el = time.time() - t0
                    print(f"[campaign] {runs_done}/{total_runs} reps done ({el:.0f}s)")

    # write per-cell results.jsonl + aggregate counts
    n_l2_replayed = 0  # W2.3: total reps that got a trace replay pass
    for ord_i, cell in enumerate(cells):
        cdir = os.path.join(runs_dir, f"c{ord_i:04d}")

        # ---- W2.3 trace two-pass: (a) ref pass, (b) replay pass ----
        # Runs serially in the driver (NOT in the rep pool): the ref must
        # exist before any replay diff, and each replay re-runs the SAME
        # manifest (same seed) — determinism relies on gem5 same-environment
        # reproducibility (verified W2.1: two no-injection smoke traces are
        # field-identical). A replay classification that DIFFERS from pass 1
        # is recorded honestly in the l2 block (replay_determinism), not
        # hidden — that mismatch is itself a finding.
        if trace_enabled:
            # (a) ref pass: ONE no-injection run per cell (rep-0 manifest +
            # --no-inject), trace named ctrace_ref_cNNNN.csv.gz at the
            # campaign root. Reuse an existing file (idempotent resume) —
            # BUT only when its sidecar records the SAME gem5.opt sha256:
            # a ref traced on an older binary produces garbage verdicts
            # against run traces from the current one (found live 2026-09-24:
            # a parallel W2.4 rebuild swapped gem5.opt mid-campaign).
            ref_path = os.path.join(runs_dir, f"ctrace_ref_c{ord_i:04d}.csv.gz")
            ref_side = ref_path + ".provenance.json"
            reuse_ref = os.path.exists(ref_path)
            if reuse_ref:
                side = None
                if os.path.exists(ref_side):
                    try:
                        with open(ref_side) as f:
                            side = json.load(f)
                    except (OSError, ValueError):
                        side = None
                if side is None:
                    print(f"[campaign] trace ref cell {ord_i}: WARNING — "
                          f"reusing {ref_path} with UNKNOWN binary "
                          f"provenance (no readable sidecar)")
                elif side.get("gem5_sha256") != gem5_sha256():
                    print(f"[campaign] trace ref cell {ord_i}: ref traced "
                          f"with a DIFFERENT gem5.opt (sidecar "
                          f"{str(side.get('gem5_sha256'))[:12]}... != current "
                          f"{gem5_sha256()[:12]}...) — REGENERATING the ref "
                          f"(a stale-binary ref would diff garbage)")
                    reuse_ref = False
                else:
                    print(f"[campaign] trace ref cell {ord_i}: reusing existing "
                          f"{ref_path} (same gem5.opt "
                          f"{gem5_sha256()[:12]}...)")
            if not reuse_ref:
                m0 = rep0_manifest.get(ord_i)
                if m0 is None:
                    print(f"[campaign] trace ref cell {ord_i}: WARNING — no "
                          f"rep-0 manifest; cell has no ref trace, replay "
                          f"diffs will record l2_error")
                else:
                    print(f"[campaign] trace ref pass cell {ord_i}: "
                          f"--no-inject --ctrace -> {ref_path}")
                    rref = run_one_rep(m0, binary, hang_timeout,
                                       args.keep_manifests, log_bad,
                                       extra_args=["--no-inject", "--ctrace",
                                                   ref_path])
                    ref_ct = rref.get("ctrace") or {}
                    # A no-inject run classifies Inactive (faults=0 -> "0
                    # valid injections") or Masked; anything else means the
                    # fault-free baseline itself is broken (golden mismatch,
                    # crash) — the l2 diffs against it would be meaningless.
                    if rref["classification"] not in ("Inactive", "Masked"):
                        print(f"[campaign] trace ref cell {ord_i}: WARNING — "
                              f"no-inject ref classified "
                              f"{rref['classification']} (expected Inactive/"
                              f"Masked; golden/baseline suspect)")
                    if isinstance(ref_ct.get("lines"), int) and ref_ct["lines"] > 0:
                        print(f"[campaign] trace ref cell {ord_i}: ref trace "
                              f"OK ({ref_ct['lines']} committed instructions, "
                              f"{ref_ct.get('bytes')} bytes, classification="
                              f"{rref['classification']})")
                        # provenance sidecar: which gem5.opt traced this ref
                        try:
                            with open(ref_side, "w") as f:
                                json.dump({"gem5_sha256": gem5_sha256(),
                                           "created": time.strftime(
                                               "%Y-%m-%dT%H:%M:%S"),
                                           "lines": ref_ct.get("lines"),
                                           "manifest": os.path.basename(m0)},
                                          f)
                        except OSError:
                            pass  # next reuse falls to the UNKNOWN-provenance warn
                    else:
                        print(f"[campaign] trace ref cell {ord_i}: WARNING — "
                              f"ref trace missing/empty ({ref_ct}); replay "
                              f"diffs will record l2_error")
            # (b) replay pass: every rep classified into replay_for re-runs
            # the SAME manifest with --ctrace (run trace named per (cell,rep)
            # in the cell dir) + --ctrace-ref (runner diffs via commit_diff
            # and prints L2RESULT, which run_one_rep parses into res["l2"]).
            # Binary-consistency guard: if gem5.opt changed since the ref was
            # traced, the diff would be garbage — record an honest l2_error
            # instead of running a meaningless replay.
            ref_sha = None
            if os.path.exists(ref_side):
                try:
                    with open(ref_side) as f:
                        ref_sha = json.load(f).get("gem5_sha256")
                except (OSError, ValueError):
                    pass
            for (mpath, res) in results_by_cell[ord_i]:
                if res.get("classification") not in trace_replay_for:
                    continue
                rep = rep_of[mpath]
                tpath = os.path.join(cdir, f"ctrace_r{rep:04d}.csv.gz")
                if ref_sha is not None and gem5_sha256() != ref_sha:
                    res["l2"] = {"l2_error":
                                 "gem5.opt changed since the ref trace was "
                                 f"recorded (ref {str(ref_sha)[:12]}... vs "
                                 f"current {gem5_sha256()[:12]}...) — replay "
                                 "skipped, a cross-binary diff would be "
                                 "garbage"}
                    with open(bad_log_path, "a") as f:
                        f.write(f"[l2-binary-swap] {mpath}: gem5.opt changed "
                                f"since ref; replay skipped\n")
                    print(f"[campaign] trace replay cell {ord_i} rep {rep}: "
                          f"SKIPPED — gem5.opt changed since the ref was "
                          f"traced")
                    continue
                r2 = run_one_rep(mpath, binary, hang_timeout,
                                 args.keep_manifests, log_bad,
                                 extra_args=["--ctrace", tpath,
                                             "--ctrace-ref", ref_path])
                n_l2_replayed += 1
                det = ("match" if r2["classification"] == res["classification"]
                       else f"MISMATCH({res['classification']}"
                            f"->{r2['classification']})")
                if det != "match":
                    with open(bad_log_path, "a") as f:
                        f.write(f"[l2-replay-mismatch] {mpath}: "
                                f"{res['classification']} -> "
                                f"{r2['classification']}\n")
                res["l2"] = {
                    "replay_triggered_for": res["classification"],
                    "replay_classification": r2["classification"],
                    "replay_determinism": det,
                    "trace_file": tpath,
                    "ref_file": ref_path,
                    "replay_ctrace": r2.get("ctrace"),
                    "commit_diff": r2.get("l2"),
                }
                l2v = (r2.get("l2") or {}).get("verdict", "l2_error")
                print(f"[campaign] trace replay cell {ord_i} rep {rep}: "
                      f"{res['classification']} -> determinism={det} "
                      f"commit_diff.verdict={l2v}")
            n_hit = sum(1 for (_, r) in results_by_cell[ord_i]
                        if r.get("l2") is not None)
            print(f"[campaign] trace two-pass cell {ord_i}: {n_hit}/"
                  f"{len(results_by_cell[ord_i])} reps replayed")

        jpath = os.path.join(cdir, "results.jsonl")
        counter = {c: 0 for c in ALL_CLASSES}
        with open(jpath, "w") as f:
            for (mpath, res) in results_by_cell[ord_i]:
                rec = {"manifest": os.path.basename(mpath),
                       "classification": res["classification"],
                       "faults_injected": res["faults_injected"],
                       "exit": res["exit"], "timed_out": res["timed_out"]}
                # W2.3: trace-run evidence + five-class l2 block; keys added
                # ONLY when present so non-trace campaigns keep the legacy
                # record shape byte-for-byte.
                if res.get("ctrace") is not None:
                    rec["ctrace"] = res["ctrace"]
                if res.get("l2") is not None:
                    rec["l2"] = res["l2"]
                f.write(json.dumps(rec) + "\n")
                if res["classification"] in counter:
                    counter[res["classification"]] += 1
                else:
                    counter["SimulatorError"] += 1  # unknown class -> tool error

        # §1.5 replay-consistency check: re-run max(1, round(replay_pct%)) reps,
        # compare classification. Mismatch -> freeze cell.
        n_replay = max(1, round(replay_pct / 100.0 * n_per_cell))
        frozen = False
        for (mpath, res) in results_by_cell[ord_i][:n_replay]:
            r2 = run_one_rep(mpath, binary, hang_timeout, args.keep_manifests, log_bad)
            if r2["classification"] != res["classification"]:
                frozen = True
                with open(bad_log_path, "a") as f:
                    f.write(f"[replay-mismatch] {mpath}: {res['classification']} -> {r2['classification']}\n")

        cell_results.append({"ordinal": ord_i, "cell": cell, "counter": counter, "frozen": frozen})

    wall = time.time() - t0
    csv = write_heatmap(cell_results, campaign["campaign_id"], artifacts_dir)
    md = write_summary(cell_results, campaign, artifacts_dir, wall, runs_done, len(cells), 0,
                       n_l2_replayed=n_l2_replayed)
    print(f"\n[campaign] DONE — {runs_done} reps in {wall:.0f}s")
    print(f"[campaign] heatmap: {csv}")
    print(f"[campaign] summary: {md}")
    # print the summary to stdout for quick inspection
    print("\n--- summary.md ---")
    with open(md) as f:
        print(f.read())
    return 0


if __name__ == "__main__":
    sys.exit(main())
