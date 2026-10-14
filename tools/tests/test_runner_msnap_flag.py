#!/usr/bin/env python3
"""[OOO][P1] runner.py --msnap flag test (L0-L5 plan Task 2, 2026-10-12).

Pins three behaviors on the REAL smoke workload (W1.0, 308K insts, C3):
  1. without --msnap the stdout is byte-for-byte the legacy shape: a
     RESULT line and NO MSNAP line (read-only contract, regression-safe);
  2. with --msnap the run produces an MSNAP evidence line + a gzipped
     micro_snap CSV honoring the micro_diff 16-column contract, and the
     classification is IDENTICAL to the no-flag run (the snapshot is
     read-only -- ooo_proxy.py's hard gate);
  3. --msnap on a non-C3/C4-LSU config family is rejected loudly BEFORE
     any gem5 run (mirror of the --ctrace early validation).

Real gem5 runs (two smoke simulations, ~10-20s each). Run:
  python3 tools/tests/test_runner_msnap_flag.py
"""

import os
import gzip
import subprocess
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.realpath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
RUNNER = os.path.join(REPO, "tools", "runner.py")
OUTROOT = "/home/sdc/gem5-fi-ding/runs/ooo-l0l5/selftest/msnap-flag"

FAILURES = []


def check(name, cond, detail=""):
    if cond:
        print(f"  PASS {name}")
    else:
        print(f"  FAIL {name} {detail}")
        FAILURES.append(name)


def smoke_manifest(path, run_id):
    with open(path, "w") as f:
        f.write(f"""schema_version: arm-chaos-fi/v1
campaign_id: l0l5-selftest
run_id: {run_id}
source:
  chaos_commit: selftest
  gem5_commit: 62c7bf284864b83f7308f5e14ca9c80812621c29
  patchset_sha256: selftest
platform:
  isa: ARM64
  mode: SE
  cpu_model: ArmO3CPU
  config_family: C3
workload:
  binary_sha256: ''
  input_sha256: ''
  roi: {{}}
trigger:
  mode: cycle
  value: 1000
target:
  layer: architectural
  component: decode
  instance: cpu0.thread0
  index: -1
  field: imm
  width_bits: 32
  sub_field: imm_bitflip
fault:
  model: transient_bit_flip
  bit_indices: []
  duration_events: 1
  stage: no_protection_model
  protection_model: none
rng:
  master_seed: 20261012
  selection_seed: 20261012
limits:
  max_faults: 1
  max_ticks: 0
oracle:
  kind: exact_hash
  golden_id: smoke-golden-v1
""")


def run_runner(manifest, extra_args, env_extra=None):
    env = dict(os.environ)
    env["PYTHONHASHSEED"] = "0"
    if env_extra:
        env.update(env_extra)
    cmd = [sys.executable, RUNNER, manifest, "--binary",
           os.path.join(REPO, "workloads/ooo/smoke/smoke")] + extra_args
    t0 = time.time()
    r = subprocess.run(cmd, capture_output=True, text=True, errors="replace",
                       timeout=660, env=env)
    return r, time.time() - t0


def parse_result_line(stdout):
    for line in stdout.splitlines():
        if "RESULT:" in line:
            return line.strip()
    return None


