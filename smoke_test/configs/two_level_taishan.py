# TaiShan v110 (Kunpeng 920) O3 / SE smoke-test configuration.
#
# Old-style configs layout. CHAOS is mounted as:
#       system.CHAOSReg = CHAOSReg(cpu=system.cpu, ...)
# which is exactly the form CHAOS's own examples use.
#
# Usage:
#   baseline (golden reference, no injection):
#       ./build/ARM/gem5.opt -d <outdir> configs/two_level_taishan.py \
#           --binary <test_workload> --mode baseline
#   fault injection (CHAOSReg):
#       ./build/ARM/gem5.opt -d <outdir> configs/two_level_taishan.py \
#           --binary <test_workload> --mode inject
#
# The ONLY variable that differs between baseline and inject is the CHAOSReg
# SimObject, so any output divergence is attributable to the injection.

import argparse
import os
import sys

import m5
from m5.objects import *

# Make this configs dir importable for the local cache / fu_pool modules.
sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
from caches import L1ICache, L1DCache, L2Cache
from fu_pool import TaiShanFUPool


# ---------------------------------------------------------------------------
# TaiShan v110 execution resources as a single IQUnit's FUPool.
# ---------------------------------------------------------------------------
def make_taishan_iq(num_entries=64):
    # v25 models the issue queue as a vector of IQUnit objects, each with its
    # own entry count and FUPool. We use one IQUnit sized to numIQEntries.
    from m5.objects.IQUnit import IQUnit
    return IQUnit(numEntries=num_entries, fuPool=TaiShanFUPool())


def build_cpu():
    cpu = ArmO3CPU()

    # --- Pipeline widths: all 4 (fetch/decode/rename/dispatch/issue/wb/commit)
    cpu.fetchWidth = 4
    cpu.decodeWidth = 4
    cpu.renameWidth = 4
    cpu.dispatchWidth = 4
    cpu.issueWidth = 4
    cpu.wbWidth = 4
    cpu.commitWidth = 4

    # --- Reorder buffer / physical register file
    # TaiShan v110: ROB 97. Phys int regs = 93推测 + 32已退休 = 125.
    cpu.numROBEntries = 97
    cpu.numPhysIntRegs = 125
    cpu.numPhysFloatRegs = 96    # 64 + 32
    cpu.numPhysVecRegs = 96      # NEON 128-bit, 96 phys vector regs

    # --- Load / Store queues
    # !!! LQ/SQ 疑点（务必保留此注释，后续微基准复核）!!!
    # LQEntries=65, SQEntries=47 -> 合计 112, 大于 ROB 容量 97。
    # 在飞指令(in-flight)数量物理上不应超过 ROB 容量，因此该值存在疑问：
    #   - 可能 LQ/SQ 表项包含了 ROB 退休后仍在排空(store buffer drain)的项；
    #   - 也可能是微基准测量时把退休后的表项一并计入了；
    #   - 或厂商文档对 LQ/SQ 的口径与 gem5 的 LQ/SQEntries 定义不同。
    # 先照规格配置，后续会用专门的 load/store 微基准复核真实在飞容量，
    # 届时若发现配置导致的 in-flight > ROB 异常再校正。
    cpu.LQEntries = 65
    cpu.SQEntries = 47

    # --- Issue queue (v25: vector of IQUnit, numEntries per unit)
    # numIQEntries=64 是未实测值，先用此，后续标定。
    cpu.instQueues = [make_taishan_iq(num_entries=64)]

    # FUPool is set per-IQUnit above (TaiShan layout: 3 IntALU + 1 mul/div,
    # 2 FP/SIMD ports with FP32 FMA latency 5, 2 MemRead + 2 MemWrite AGU).

    # SVE is NOT enabled: ArmO3CPU uses the NEON-based SIMD_Unit only; our
    # workload emits no SVE instructions, so no SVE unit is needed.
    return cpu


