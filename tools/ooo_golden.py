#!/usr/bin/env python3
"""ooo_golden.py -- one-shot cached no-fault golden per baseline_key
(plan Task 4; task-book §二.4: 每个 baseline_key 只生成一次 no-fault golden
并缓存).

A "golden" is the full no-injection reference for ONE (gem5 binary, config,
workload, benign argv, msnap period) tuple: the L2 commit trace
(ctrace_ref.csv.gz), the L1 µarch snapshot series (micro_snap_ref.csv.gz),
the fault-free FINAL checksum, and provenance. Sample runs diff against THIS
cached object; it is generated exactly once per baseline_key under a global
golden claim lock and then only ever READ.

Honesty contract:
  * the observed FINAL checksum is CROSS-CHECKED against runner.py's
    GOLDEN_IDS registry entry for the spec's golden_id — a mismatch is a
    loud, blocking error (registered golden vs measured golden conflict),
    never silently accepted;
  * the golden sidecar records the gem5.opt sha256 that traced it; a cache
    hit under a DIFFERENT binary is refused (regeneration required) —
    cross-binary diffs are garbage (the W2.4 live-found lesson);
  * cache verification re-hashes the heavy files only when their
    (size, mtime_ns) drifts from provenance (campaign.py's stat-cache
    pattern); per-call cost is a few stat()s.

Layout: <runs_root>/ooo-l0l5/goldens/<key>/
  ctrace_ref.csv.gz  micro_snap_ref.csv.gz  stats_ref.txt
  manifest.yaml  runner.stdout  runner.stderr
  provenance.json  COMPLETE.json
Staging builds in <key>.staging/ (a SIBLING of the final dir) and
os.rename()s into place; COMPLETE.json is written INSIDE staging right
before the rename so a half-built golden can never be mistaken for a
complete one.
"""

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.realpath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import ooo_guard  # noqa: E402
import campaign as campaign_mod  # noqa: E402  (one manifest builder, no drift)

try:
    import yaml
except ImportError:
    sys.exit("ERROR: pip install pyyaml (needed for golden spec parsing)")

DEFAULT_RUNS_ROOT = "/home/sdc/gem5-fi-ding/runs"
DEFAULT_GUARD_DIR = "/home/sdc/gem5-fi-ding/runs/ooo-l0l5/guard"

SPEC_FIELDS = ("gem5_sha256", "config_family", "config_sha256",
               "workload_relpath", "workload_sha256", "trigger_mode",
               "trigger_value", "max_faults", "fault_type", "rng_seed",
               "maxinsts", "msnap_every", "golden_id")


class GoldenError(Exception):
    """Blocking golden failure (registry conflict, identity drift, ...)."""


# ---------------------------------------------------------------- spec/key

def baseline_key(spec):
    """Stable 24-hex identity of a golden baseline: sha256 over the
    canonical (sorted-keys, no-whitespace) JSON of the spec dict."""
    canon = json.dumps({k: spec[k] for k in SPEC_FIELDS}, sort_keys=True,
                       separators=(",", ":"))
    return hashlib.sha256(canon.encode()).hexdigest()[:24]


def write_spec_yaml(spec, path):
    with open(path, "w") as f:
        yaml.safe_dump({k: spec[k] for k in SPEC_FIELDS}, f,
                       sort_keys=True, default_flow_style=False)


def load_spec_yaml(path):
    with open(path) as f:
        d = yaml.safe_load(f)
    missing = [k for k in SPEC_FIELDS if k not in d]
    if missing:
        raise GoldenError(f"golden spec {path} missing fields {missing}")
    return {k: d[k] for k in SPEC_FIELDS}