def main():
    os.makedirs(OUTROOT, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="msnap-test-") as td:
        # --- run 1: legacy, no flag -------------------------------------
        m1 = os.path.join(td, "m_noflag.yaml")
        smoke_manifest(m1, "l0l5-selftest-noflag")
        r1, w1 = run_runner(m1, [])
        res1 = parse_result_line(r1.stdout)
        print(f"[run1] wall={w1:.1f}s rc={r1.returncode}")
        print(f"[run1] {res1}")
        check("run1-exit0", r1.returncode == 0, r1.stderr[-300:])
        check("run1-has-result", res1 is not None)
        check("run1-no-msnap-line", "MSNAP:" not in r1.stdout)

        # --- run 2: --msnap ---------------------------------------------
        msnap_path = os.path.join(OUTROOT, "msnap_smoke.csv.gz")
        if os.path.exists(msnap_path):
            os.unlink(msnap_path)
        m2 = os.path.join(td, "m_flag.yaml")
        smoke_manifest(m2, "l0l5-selftest-flag")
        r2, w2 = run_runner(m2, ["--msnap", msnap_path])
        res2 = parse_result_line(r2.stdout)
        print(f"[run2] wall={w2:.1f}s rc={r2.returncode}")
        print(f"[run2] {res2}")
        check("run2-exit0", r2.returncode == 0, r2.stderr[-300:])
        check("run2-has-result", res2 is not None)
        check("run2-msnap-line", "MSNAP: file=" in r2.stdout)
        check("run2-msnap-file-exists", os.path.exists(msnap_path))
        cls1 = res1.split("classification=")[1].split()[0] if res1 else "?"
        cls2 = res2.split("classification=")[1].split()[0] if res2 else "?"
        check("read-only-classification-identical", cls1 == cls2,
              f"{cls1} vs {cls2}")
        if os.path.exists(msnap_path):
            def read_msnap_rescued(path, max_head=4):
                """Line-wise read with the truncated-gzip rescue semantics
                of tools/micro_diff.py::load_snaps: a crashed run's msnap
                lacks the gz trailer; complete rows before the EOFError are
                the honest readable prefix."""
                head, rows, ncol, truncated = [], [], None, False
                with gzip.open(path, "rt", errors="replace") as f:
                    try:
                        for line in f:
                            if len(head) < max_head:
                                head.append(line)
                            if line.startswith("#"):
                                continue
                            if ncol is None:
                                ncol = len(line.rstrip("\n").split(","))
                            rows.append(line)
                    except EOFError:
                        truncated = True
                return head, rows, ncol, truncated
            head, rows, ncol, truncated = read_msnap_rescued(msnap_path)
            check("msnap-leading-comment", head and head[0].startswith("#"),
                  repr(head[0][:60] if head else "<empty>"))
            check("msnap-16-columns", ncol == 16 or truncated, f"ncol={ncol}")
            check("msnap-has-rows", len(rows) >= 1 or truncated,
                  f"nrows={len(rows)}")
            # a Crash run's msnap is EXPECTED to be truncated (gem5 aborts
            # before the gz trailer); zero data rows is the honest truth when
            # the crash lands before the first msnap_every interval. The
            # leading '#' comment proves CHAOSMicroSnap attached at all.
            if cls2 == "Crash":
                check("msnap-truncation-expected-honest",
                      truncated is True or len(rows) >= 1,
                      f"truncated={truncated} rows={len(rows)}")
            else:
                check("msnap-complete-on-masked", truncated is False,
                      f"truncated={truncated}")
            print(f"[msnap] rows={len(rows)} cols={ncol} "
                  f"truncated={truncated} (classification={cls2})")

        # --- run 2b: no-inject + msnap -> the COMPLETE happy path --------
        # (the crash run above honestly yields a truncated/empty msnap; a
        # no-inject run runs to completion -> a full 16-column snapshot
        # series -- exactly the shape Task 4's golden generation relies on.)
        msnap_ni = os.path.join(OUTROOT, "msnap_smoke_noinj.csv.gz")
        if os.path.exists(msnap_ni):
            os.unlink(msnap_ni)
        r2b, w2b = run_runner(m2, ["--msnap", msnap_ni, "--no-inject"])
        res2b = parse_result_line(r2b.stdout)
        cls2b = res2b.split("classification=")[1].split()[0] if res2b else "?"
        print(f"[run2b] wall={w2b:.1f}s rc={r2b.returncode} {res2b}")
        check("run2b-exit0", r2b.returncode == 0, r2b.stderr[-300:])
        check("run2b-classification-clean", cls2b in ("Inactive", "Masked"),
              cls2b)
        check("run2b-msnap-file", os.path.exists(msnap_ni))
        if os.path.exists(msnap_ni):
            head, rows, ncol, truncated = read_msnap_rescued(msnap_ni)
            check("run2b-msnap-complete", truncated is False,
                  f"truncated={truncated}")
            check("run2b-msnap-16-columns", ncol == 16, f"ncol={ncol}")
            # smoke = 308057 committed insts -> ~308 snapshots at every=1000
            check("run2b-msnap-rowcount", len(rows) >= 100,
                  f"nrows={len(rows)}")
            print(f"[msnap-noinj] rows={len(rows)} cols={ncol} "
                  f"truncated={truncated}")
        else:
            check("msnap-16-columns", False, "msnap file missing")
            check("msnap-has-rows", False, "msnap file missing")

        # --- run 3: --msnap on C0 must fail loudly before gem5 ----------
        m3 = os.path.join(td, "m_c0.yaml")
        smoke_manifest(m3, "l0l5-selftest-c0")
        with open(m3) as f:
            txt = f.read().replace("config_family: C3", "config_family: C0")
        with open(m3, "w") as f:
            f.write(txt)
        r3, _ = run_runner(m3, ["--msnap", os.path.join(OUTROOT, "bad.csv.gz")])
        check("c0-rejected", r3.returncode != 0
              and "C3/C4-LSU" in (r3.stderr + r3.stdout),
              f"rc={r3.returncode}")

    n = len(FAILURES)
    print(f"\n{'ALL PASS' if n == 0 else 'FAILURES: ' + repr(FAILURES)}")
    sys.exit(1 if n else 0)


if __name__ == "__main__":
    main()