def build_system(binary):
    system = System()
    system.clk_domain = SrcClockDomain()
    system.clk_domain.clock = "2.6GHz"   # TaiShan v110 nominal 2.6 GHz
    system.clk_domain.voltage_domain = VoltageDomain()

    system.mem_mode = "timing"
    system.mem_ranges = [AddrRange("512MiB")]

    system.cpu = build_cpu()

    system.cpu.icache = L1ICache()
    system.cpu.dcache = L1DCache()
    system.cpu.icache.connectCPU(system.cpu)
    system.cpu.dcache.connectCPU(system.cpu)

    system.l2bus = L2XBar()
    system.cpu.icache.connectBus(system.l2bus)
    system.cpu.dcache.connectBus(system.l2bus)

    system.l2cache = L2Cache()
    system.l2cache.connectCPUSideBus(system.l2bus)

    system.membus = SystemXBar()
    system.l2cache.connectMemSideBus(system.membus)

    system.cpu.createInterruptController()
    system.system_port = system.membus.cpu_side_ports

    system.mem_ctrl = MemCtrl()
    system.mem_ctrl.dram = DDR3_1600_8x8()
    system.mem_ctrl.dram.range = system.mem_ranges[0]
    system.mem_ctrl.port = system.membus.mem_side_ports

    system.workload = SEWorkload.init_compatible(binary)
    process = Process()
    process.cmd = [binary]
    system.cpu.workload = process
    system.cpu.createThreads()
    return system


def add_chaos(system, first_clock=0, max_faults=0, probability=1.0,
              fault_type="bit_flip", bits=1, reg_class="integer", rng_seed=0,
              max_reg_idx=31):
    # CHAOSReg: inject one fault per the given model, log everything.
    #
    # Injection COUNT is controlled by maxFaults (patched-in param):
    #   maxFaults=1 -> exactly one fault per run (patch guarantee).
    #   maxFaults=0 -> original unlimited behavior.
    # lastClock is FIXED to 0 = unrestricted (per project config discipline).
    # Do NOT use lastClock as a window control: a nonzero lastClock whose
    # value falls before the first geometric-sampled injection causes silent
    # zero-injection with no error (see CHAOSReg.cc attackCheck comment).
    # rng_seed (patched-in): 0 = random_device (original, NON-reproducible);
    # nonzero = fixed seed so register/mask are reproducible across re-runs
    # of the SAME firstClock. This is essential: without it, --seed at the
    # Python level only fixes firstClock sampling, NOT which register/mask
    # CHAOS picks inside gem5 (rng.seed(rd()) uses system entropy).
    # max_reg_idx (patched): restrict integer sampling to indices [0,30] =
    # X0-X30, excluding integer[31]=Zero and idx>=32 banked/non-arch slots
    # (the ARM IntRegClass zero-trap). 0 = original full-range behavior.
    fi = CHAOSReg(
        cpu=system.cpu,
        probability=probability,
        faultType=fault_type,
        bitsToChange=bits,
        regTargetClass=reg_class,
        firstClock=first_clock,
        lastClock=0,
        maxFaults=max_faults,
        rngSeed=rng_seed,
        maxRegIdx=max_reg_idx,
        writeLog=True,
    )
    system.CHAOSReg = fi


def add_chaos_phys(system, first_clock=0, max_faults=0, probability=1.0,
                   fault_type="bit_flip", bits=1, rng_seed=0,
                   injection_mode="phys", target_phys_idx=-1,
                   target_arch_idx=0, fault_mask=0):
    # CHAOSPhysReg: inject into the O3 physical register file.
    # injection_mode:
    #   'phys'         = inject by physical register index (ITC'23/GeFIN)
    #   'arch_frontend'= renameMap.lookup (corrected arch; in-flight mapping)
    #   'arch_commit'  = commitRenameMap.lookup (= CHAOSReg behavior, fails O3)
    # target_phys_idx: -1 = random across int phys regs (phys mode only)
    # fault_mask: 0 = random mask (bitsToChange bits); nonzero = fixed mask,
    # used for equivalence tests (same mask across modes).
    fi = CHAOSPhysReg(
        cpu=system.cpu,
        injectionMode=injection_mode,
        targetPhysRegIdx=target_phys_idx,
        targetArchRegIdx=target_arch_idx,
        probability=probability,
        faultType=fault_type,
        bitsToChange=bits,
        faultMask=fault_mask,
        firstClock=first_clock,
        lastClock=0,
        maxFaults=max_faults,
        rngSeed=rng_seed,
        writeLog=True,
    )
    system.CHAOSPhysReg = fi

