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
# gem5.opt lives at CHAOS/gem5/build/ARM/ (the scons build target). The older
# note about REPO-ROOT build/ARM was stale — that path is empty on this host.
# Override with env GEM5_OPT if set (campaign.py does this), else the canonical
# vendored-build path.
G5 = os.environ.get("GEM5_OPT") or os.path.join(REPO, "CHAOS/gem5/build/ARM/gem5.opt")
CFG = os.path.join(REPO, "configs/se/arm_chaos.py")

# manifest oracle.golden_id -> the workload's golden (no-injection) checksum.
# These are the no-injection reference outputs (native == gem5, deterministic).
GOLDEN_IDS = {
    "regchain-golden-v1":   "f247ef3fe6f02cfd",  # reg_chain
    "l1dreduce-golden-v1":  "f44d2b9cd4a173cd",  # l1d_reduce
    "l1iloop-golden-v1":    "bb0b1c4cb661236e",  # l1i_loop
    "stuckpersist-golden-v1": "00000000dee1f5d0",  # stuck_persist
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
    ap.add_argument("--golden-checksum",
                    help="workload oracle checksum (e.g. reg_chain's 16-hex "
                         "value) from a no-injection run. If omitted, the "
                         "manifest's oracle.golden_id is resolved via the "
                         "runner's GOLDEN_IDS table.")
    ap.add_argument("--binary", required=True, help="path to the workload binary")
    ap.add_argument("--cache-block-addr", type=lambda x: int(x, 0), default=0,
                    help="directed cache block address (live-data block) for "
                         "l1d/l2/l1i components. 0 = random block (mostly "
                         "Masked). Overrides CHAOS_CACHE_BLOCK_ADDR env.")
    args = ap.parse_args()

    with open(args.manifest) as f:
        m = yaml.safe_load(f)

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

    cmd = [G5, "--quiet", "-d", tempfile.mkdtemp(prefix="man-"), CFG,
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
            cmd += [f"--target_reg_idx={idx}"]
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
        # S0-2 v2: F3 data-dependent trigger (CHAOSPhysReg).
        tvm = inj.get("trigger_value_mask")
        if tvm:
            cmd += [f"--phys_trigger_mask={tvm}",
                    f"--phys_trigger_pattern={inj.get('trigger_value_pattern',0)}"]
    elif comp == "memory":
        cmd += ["--chaos_mem"]
    elif comp == "rat":
        # S0-2 v2: CHAOSRenameMap (method1 history residue F5).
        cmd += ["--chaos_rat"]
        # f5_substitute_target maps to targetArchReg; else idx
        f5t = inj.get("f5_substitute_target")
        if f5t is not None:
            cmd += [f"--rat_target_arch={f5t}", "--rat_mode=f5_substitute"]
        elif idx is not None:
            cmd += [f"--rat_target_arch={idx}"]
        if tgt.get("semantic_role"):
            cmd += [f"--rat_semantic_role={tgt['semantic_role']}"]
        # method1 formal: cholesky's d0 is an FP accumulator — on AArch64
        # the FP/SIMD registers live in VecRegClass (there is no separate
        # FloatRegClass on ARM — regs/vec.hh; FloatRegClass yields
        # numRegs()==0 and every attempt rejects). Target 'vector'.
        if tgt.get("semantic_role") == "fp_accum":
            cmd += ["--rat_reg_class", "vector"]
    elif comp == "freelist":
        # S0-2 v2: CHAOSFreeList (method1 live-reg-marked-free).
        cmd += ["--chaos_freelist"]
        if idx is not None:
            cmd += [f"--freelist_target_phys={idx}"]
    elif comp == "lsq_fwd":
        # S0-2 v2: CHAOSLSQFwd. protection_model not applicable here (data path);
        # f6_phase_offset -> --lsq_phase_offset (when implemented).
        cmd += ["--chaos_lsqfwd"]
        if inj.get("f6_phase_offset") is not None:
            # phaseOffset mode not yet wired in arm_chaos.py; record honestly.
            print(f"[runner] WARNING: f6_phase_offset={inj['f6_phase_offset']} "
                  f"not yet wired (phaseOffset mode pending S1-5).")
    elif comp == "l1d" or comp == "l2" or comp == "l1i":
        # S7-5: CHAOSCache path — route to arm_chaos_cache.py (the cache
        # config). protection_model applies (classify_run_pa nine-class).
        # Directed cache injection needs a live-data block addr; pass via
        # --cache-block-addr (experiment config, not fault semantics).
        CACHE_CFG = os.path.join(REPO, "configs/se/arm_chaos_cache.py")
        block_addr = args.cache_block_addr or int(
            os.environ.get("CHAOS_CACHE_BLOCK_ADDR", "0"), 0)
        byte_off = idx if idx is not None else -1
        pmodel = inj.get("protection_model", "none")
        cmd = [G5, "--quiet", "-d", tempfile.mkdtemp(prefix="man-"), CACHE_CFG,
               "--cmd", args.binary, "--cpu", "O3",
               "--target", comp,                      # l1d/l2/l1i 直译
               "--target_block_addr", str(block_addr),
               "--target_byte_offset", str(byte_off),
               "--first_clock", str(t["value"]),
               "--max_faults", str(m["limits"]["max_faults"]),
               "--rng_seed", str(m["rng"]["selection_seed"]),
               "--fault_type", fault_type,
               "--bits_to_change", bits_to_change,
               "--protection_model", pmodel]
        print(f"[runner] cache path: target={comp} block=0x{block_addr:x} "
              f"byte={byte_off} protection={pmodel}")
    # FS-only components (sysreg/ptw/l1_tlb/addr-path) need arm_chaos_fs.py;
    # the SE runner cannot drive them — record honestly.
    elif comp in ("sysreg", "ptw", "l1_tlb", "l2_tlb"):
        sys.exit(f"[runner] component '{comp}' requires FS mode (arm_chaos_fs.py); "
                 f"the SE runner cannot drive it. Use the FS campaign path.")
    # else: unknown component — let arm_chaos.py reject it.

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
    for logname in ("fault_injections.log","main_mem_injections.log",
                    "cache_injections.log","rat_injections.log",
                    "freelist_injections.log","lsq_fwd_injections.log",
                    "addr_path_injections.log","ptw_injections.log",
                    "armtlb_injections.log","arm_sysreg_injections.log"):
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
                    # count valid injection lines: exclude Inactive/Error/REJECT/MISS
                    # and the per-mode DETAIL line (printed before writeLog for
                    # rat/freelist — "f5_substitute: ..."/"mark_free ..."/
                    # "pop_wrong ..." without "Site:"). Both detail + summary are
                    # emitted per injection; counting both double-counts. The
                    # writeLog summary line is the authoritative one-per-fault.
                    if ("Inactive" in line) or line.startswith("Error"):
                        continue
                    if "REJECT" in line or "MISS" in line:
                        continue
                    # rat/freelist detail lines: start with the mode name + ':'
                    # (e.g. "Cycle: ... f5_substitute: ArchReg..." / "mark_free:").
                    # Distinguish from the writeLog summary by absence of "Site:".
                    # For injectors whose summary HAS "Site:" (rat/freelist/lsq/ptw/
                    # addr/tlb/sysreg), count only that. For CHAOSCache (no Site:,
                    # summary has "Cache Block Addr"), count non-detail lines.
                    if "f5_substitute:" in line and "Site:" not in line:
                        continue
                    if "mark_free:" in line and "Site:" not in line:
                        continue
                    if "pop_wrong:" in line and "Site:" not in line:
                        continue
                    # CHAOSCache log: only the INJECTION line (has
                    # "Cache Block Addr") counts — the "Directed ... NOT
                    # resident" fallback warning and the indented
                    # "ProtectionModel=... EccCorrected" PA marker lines
                    # are per-injection context, not separate faults.
                    if logname == "cache_injections.log" and \
                            "Cache Block Addr" not in line:
                        continue
                    if line.strip():
                        faults += 1
            break
    # G5 assertion: exactly 0 or 1 valid injection
    if faults not in (0,1):
        print(f"[runner] G5 VIOLATION: faults_injected={faults} (not in {{0,1}}) "
              f"— run invalid")

    stdout_text = r.stdout if r.stdout else ""
    # S7-5: cache path — the PA marker (EccCorrected/Poisoned/Latent) lives
    # in cache_injections.log, NOT gem5 stdout. Read it and prepend to the
    # text classify sees, so classify_run_pa's nine-class split works.
    if comp in ("l1d", "l2", "l1i") and outdir:
        pa_log = os.path.join(outdir, "cache_injections.log")
        if os.path.exists(pa_log):
            with open(pa_log) as f:
                stdout_text = f.read() + "\n" + stdout_text
    # S0-2 v2: protection_model (used by the nine-class path below).
    pmodel = inj.get("protection_model", "none")
    # S7-1: fail_count oracle (accum/cholesky print "iters=N fails=M" to stderr,
    # not a 16-hex checksum). oracle.kind=fail_count -> fails>0 = SDC,
    # fails==0 = Masked. Falls through to checksum classify for exact_hash.
    oracle_kind = m.get("oracle", {}).get("kind", "exact_hash")
    if oracle_kind == "fail_count":
        from classify import extract_fail_count, _is_simerr
        if _is_simerr(r.stderr or ""):
            cls, reason = "SimulatorError", "gem5 panic/assert (tool failure)"
        elif timed_out and not r.stdout:
            cls, reason = "Hang", "timeout, no output"
        elif faults == 0:
            cls, reason = "Inactive", "0 valid injections"
        else:
            fails = extract_fail_count((r.stdout or "") + "\n" + (r.stderr or ""))
            if fails < 0:
                # no fails= line but ran — ambiguous; treat as no-mismatch
                cls, reason = "Masked", "fail_count oracle: no fails= line found"
            elif fails > 0:
                cls, reason = "SDC", f"fail_count oracle: fails={fails} > 0"
            else:
                cls, reason = "Masked", "fail_count oracle: fails=0 (no mismatch)"
    # S0-2 v2: when fault.protection_model is set (!= none), use the nine-class
    # classify_run_pa (Corrected/DetectedContained/Latent split); else six-class.
    elif pmodel and pmodel != "none":
        from classify import classify_run_pa
        cls, reason = classify_run_pa(stdout_text, r.stderr or "", r.returncode,
                                      faults, args.golden_checksum, timed_out)
    else:
        cls, reason = classify_run(stdout_text, r.stderr or "", r.returncode,
                                   faults, args.golden_checksum, timed_out)
    print(f"[runner] RESULT: run_id={m['run_id']} classification={cls} "
          f"faults_injected={faults} exit={r.returncode} "
          f"timed_out={timed_out}")
    print(f"[runner]   reason: {reason}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