def spec_from_campaign(camp_yaml_path, gem5_sha256, config_sha256,
                       workload_sha256):
    """Derive the golden spec from an L0-L5 campaign yaml (the sample-side
    identity), so a campaign and its golden can never drift apart."""
    with open(camp_yaml_path) as f:
        c = yaml.safe_load(f)
    wl = c["workload"]
    return {
        "gem5_sha256": gem5_sha256,
        "config_family": c.get("config", "C3"),
        "config_sha256": config_sha256,
        "workload_relpath": wl["binary"],
        "workload_sha256": workload_sha256,
        "trigger_mode": wl.get("trigger_mode", "cycle"),
        "trigger_value": wl.get("trigger_value", 1000),
        "max_faults": c.get("limits", {}).get("max_faults", 1),
        "fault_type": "bit_flip",
        "rng_seed": 0,  # fixed: the no-inject reference seed is part of
        #                the baseline definition, independent of sample seeds
        "maxinsts": 0,
        "msnap_every": (c.get("trace") or {}).get("msnap_every", 1000),
        "golden_id": wl["golden_id"],
    }


# ------------------------------------------------------------------ hashes

def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _stat_sig(path):
    st = os.stat(path)
    return [st.st_size, st.st_mtime_ns]


# ------------------------------------------------------------ golden build

def _golden_manifest(spec, outdir, key):
    """Build the no-inject reference manifest via campaign.manifest_for_cell
    (ONE manifest builder — the runner arg mapping stays single-sourced).
    The fault block mirrors a real sample of this campaign so the only
    difference between golden run and sample run is --no-inject."""
    injector = _injector_for(spec)
    cell = {"fault_model": "transient_bit_flip", "protection_model": "none"}
    if injector == "decode":
        cell.update({"field": "imm", "width_bits": 32,
                     "sub_field": "imm_bitflip"})
    camp = {
        "campaign_id": f"golden_{key}",
        "injector": injector,
        "config": spec["config_family"],
        "mode": "SE",
        "chaos_commit": "golden",
        "base_seed": 0,
        "workload": {
            "binary": spec["workload_relpath"],
            "golden_id": spec["golden_id"],
            "trigger_mode": spec["trigger_mode"],
            "trigger_value": spec["trigger_value"],
            "binary_sha256": spec["workload_sha256"],
        },
        "limits": {"max_faults": spec["max_faults"]},
    }
    mpath, man = campaign_mod.manifest_for_cell(camp, cell, 0, 0, outdir)
    return mpath, man


def _injector_for(spec):
    """The golden spec carries the workload, not the injector (a golden is
    shared by every campaign on the same baseline). The manifest still
    needs a syntactically valid fault block; decode is the neutral choice
    for C3 SE and the fault block is INERT under --no-inject (validated but
    never mapped to a --chaos_* flag)."""
    return "decode"


def _run_reference(spec, key, staging, hang_timeout):
    """Run the no-inject reference with L1+L2 observers attached."""
    runner = os.path.join(HERE, "runner.py")
    mpath, man = _golden_manifest(spec, os.path.join(staging, "manifests"),
                                  key)
    ctrace = os.path.join(staging, "ctrace_ref.csv.gz")
    msnap = os.path.join(staging, "micro_snap_ref.csv.gz")
    cmd = [sys.executable, runner, mpath,
           "--binary", os.path.join(REPO, spec["workload_relpath"]),
           "--no-inject",
           "--ctrace", ctrace,
           "--msnap", msnap,
           "--msnap-every", str(spec["msnap_every"]),
           "--stats",
           "--echo-checksum"]  # observed FINAL surfaces as [runner] CHECKSUM
    env = dict(os.environ)
    env["PYTHONHASHSEED"] = "0"  # forced, not setdefault (task-book §二.4)
    env["TMPDIR"] = os.path.join(staging, "tmp")
    os.makedirs(env["TMPDIR"], exist_ok=True)
    t0 = time.time()
    try:
        r = subprocess.run(cmd, capture_output=True, text=True,
                           errors="replace",
                           timeout=hang_timeout + 30, env=env)
    except subprocess.TimeoutExpired as e:
        raise GoldenError(
            f"golden reference run exceeded {hang_timeout + 30}s "
            f"(key={key}); partial stdout tail: "
            f"{(e.stdout or b'')[-300:]!r}")
    wall = time.time() - t0
    return {"rc": r.returncode, "stdout": r.stdout, "stderr": r.stderr,
            "wall_s": wall, "manifest_path": mpath, "manifest": man,
            "ctrace_path": ctrace, "msnap_path": msnap}


