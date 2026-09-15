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

    # platform.config_params (optional dict): microarch knob overrides passed
    # through to the config script (Phase 3 H2 window sweep — ROB/PhysInt
    # sizing). Whitelist-checked: only keys the target config's argparse
    # actually defines, so a typo fails loudly at the runner, not silently
    # inside gem5 (the lsqfwd argparse lesson, 79f32b1).
    cfg_params = m.get("platform", {}).get("config_params") or {}
    if cfg_params:
        supported = {"rob", "phys_int", "phys_float", "lq", "sq"}  # kp920_proxy.py knobs
        unsupported = set(cfg_params) - supported
        if unsupported:
            sys.exit(f"[runner] platform.config_params keys {sorted(unsupported)} "
                     f"not in supported set {sorted(supported)} for family "
                     f"{cfg_family}. Aborting.")
        if cfg_family != "C2":
            sys.exit(f"[runner] platform.config_params is C2-only (kp920_proxy "
                     f"microarch knobs); config_family={cfg_family}. Aborting.")

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
    if cfg_family not in ("C0-CACHE", "C0-FS", "C2-FS"):
        cmd += ["--fault_mask", fault_mask, "--bits_to_change", bits_to_change]
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
        # fault model -> rename_mode
        # intermittent_burst -> spec_leak (§2.3 Phase 4.1, method1 speculative
        # leak): one squash-rollback suppression — the wrong-path µop's dest
        # stays mapped, its value leaks into the correct path.
        rm = {"transient_bit_flip": "map_bitflip",
              "local_mbu": "map_bitflip",
              "intermittent_burst": "spec_leak",
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
        # §2.5 CHAOSIQ. wake_omit (F6, default) / src_ready_bitflip (F5,
        # wrong-source wakeup — legal_domain_sub) / wake_phase (F6 phase
        # delay — intermittent_burst; bit_indices[0] = offset in cycles).
        cmd += ["--chaos_iq"]
        im = {"legal_domain_sub": "src_ready_bitflip",
              "intermittent_burst": "wake_phase"}.get(inj["model"], "wake_omit")
        cmd += ["--iq_mode", im]
        if im == "wake_phase":
            offset = bits[0] if bits else 1
            cmd += ["--iq_phase_offset", str(offset)]
        cmd += ["--iq_first_clock", str(t["value"]),
                "--iq_max_faults", str(m["limits"]["max_faults"]),
                "--iq_rng_seed", str(m["rng"]["selection_seed"])]
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
        cmd += ["--chaos_decode", "--decode_first_clock", str(t["value"]),
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
    return 0

if __name__ == "__main__":
    sys.exit(main())
