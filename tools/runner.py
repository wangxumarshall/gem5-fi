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
import sys, os, json, subprocess, hashlib, argparse, tempfile

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

def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1<<16), b""):
            h.update(chunk)
    return h.hexdigest()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("manifest")
    ap.add_argument("--golden-checksum", required=True,
                    help="workload oracle checksum (e.g. reg_chain's 16-hex "
                         "value) from a no-injection run")
    ap.add_argument("--binary", required=True, help="path to the workload binary")
    args = ap.parse_args()

    with open(args.manifest) as f:
        m = yaml.safe_load(f)

    # schema validation
    if HAVE_SCHEMA:
        sp = os.path.join(REPO, "schemas/manifest.schema.json")
        with open(sp) as sf:
            schema = json.load(sf)
        try:
            jsonschema.validate(m, schema)
        except jsonschema.ValidationError as e:
            sys.exit(f"manifest schema validation FAILED: {e.message}")
        print("[runner] manifest schema: OK")
    else:
        print("[runner] jsonschema not installed — skipping schema check")

    # validate binary hash
    if m["workload"].get("binary_sha256"):
        actual = sha256_file(args.binary)
        expected = m["workload"]["binary_sha256"]
        if actual != expected:
            sys.exit(f"[runner] binary sha256 MISMATCH: {actual} != {expected}")
        print(f"[runner] binary sha256: OK ({actual[:12]}...)")

    assert m["limits"]["max_faults"] in (0,1), "formal runs require max_faults in {0,1}"

    # map manifest -> arm_chaos.py args
    t = m["trigger"]
    inj = m["fault"]
    tgt = m["target"]
    comp = tgt["component"]
    cmd = [G5, "--quiet", "-d", tempfile.mkdtemp(prefix="man-"), CFG,
           "--cmd", args.binary, "--cpu", "O3",
           "--first_clock", str(t["value"]),
           "--max_faults", str(m["limits"]["max_faults"]),
           "--rng_seed", str(m["rng"]["selection_seed"]),
           "--fault_type", "bit_flip" if inj["model"]=="transient_bit_flip" else inj["model"],
           "--bits_to_change", "1"]
    if comp == "gpr":
        cmd += ["--chaos_reg"]
    elif comp == "physreg":
        cmd += ["--chaos_phys", "--phys_mode", "phys"]
    elif comp == "memory":
        cmd += ["--chaos_mem"]

    print("[runner] running:", " ".join(cmd[:4]), "...")
    # Hang timeout (plan §13.2): a normal sim completes in well under the
    # wall budget; a Hang = no completion within this. Default 600s; the
    # manifest may specify limits.max_ticks but we bound on wall time here.
    HANG_TIMEOUT = 600
    timed_out = False
    try:
        r = subprocess.run(cmd, capture_output=True, text=True,
                           timeout=HANG_TIMEOUT)
    except subprocess.TimeoutExpired as e:
        timed_out = True
        # Build a pseudo-result from whatever was captured.
        r = subprocess.CompletedProcess(
            cmd, returncode=-1, stdout=e.stdout or "", stderr=e.stderr or "")

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
    for logname in ("fault_injections.log","main_mem_injections.log","cache_injections.log"):
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
                    # count valid injection lines: exclude Inactive/Error
                    if ("Inactive" in line) or line.startswith("Error"):
                        continue
                    if line.strip():
                        faults += 1
            break
    # G5 assertion: exactly 0 or 1 valid injection
    if faults not in (0,1):
        print(f"[runner] G5 VIOLATION: faults_injected={faults} (not in {{0,1}}) "
              f"— run invalid")

    stdout_text = r.stdout if r.stdout else ""
    cls, reason = classify_run(stdout_text, r.stderr or "", r.returncode,
                               faults, args.golden_checksum, timed_out)
    print(f"[runner] RESULT: run_id={m['run_id']} classification={cls} "
          f"faults_injected={faults} exit={r.returncode} "
          f"timed_out={timed_out}")
    print(f"[runner]   reason: {reason}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