def add_chaos_lsq_fwd(system, first_clock=0, max_faults=0, probability=1.0,
                      fault_type="bit_flip", bits=1, rng_seed=0,
                      structural_fault="byte_lane_skew", skew_bytes=0):
    # CHAOSLSQFwd: store-to-load forwarding-path structural fault injector (O3).
    # structuralFault=byte_lane_skew models core-179 D1 (load returned rol_k(stale)).
    fi = CHAOSLSQFwd(
        cpu=system.cpu,
        probability=probability,
        faultType=fault_type,
        bitsToChange=bits,
        firstClock=first_clock,
        lastClock=0,
        maxFaults=max_faults,
        rngSeed=rng_seed,
        structuralFault=structural_fault,
        skewBytes=skew_bytes,
        writeLog=True,
    )
    system.CHAOSLSQFwd = fi


# --- Top-level execution (gem5.opt exec()s this file, so __name__ is not
#     "__main__"; run directly here) ---
_ap = argparse.ArgumentParser()
_ap.add_argument("--binary", required=True, help="static aarch64 binary")
_ap.add_argument(
    "--mode",
    choices=["baseline", "inject"],
    default="baseline",
    help="baseline = no CHAOS; inject = mount CHAOSReg",
)
_ap.add_argument(
    "--first-clock",
    type=int,
    default=0,
    help="firstClock (cycle) for CHAOS injection; ignored in baseline mode",
)
_ap.add_argument(
    "--max-faults",
    type=int,
    default=0,
    help="maxFaults cap (0=unlimited); use 1 for single-injection campaign",
)
_ap.add_argument(
    "--probability",
    type=float,
    default=1.0,
    help="per-interval injection probability (use 1.0 with maxFaults=1 so "
    "the first (and only) injection lands exactly at firstClock)",
)
_ap.add_argument("--fault-type", default="bit_flip",
                help="bit_flip | stuck_at_zero | stuck_at_one | random")
_ap.add_argument("--bits", type=int, default=1,
                help="bitsToChange (use 32 with stuck_at_one for positive control)")
_ap.add_argument("--reg-class", default="integer",
                help="integer | floating_point | both")
_ap.add_argument("--rng-seed", type=int, default=0,
                help="CHAOS injection RNG seed (0=random_device/non-repro; "
                "nonzero=fixed for reproducible register/mask)")
_ap.add_argument("--max-reg-idx", type=int, default=31,
                help="exclusive upper bound on register index (31=X0-X30, "
                "excludes Zero/banked slots; 0=original full-range)")
_ap.add_argument("--injector", choices=["reg", "phys", "lsq_fwd"], default="reg",
                help="reg = CHAOSReg (arch-commit map); phys = CHAOSPhysReg "
                "(physical regfile / arch-frontend / arch-commit via injection-mode)")
_ap.add_argument("--injection-mode", default="phys",
                help="CHAOSPhysReg mode: phys | arch_frontend | arch_commit")
_ap.add_argument("--target-phys-idx", type=int, default=-1,
                help="CHAOSPhysReg phys mode: target physical reg index (-1=random)")
_ap.add_argument("--target-arch-idx", type=int, default=0,
                help="CHAOSPhysReg arch_* modes: target arch reg index")
_ap.add_argument("--fault-mask", type=lambda x: int(x,0), default=0,
                help="fixed fault mask (0=random); for equivalence tests across modes")
_ap.add_argument("--structural-fault", default="none",
                choices=["none","byte_lane_skew","all_zero"],
                help="CHAOSLSQFwd structural fault (P-D1); default none")
_ap.add_argument("--skew-bytes", type=int, default=0,
                help="byte_lane_skew rotation 1..7; 0=random per event")
# --- Harpocrates coverage instrumentation (harp plan Task 1.2) ---
_ap.add_argument("--cov", action="store_true", default=False,
                help="mount CHAOSCov (single-run ACE/IBR coverage; "
                     "default off = exact pre-harp behavior)")
_ap.add_argument("--cov-roi", default="m5ops", choices=["m5ops","cycles","all"],
                help="ROI mode: m5ops (workbegin/workend) | cycles | all")
_ap.add_argument("--cov-roi-begin-cycle", type=int, default=0,
                help="ROI begin cycle (cov-roi=cycles)")
_ap.add_argument("--cov-roi-end-cycle", type=int, default=0,
                help="ROI end cycle (cov-roi=cycles; 0=end)")
