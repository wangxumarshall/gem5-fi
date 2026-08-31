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

# Platform config family (design doc §1.1) -> the SE .py harness to run.
# C0 = arm_chaos.py (baseline). C2 = kp920_proxy.py (Kunpeng V110 proxy, E3).
# The campaign driver picks this from the campaign/manifest config_family;
# runner.py defaults to C0 so single-manifest runs are unchanged.
CONFIG_FAMILY = {
    "C0": os.path.join(REPO, "configs/se/arm_chaos.py"),
    "C2": os.path.join(REPO, "configs/se/kp920_proxy.py"),
}

# manifest oracle.golden_id -> the workload's golden (no-injection) checksum.
# These are the no-injection reference outputs (native == gem5, deterministic).
GOLDEN_IDS = {
    "regchain-golden-v1":   "f247ef3fe6f02cfd",  # reg_chain
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
    "branchyreduce-golden-v1": "d47587240e6f0a83",  # branchy_reduce (§2.3)
}

def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1<<16), b""):
            h.update(chunk)
    return h.hexdigest()

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
    ap.add_argument("--binary", required=True, help="path to the workload binary")
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

    # resolve golden checksum: explicit arg, else manifest golden_id
    golden = args.golden_checksum
    if not golden:
        gid = m.get("oracle", {}).get("golden_id")
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

    # fault model -> --fault_type
    model_map = {"transient_bit_flip": "bit_flip",
                 "stuck_at_zero": "stuck_at_zero",
                 "stuck_at_one": "stuck_at_one",
                 "local_mbu": "bit_flip",       # MBU = multi-bit flip (bits_to_change>1)
                 "intermittent_burst": "bit_flip",
                 "legal_domain_sub": "bit_flip",
                 "delay_omission": "bit_flip"}
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

    cmd = [G5, "--quiet", "-d", tempfile.mkdtemp(prefix="man-"), cfg_path,
           "--cmd", args.binary, "--cpu", "O3",
           "--first_clock", str(t["value"]),
           "--max_faults", str(m["limits"]["max_faults"]),
           "--rng_seed", str(m["rng"]["selection_seed"]),
           "--fault_type", fault_type,
           "--fault_mask", fault_mask,
           "--bits_to_change", bits_to_change]
    # target component + layer -> the right injector + index knob
    if comp == "gpr":
        cmd += ["--chaos_reg"]
        if idx is not None:
            # Report #5: manifest target.index MUST take effect. CHAOSReg now
            # has a targetRegIdx directed knob (patch: G1 directed-reg) — force
            # the fault onto the manifest's reg index, not RNG luck.
            cmd += [f"--target_reg_idx={idx}"]
        # max_reg_idx still bounds random sampling when idx is None (random cell)
    elif comp == "physreg":
        cmd += ["--chaos_phys"]
        if layer == "physical":
            cmd += ["--phys_mode", "phys"]
            if idx is not None:
                cmd += [f"--phys_target_idx={idx}"]
        else:  # architectural
            cmd += ["--phys_mode", "arch_frontend"]
            if idx is not None:
                cmd += [f"--phys_target_arch={idx}"]
    elif comp == "memory":
        cmd += ["--chaos_mem"]
    elif comp == "rat":
        # §2.2 CHAOSRenameMap (S1 patch 1). Manifest fault.model maps to the
        # --rename_mode (map_bitflip / f5_substitute / f4_field_stuck). The
        # v2 schema's fault.model enum has legal_domain_sub for F5; map it.
        cmd += ["--chaos_rename"]
        # fault model -> rename_mode
        rm = {"transient_bit_flip": "map_bitflip",
              "local_mbu": "map_bitflip",
              "legal_domain_sub": "f5_substitute",
              "stuck_at_zero": "f4_field_stuck",
              "stuck_at_one": "f4_field_stuck"}.get(inj["model"], "map_bitflip")
        cmd += ["--rename_mode", rm, "--rename_first_clock", str(t["value"]),
                "--rename_max_faults", str(m["limits"]["max_faults"]),
                "--rename_rng_seed", str(m["rng"]["selection_seed"]),
                "--rename_fault_mask", fault_mask, "--rename_target_arch",
                str(idx) if idx is not None else "-1"]
    elif comp == "freelist":
        # §2.2 CHAOSFreeList (S1 patch 2). mark_free / pop_wrong via fault.model.
        cmd += ["--chaos_freelist"]
        fm = {"transient_bit_flip": "mark_free",
              "local_mbu": "mark_free",
              "legal_domain_sub": "pop_wrong"}.get(inj["model"], "mark_free")
        cmd += ["--freelist_mode", fm, "--freelist_first_clock", str(t["value"]),
                "--freelist_max_faults", str(m["limits"]["max_faults"]),
                "--freelist_rng_seed", str(m["rng"]["selection_seed"])]
    elif comp == "rob":
        # §2.3 CHAOSROB (S1 patch 1). entry_bitflip/exc_suppress via fault.model.
        cmd += ["--chaos_rob"]
        rm = {"transient_bit_flip": "entry_bitflip",
              "local_mbu": "entry_bitflip",
              "legal_domain_sub": "exc_suppress"}.get(inj["model"], "entry_bitflip")
        cmd += ["--rob_mode", rm, "--rob_first_clock", str(t["value"]),
                "--rob_max_faults", str(m["limits"]["max_faults"]),
                "--rob_rng_seed", str(m["rng"]["selection_seed"])]
    elif comp == "iq":
        # §2.5 CHAOSIQ (S1 patch 1). wake_omit (F6).
        cmd += ["--chaos_iq", "--iq_mode", "wake_omit",
                "--iq_first_clock", str(t["value"]),
                "--iq_max_faults", str(m["limits"]["max_faults"]),
                "--iq_rng_seed", str(m["rng"]["selection_seed"])]
    elif comp == "lsq_fwd":
        # §2.4 CHAOSLSQFwd structured ext. byte_flip / byte_lane_skew / all_zero.
        cmd += ["--chaos_lsqfwd"]
        sm = {"transient_bit_flip": "byte_flip",
              "local_mbu": "byte_lane_skew",
              "intermittent_burst": "byte_lane_skew",
              "legal_domain_sub": "all_zero"}.get(inj["model"], "byte_flip")
        cmd += ["--lsq_struct_mode", sm, "--first_clock", str(t["value"]),
                "--max_faults", str(m["limits"]["max_faults"]),
                "--rng_seed", str(m["rng"]["selection_seed"]),
                "--fault_type", fault_type, "--fault_mask", fault_mask]
    elif comp == "exec":
        # §2.12 CHAOSExec (integer execution-unit result XOR).
        cmd += ["--chaos_exec", "--exec_first_clock", str(t["value"]),
                "--exec_max_faults", str(m["limits"]["max_faults"]),
                "--exec_fault_mask", fault_mask,
                "--exec_rng_seed", str(m["rng"]["selection_seed"])]
    elif comp == "fsu":
        # §2.6 CHAOSFPU (FP/vector execution-unit result XOR).
        cmd += ["--chaos_fpu", "--fpu_first_clock", str(t["value"]),
                "--fpu_max_faults", str(m["limits"]["max_faults"]),
                "--fpu_fault_mask", fault_mask,
                "--fpu_rng_seed", str(m["rng"]["selection_seed"])]
    elif comp == "l1d_fwd":
        # §2.7 CHAOSL1DForward (post-check escape).
        cmd += ["--chaos_l1dfwd", "--l1dfwd_first_clock", str(t["value"]),
                "--l1dfwd_max_faults", str(m["limits"]["max_faults"]),
                "--l1dfwd_fault_mask", fault_mask,
                "--l1dfwd_rng_seed", str(m["rng"]["selection_seed"])]
    elif comp == "bpu":
        # §2.13 CHAOSBPU (dir_flip / target_flip F5).
        cmd += ["--chaos_bpu"]
        bm = {"transient_bit_flip": "dir_flip",
              "local_mbu": "target_flip",
              "legal_domain_sub": "target_flip"}.get(inj["model"], "dir_flip")
        cmd += ["--bpu_mode", bm, "--bpu_first_clock", str(t["value"]),
                "--bpu_max_faults", str(m["limits"]["max_faults"]),
                "--bpu_rng_seed", str(m["rng"]["selection_seed"])]
    elif comp == "addr_path":
        # §2.4 CHAOSAddrPath (AGU address-path, SE-inert, FS-only).
        cmd += ["--chaos_addrpath", "--addrpath_mode", "byte7_zero",
                "--addrpath_first_clock", str(t["value"]),
                "--addrpath_max_faults", str(m["limits"]["max_faults"]),
                "--addrpath_rng_seed", str(m["rng"]["selection_seed"])]
    elif comp == "ptw":
        # §2.10 CHAOSPTW (page-table-walker, SE-inert, FS-only).
        # Honest: arm_chaos.py (SE) can't mount CHAOSPTW — it's an FS-injector
        # on the ArmTableWalker WalkUnit, not the CPU. Route to FS config.
        sys.exit(f"[runner] target.component='ptw' is FS-only (hooks the ArmTable"
                 f"Walker WalkUnit, not the SE CPU). Use arm_chaos_fs.py with "
                 f"--chaos_ptw (FS mode). Aborting — SE can't mount CHAOSPTW.")
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
    for logname in ("fault_injections.log","main_mem_injections.log","cache_injections.log","rename_injections.log","freelist_injections.log"):
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
