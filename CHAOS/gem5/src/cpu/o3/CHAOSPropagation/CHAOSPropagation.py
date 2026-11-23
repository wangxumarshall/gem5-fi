from m5.params import *
from m5.SimObject import SimObject

# CHAOSPropagation — [LSU][OBS-L3] real L3 propagation-chain tracer for LSU
# non-PRF faults (central correction directive 2026-10-13). READ-ONLY for
# architectural/µarch state: it observes the injector call path, the LSQ
# request/response path and the commit stream, and writes one CSV node per
# propagation event into prop_trace.csv.gz (pinned v1 format — see
# CHAOSPropagation.hh). NOT an injector: attaching it must leave the
# workload FINAL checksum byte-identical (CHAOSMicroSnap/CHAOSCommitTrace
# hard-gate precedent). Consumed by tools/lsu_l3_propagation.py
# (COVERED_FAMILIES = addrpath + cache; lsqfwd/prefetch/exmod stay
# unsupported, honestly).
class CHAOSPropagation(SimObject):
    type = 'CHAOSPropagation'
    cxx_class = 'gem5::CHAOSPropagation'
    cxx_header = "cpu/o3/CHAOSPropagation/CHAOSPropagation.hh"

    cpu = Param.BaseCPU(NULL, "Target CPU (must be an O3CPU)")

    traceFile = Param.String("prop_trace.csv.gz",
        "propagation trace output (relative to --outdir; .gz = auto gzip)")
    writeLog = Param.Bool(True,
        "write the propagation trace (false = attached but inert)")
    addrExpiryTicks = Param.Unsigned(20000000,
        "registry entry lifetime in ticks (0 = never expire); bounds "
        "address-reuse misattribution (lazy sweep on insert/lookup)")
    # [MDSPEC][H0] PROP-EVT unified stream (spec sheet 11)
    evtTraceFile = Param.String("prop_evt.txt.gz",
        "PROP-EVT unified event stream (relative to --outdir; .gz = auto "
        "gzip; all registry fields per line, empty values kept)")
    runId = Param.String("", "campaign RunID (spec sheet 11: written into "
        "every PROP-EVT event; empty = unset, honest empty)")
    sampleRunId = Param.String("", "sample index within the RunID (spec "
        "sheet 11 sample_run_id; empty = unset)")
    # [MMU-TRACE v1] VA-gated unified MMU/TLB/PTW/LSU event trace. It writes
    # into the same prop_evt.txt.gz stream as the fault-propagation events.
    mmuTrace = Param.Bool(False,
        "emit fault-free unified MMU trace events (VA-gated; fault events "
        "always use the same stream)")
    mmuTraceVaLo = Param.Addr(0,
        "MMU trace VA lower bound (inclusive); 0 = no lower bound")
    mmuTraceVaHi = Param.Addr(0,
        "MMU trace VA upper bound (exclusive); 0 = unbounded")
    # [MMU-TRACE v2] One-shot M01/M02 smoke fault configuration. Empty model
    # = both hooks are strict no-ops (fault-free execution is unchanged).
    mmuFaultModel = Param.String("",
        "MMU fault model: '' (off) | 'M01'..'M08'")
    # [Phase 2.2] Independent injection switch. Fault enablement is decided
    # here (plus the model selection) and is NEVER coupled to writeLog or
    # mmuTrace: disabling logging/trace must not disable the fault hook.
    mmuFaultEnable = Param.Bool(True,
        "enable the selected MMU fault model (independent of writeLog/"
        "mmuTrace; false = configured but inert)")
    mmuM01Va = Param.Addr(0, "M01 target canonical VA")
    mmuM01Asid = Param.Int(-1, "M01 target ASID (-1 = any)")
    mmuM01Vmid = Param.Int(-1, "M01 target VMID (-1 = any)")
    mmuM01N = Param.Unsigned(12, "M01 target page size exponent")
    # [MMU-TRACE v3] Optional target translation-regime / security-state
    # constraints. -1 keeps the Phase-2 behaviour (any regime/state).
    mmuM01Regime = Param.Int(-1,
        "M01 target TranslationRegime (EL10=0, EL20=1, EL2=2, EL3=3; -1 = any)")
    mmuM01SecurityState = Param.Int(-1,
        "M01 target SecurityState (NonSecure=0, Secure=1; -1 = any)")
    mmuM02Va = Param.Addr(0, "M02 target canonical VA")
    mmuM02OldPfn = Param.Addr(0, "M02 expected clean PFN")
    mmuM02XorMask = Param.Addr(1, "M02 refill PFN XOR mask")
    mmuM02DramLo = Param.Addr(0x80000000,
        "M02 lower bound of the valid guest DRAM PA range")
    mmuM02DramHi = Param.Addr(0x100000000,
        "M02 upper bound (exclusive) of the valid guest DRAM PA range")
    # [MMU-PHASE3] Generic target selector shared by M03-M08. Every field is
    # a strict guard: -1 / "" / 0-where-documented means "unconstrained".
    # The target VA is page-granular (same page under mmuTargetN).
    mmuTargetVa = Param.Addr(0, "target canonical VA (0 = any)")
    mmuTargetAsid = Param.Int(-1, "target ASID (-1 = any)")
    mmuTargetVmid = Param.Int(-1, "target VMID (-1 = any)")
    mmuTargetN = Param.Int(-1, "target page size exponent (-1 = any)")
    mmuTargetRegime = Param.Int(-1, "target TranslationRegime (-1 = any)")
    mmuTargetSecurityState = Param.Int(-1, "target SecurityState (-1 = any)")
    mmuTargetInstance = Param.String("", "target TLB instance ('' = any)")
    mmuTargetWalkLevel = Param.Int(-1, "target walk level (-1 = any)")
    mmuTargetSeq = Param.UInt64(0, "target DynInst seq (0 = any)")
    mmuTargetMode = Param.String("", "target mode Read|Write|Execute|Atomic "
                                     "('' = any)")
    mmuEligibleEventIndex = Param.UInt64(1,
        "1-based ordinal of the target event among eligible events")
    # [WHEN-5X3] Golden pre-scan. The selected model's hooks run their full
    # eligibility predicates, count and emit EVERY eligible event, and never
    # mutate state / activate the fault. The exit report carries
    # eligible_total so the runner can compute ceil(p*N).
    mmuPrescan = Param.Bool(False,
        "count/emit eligible events without injecting (golden pre-scan)")
    mmuFaultPersistence = Param.String("one_shot",
        "one_shot | entry_lifetime (corrupted TLB entry stays corrupted)")
    # Model-specific parameters (M03-M08).
    mmuM03CandidateAsid = Param.Int(-1,
        "M03: required foreign candidate ASID (-1 = any ASID != current)")
    mmuM04DecoyPfn = Param.Addr(0,
        "M04: legal decoy PFN substituted into the resident entry (0 = pick "
        "a same-size live entry's PFN)")
    mmuM05DecoyVa = Param.Addr(0,
        "M05: decoy VA whose live L2 partial entry supplies the next-table "
        "base (0 = unset). Selected by matchAddress; when set, an arbitrary "
        "live-scan fallback is disabled and a missing/illegal entry leaves "
        "M05 honestly unactivated.")
    mmuM05DecoyTableBase = Param.Addr(0,
        "M05: explicit decoy next-table base PA override (0 = derive from "
        "--mmu_m05_decoy_va, else the documented pilot live-scan fallback). "
        "If both are set, the selected entry's pfn must equal this base.")
    mmuM08PaXorMask = Param.Addr(0x1000,
        "M08: XOR mask applied to the final request PA (bit 12 = 4 KiB "
        "neighbor page)")