_ap.add_argument("--cov-detail", action="store_true", default=True,
                help="write harp_cov_detail.log (advice-engine evidence)")
# --- SDC-ED Task 2.1: CPU-profile-driven CHAOSCov denominators ---
_ap.add_argument("--cov-profile", default=None,
                help="CPU profile YAML (configs/cpu-profiles/*.yaml): "
                     "overrides IBR FU counts/widths from the profile's "
                     "IEX/FSU fus tables. Absent = TaiShan v110 defaults "
                     "(behavior identical to the pre-parameterization "
                     "hardcoded values)")
# --- FU permanent fault (harp plan Task 5.2, execution-level L1) ---
_ap.add_argument("--fu-perm", action="store_true", default=False,
                help="mount CHAOSFUPerm (permanent execution-level FU fault)")
_ap.add_argument("--fu-perm-opclass", default="IntAlu",
                help="target OpClass name (IntAlu/IntMult/FloatAdd/...)")
_ap.add_argument("--fu-perm-mask", type=lambda x: int(x, 0), default=0,
                help="fixed result XOR mask (0 = one random bit from seed)")
_ap.add_argument("--fu-perm-seed", type=int, default=20260916,
                help="seed for the random bit when mask=0")
_ap.add_argument("--fu-perm-first-clock", type=int, default=0,
                help="cycle after which the fault is active (0=start; "
                     "set to ROI begin to skip C-lib startup)")
# --- CHAOSFPU FP writeback fault (harp plan Task 5.4: FP FU SFI) ---
_ap.add_argument("--fpu-inject", action="store_true", default=False,
                help="mount CHAOSFPU (FP writeback result corruption)")
_ap.add_argument("--fpu-fault-mask", type=lambda x: int(x, 0), default=0,
                help="FP result XOR mask (0 = random bit from seed)")
_ap.add_argument("--fpu-first-clock", type=int, default=0,
                help="first cycle eligible")
_ap.add_argument("--fpu-seed", type=int, default=20260916,
                help="RNG seed for random bit")
_ap.add_argument("--fpu-bit-segment", default="all",
                help="all | low | mid | high (IEEE754 spectrum)")

# --- gate-level netlist FU fault (harp plan Task 5.3) ---
_ap.add_argument("--gate-fu", action="store_true", default=False,
                help="mount CHAOSGateFU (synthetic gate-level netlist "
                     "stuck-at; IntAlu/IntMult)")
_ap.add_argument("--gate-fu-opclass", default="IntMult",
                help="netlist target: IntAlu (Kogge-Stone) | IntMult "
                     "(shift-add array)")
_ap.add_argument("--gate-fu-gate", type=int, default=-1,
                help="gate index to stick (-1 = none, equivalence mode)")
_ap.add_argument("--gate-fu-polarity", type=int, default=1,
                help="stuck value 0|1")
_ap.add_argument("--gate-fu-first-clock", type=int, default=0,
                help="cycle after which the fault is active")
_args = _ap.parse_args()

system = build_system(_args.binary)
if _args.mode == "inject":
    if _args.injector == "phys":
        add_chaos_phys(
            system,
            first_clock=_args.first_clock,
            max_faults=_args.max_faults,
            probability=_args.probability,
            fault_type=_args.fault_type,
            bits=_args.bits,
            rng_seed=_args.rng_seed,
            injection_mode=_args.injection_mode,
            target_phys_idx=_args.target_phys_idx,
            target_arch_idx=_args.target_arch_idx,
            fault_mask=_args.fault_mask,
        )
    elif _args.injector == "lsq_fwd":
        add_chaos_lsq_fwd(
            system,
            first_clock=_args.first_clock,
            max_faults=_args.max_faults,
            probability=_args.probability,
            fault_type=_args.fault_type,
            bits=_args.bits,
            rng_seed=_args.rng_seed,
            structural_fault=_args.structural_fault,
            skew_bytes=_args.skew_bytes,
        )
    else:
        add_chaos(
            system,
            first_clock=_args.first_clock,
            max_faults=_args.max_faults,
            probability=_args.probability,
            fault_type=_args.fault_type,
            bits=_args.bits,
            reg_class=_args.reg_class,
            rng_seed=_args.rng_seed,
            max_reg_idx=_args.max_reg_idx,
        )