def _find_man_dir(staging):
    """The runner's -d man-* tempdir (under TMPDIR=<staging>/tmp)."""
    tmpd = os.path.join(staging, "tmp")
    if not os.path.isdir(tmpd):
        return None
    for name in os.listdir(tmpd):
        if name.startswith("man-"):
            return os.path.join(tmpd, name)
    return None


def build_golden(spec, runs_root, guard_dir, hang_timeout=650,
                 force=False, verify2=False):
    """Generate-or-verify the cached golden for spec. Returns the handle
    dict. Raises GoldenError on any blocking failure (registry conflict,
    identity drift, unreadable evidence)."""
    key = baseline_key(spec)
    gdir = os.path.join(runs_root, "ooo-l0l5", "goldens", key)
    final_dir = gdir + ".verify2" if verify2 else gdir
    complete = os.path.join(final_dir, "COMPLETE.json")
    if not force and not verify2 and os.path.exists(complete):
        return _verify_cached(spec, key, final_dir)

    os.makedirs(os.path.dirname(gdir), exist_ok=True)
    # generation claim: exactly one builder per key, host-wide
    deadline = time.time() + 1800
    while not ooo_guard.golden_claim_acquire(guard_dir, key):
        # someone else is building: wait for their COMPLETE (or reclaim a
        # provably-dead builder's claim)
        if os.path.exists(complete):
            return _verify_cached(spec, key, final_dir)
        cpath = os.path.join(guard_dir, "goldens", f"{key}.claim")
        try:
            with open(cpath) as f:
                cj = json.load(f)
            if not ooo_guard.pid_matches(cj.get("pid"), cj.get("starttime")):
                ooo_guard.golden_claim_release(guard_dir, key)
                continue
        except (OSError, ValueError):
            pass
        if time.time() > deadline:
            raise GoldenError(f"golden {key}: builder claim held >30min "
                              f"without COMPLETE")
        time.sleep(5)

    try:
        # staging is a SIBLING of the final dir, not a child: publishing is
        # a same-parent os.rename(staging, final_dir) which cannot hit the
        # "target is the source's own non-empty parent" wall. (Found by the
        # first real golden build 2026-10-12: with staging at gdir/.staging
        # the primary publish os.rename(gdir/.staging, gdir) is impossible —
        # gdir exists and is non-empty — and the force-branch rmtree(gdir)
        # deleted the fresh staging right before the rename.)
        staging = gdir + ".staging"
        if os.path.isdir(staging):
            shutil.rmtree(staging)  # never resumes a half-build
        legacy = os.path.join(gdir, ".staging")
        if os.path.isdir(legacy):  # old-layout half-build remnant
            shutil.rmtree(legacy)
        os.makedirs(staging)
        res = _run_reference(spec, key, staging, hang_timeout)

        with open(os.path.join(staging, "runner.stdout"), "w") as f:
            f.write(res["stdout"])
        with open(os.path.join(staging, "runner.stderr"), "w") as f:
            f.write(res["stderr"])

        # --- validation (all blocking, none silently waived) -------------
        if res["rc"] != 0:
            raise GoldenError(f"golden {key}: runner rc={res['rc']}; "
                              f"stderr tail: {res['stderr'][-400:]}")
        # the observed FINAL checksum arrives via runner.py's opt-in
        # --echo-checksum evidence line (runner captures gem5's stdout
        # internally and never forwards the raw FINAL= line - found by the
        # first real golden build 2026-10-12)
        m = re.search(r"^\[runner\] CHECKSUM: ([0-9a-f]{16}|none)$",
                      res["stdout"], re.M)
        observed = m.group(1) if m else ""
        if not observed:
            raise GoldenError(
                f"golden {key}: no observed FINAL checksum in runner output "
                f"(--echo-checksum line missing or 'none') - cannot "
                f"cross-check against the registry")
        # registry cross-check (task-book: golden 不一致 = 立即停止)
        from runner import GOLDEN_IDS
        registered = GOLDEN_IDS.get(spec["golden_id"])
        if registered is None:
            raise GoldenError(f"golden {key}: golden_id "
                              f"{spec['golden_id']} not in runner.GOLDEN_IDS "
                              f"— refusing to create an unregistered golden")
        if observed != registered:
            raise GoldenError(
                f"golden {key}: measured FINAL {observed!r} != registered "
                f"{registered!r} for {spec['golden_id']} — registry/measured "
                f"conflict is a BLOCKING event")
        for line in res["stdout"].splitlines():
            if "RESULT:" in line:
                cls = line.split("classification=")[1].split()[0]
                if cls not in ("Inactive", "Masked"):
                    raise GoldenError(f"golden {key}: no-inject reference "
                                      f"classified {cls} (expected Inactive/"
                                      f"Masked — fault-free baseline broken)")
                break
        for p in (res["ctrace_path"], res["msnap_path"]):
            if not os.path.exists(p) or os.path.getsize(p) == 0:
                raise GoldenError(f"golden {key}: missing/empty evidence "
                                  f"{p}")
        # quick line-count sanity (count via the runner's helper)
        from runner import count_trace_lines
        for p in (res["ctrace_path"], res["msnap_path"]):
            n = count_trace_lines(p)
            if not n or n <= 0:
                raise GoldenError(f"golden {key}: {os.path.basename(p)} "
                                  f"unreadable (lines={n})")

        # --- provenance + COMPLETE, all inside staging -------------------
        md = _find_man_dir(staging)
        if md:
            for fname in ("stats.txt",):
                src = os.path.join(md, fname)
                if os.path.exists(src):
                    shutil.copy2(src, os.path.join(staging, "stats_ref.txt"))
        prov = {
            "key": key,
            "spec": {k: spec[k] for k in SPEC_FIELDS},
            "gem5_sha256": spec["gem5_sha256"],
            "final_checksum": observed,
            "golden_id_registered": registered,
            "created": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "wall_s": round(res["wall_s"], 1),
            "run_id": res["manifest"]["run_id"],
            "files": {
                "ctrace_ref.csv.gz": {
                    "sha256": sha256_file(res["ctrace_path"]),
                    **dict(zip(("size", "mtime_ns"),
                               _stat_sig(res["ctrace_path"])))},
                "micro_snap_ref.csv.gz": {
                    "sha256": sha256_file(res["msnap_path"]),
                    **dict(zip(("size", "mtime_ns"),
                               _stat_sig(res["msnap_path"])))},
            },
        }
        with open(os.path.join(staging, "provenance.json"), "w") as f:
            json.dump(prov, f, indent=2, ensure_ascii=False)
            f.write("\n")
        with open(os.path.join(staging, "COMPLETE.json"), "w") as f:
            json.dump({"key": key, "final": observed,
                       "gem5_sha256": spec["gem5_sha256"],
                       "completed": prov["created"]},
                      f, indent=2)
            f.write("\n")
        # cleanup the man-* tempdir (evidence already extracted); the
        # manifests dir keeps the exact manifest used
        if md:
            shutil.rmtree(md, ignore_errors=True)

        # --- atomic publish ------------------------------------------------
        # final_dir may hold an old COMPLETE copy (force/verify2) or a
        # failed attempt's leftovers (primary path: gdir without
        # COMPLETE.json) — both are safe to replace. The fresh staging is a
        # SIBLING of final_dir, so this rmtree can never delete it.
        if os.path.isdir(final_dir):
            shutil.rmtree(final_dir)  # old copy (force/verify2) or leftovers
        os.rename(staging, final_dir)
        print(f"[golden] {key}: BUILT final={observed} wall={res['wall_s']:.0f}s")
        return _handle(key, final_dir, observed, prov)
    finally:
        ooo_guard.golden_claim_release(guard_dir, key)


def _handle(key, final_dir, observed, prov):
    return {
        "key": key,
        "dir": final_dir,
        "ctrace_path": os.path.join(final_dir, "ctrace_ref.csv.gz"),
        "msnap_path": os.path.join(final_dir, "micro_snap_ref.csv.gz"),
        "final_checksum": observed,
        "provenance": prov,
    }


def _verify_cached(spec, key, final_dir):
    """Read-only verification of an existing COMPLETE golden: identity match,
    FINAL match, evidence present; re-hash heavy files only on stat drift."""
    complete = os.path.join(final_dir, "COMPLETE.json")
    prov_p = os.path.join(final_dir, "provenance.json")
    try:
        with open(complete) as f:
            comp = json.load(f)
        with open(prov_p) as f:
            prov = json.load(f)
    except (OSError, ValueError) as e:
        raise GoldenError(f"golden {key}: unreadable COMPLETE/provenance: {e}")
    if comp.get("gem5_sha256") != spec["gem5_sha256"]:
        raise GoldenError(
            f"golden {key}: cached under gem5 "
            f"{str(comp.get('gem5_sha256'))[:12]}... but current spec says "
            f"{spec['gem5_sha256'][:12]}... — cross-binary reuse refused, "
            f"regenerate (force)")
    if prov.get("final_checksum") != comp.get("final"):
        raise GoldenError(f"golden {key}: provenance/COMPLETE checksum "
                          f"mismatch ({prov.get('final_checksum')} vs "
                          f"{comp.get('final')})")
    for fname, meta in prov.get("files", {}).items():
        p = os.path.join(final_dir, fname)
        if not os.path.exists(p):
            raise GoldenError(f"golden {key}: evidence file missing: {p}")
        sig = _stat_sig(p)
        if [meta["size"], meta["mtime_ns"]] != sig:
            # drifted on disk: full re-hash before trusting the cache
            if sha256_file(p) != meta["sha256"]:
                raise GoldenError(f"golden {key}: {fname} content drifted "
                                  f"from provenance sha256 — cache invalid")
    return _handle(key, final_dir, prov["final_checksum"], prov)