# --- FU permanent injector (Task 5.2): default-off mount ---
if _args.fu_perm:
    system.CHAOSFUPerm = CHAOSFUPerm(
        cpu=system.cpu,
        targetOpClass=_args.fu_perm_opclass,
        faultMask=_args.fu_perm_mask,
        rngSeed=_args.fu_perm_seed,
        firstClock=_args.fu_perm_first_clock,
    )

# --- CHAOSFPU (Task 5.4): FP writeback fault, self-wires its hook ---
if _args.fpu_inject:
    system.CHAOSFPU = CHAOSFPU(
        cpu=system.cpu,
        probability=1.0,
        faultMask=_args.fpu_fault_mask,
        bitsToChange=1,
        bitSegment=_args.fpu_bit_segment,
        firstClock=_args.fpu_first_clock,
        lastClock=0,
        maxFaults=1,
        rngSeed=_args.fpu_seed,
        writeLog=True,
    )

# --- Gate-level netlist injector (Task 5.3): default-off mount ---
if _args.gate_fu:
    system.CHAOSGateFU = CHAOSGateFU(
        cpu=system.cpu,
        targetOpClass=_args.gate_fu_opclass,
        targetGate=_args.gate_fu_gate,
        stuckPolarity=_args.gate_fu_polarity,
        firstClock=_args.gate_fu_first_clock,
    )

# --- Harpocrates coverage analyzer (Task 1.2): default-off mount ---
if _args.cov:
    # SDC-ED Task 2.1: IBR denominators from the CPU profile when given.
    # Defaults (absent --cov-profile) are the TaiShan v110 fu_pool values,
    # identical to the pre-parameterization C++ hardcoded arrays.
    _cov_extra = {}
    if _args.cov_profile:
        import yaml as _yaml
        with open(_args.cov_profile) as _f:
            _prof = _yaml.safe_load(_f)
        _units = _prof.get("units", {})

        def _fu_param(unit, key, names):
            # Map profile FU entries to the 4 IBR classes. Widths: the
            # profile stores per-FU input path width (e.g. 128 for an int
            # adder's 2x64 inputs; 256 for FP 2x128 NEON lanes) — pass
            # through as-is; count from the matching fus entry.
            vals = []
            for n in names:
                d = ((_units.get(unit) or {}).get("fus") or {}).get(n) or {}
                vals.append(int(d.get(key, 0)) if d else 0)
            return vals

        _counts = _fu_param("IEX", "count", ["int_add", "int_mul"]) + \
                  _fu_param("FSU", "count", ["fp_add", "fp_mul"])
        _widths = _fu_param("IEX", "width", ["int_add", "int_mul"]) + \
                  _fu_param("FSU", "width", ["fp_add", "fp_mul"])
        if all(_counts) and all(_widths):
            _cov_extra["ibrFuCounts"] = _counts
            _cov_extra["ibrFuWidths"] = _widths
            print(f"[cov-profile] {_args.cov_profile}: "
                  f"ibrFuCounts={_counts} ibrFuWidths={_widths}")
        else:
            # Undisclosed FU fields: keep defaults (schema.md rule 1 —
            # never guess; the honest fallback is the calibre defaults).
            print(f"[cov-profile] {_args.cov_profile}: FU fields "
                  f"undisclosed/absent — keeping TaiShan v110 defaults")

    system.CHAOSCov = CHAOSCov(
        cpu=system.cpu,
        targetCache=system.cpu.dcache,
        cacheNumBlocks=64 * 1024 // 64,  # L1D 64KiB, 64B blocks
        sqEntries=system.cpu.SQEntries,
        roiMode=_args.cov_roi,
        roiBeginCycle=_args.cov_roi_begin_cycle,
        roiEndCycle=_args.cov_roi_end_cycle,
        writeDetail=_args.cov_detail,
        **_cov_extra,
    )

root = Root(full_system=False, system=system)
m5.instantiate()

print(f"Beginning simulation! mode={_args.mode} binary={_args.binary}")
exit_event = m5.simulate()
print(f"Exiting @ tick {m5.curTick()} because {exit_event.getCause()}")
code = exit_event.getCode()
if code != 0:
    print(f"Workload exit code: {code}")