def ensure_golden(spec, runs_root=DEFAULT_RUNS_ROOT,
                  guard_dir=DEFAULT_GUARD_DIR, hang_timeout=650):
    """Idempotent entry point used by the sample runner (task-book §二.4:
    generate once, then only read)."""
    return build_golden(spec, runs_root, guard_dir,
                        hang_timeout=hang_timeout)


# -------------------------------------------------------------------- cli

def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("ensure", help="(literal) ensure subcommand")
    ap.add_argument("--spec", required=True, help="golden spec yaml path")
    ap.add_argument("--runs-root", default=DEFAULT_RUNS_ROOT)
    ap.add_argument("--guard-dir", default=DEFAULT_GUARD_DIR)
    ap.add_argument("--hang-timeout", type=int, default=650)
    ap.add_argument("--force", action="store_true",
                    help="regenerate even if COMPLETE exists (evidence dir "
                         "is replaced; the old one is deleted)")
    ap.add_argument("--verify2", action="store_true",
                    help="build a SECOND copy at <key>.verify2 for the "
                         "determinism double-run check, then compare")
    args = ap.parse_args()
    if args.ensure != "ensure":
        ap.error("only the 'ensure' subcommand exists")

    spec = load_spec_yaml(args.spec)
    h = build_golden(spec, args.runs_root, args.guard_dir,
                     hang_timeout=args.hang_timeout, force=args.force,
                     verify2=args.verify2)
    print(json.dumps({"key": h["key"], "dir": h["dir"],
                      "final": h["final_checksum"]}, indent=2))
    if args.verify2:
        # compare the two independent builds bit-for-bit
        a = os.path.join(args.runs_root, "ooo-l0l5", "goldens", h["key"])
        b = h["dir"]  # the .verify2 copy
        same = all(sha256_file(os.path.join(d, f))
                   == sha256_file(os.path.join(b, f))
                   for d in [a] for f in ("ctrace_ref.csv.gz",
                                          "micro_snap_ref.csv.gz"))
        print(f"[golden] determinism double-run: "
              f"{'IDENTICAL' if same else 'MISMATCH (BLOCKING)'}")
        return 0 if same else 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
