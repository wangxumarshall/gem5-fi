from m5.params import *
from m5.SimObject import SimObject

class CHAOSROB(SimObject):
    type = 'CHAOSROB'
    cxx_class = 'gem5::CHAOSROB'
    cxx_header = "cpu/o3/CHAOSROB/CHAOSROB.hh"

    cpu = Param.BaseCPU(NULL, "Target CPU (must be an O3CPU)")

    # §2.3 ROB modes:
    #   entry_bitflip: at retireHead, flip a bit of a ROB entry field (field=
    #                  result|done|exc_status|dest_phys|spec) at distance D
    #                  from the head. Stratifies 'time-to-commit'.
    #   exc_suppress:  clear the head's fault/exception-status bit before
    #                  retireHead -> a fault that should raise SError/DUE is
    #                  silently swallowed (quantifies 'DUE->SDC conversion').
    #   spec_leak:     on squash, RETAIN one wrong-path µop's phys-reg write
    #                  (speculative state leak, method1) — TODO (needs squash
    #                  path edit; deferred to a follow-up §2.3 patch).
    # W5.1-W5.3 (ooo 04-design-matrix D25-D31, Int Dispatch/ROB) — the
    # ROB-entry WRITE-path site (ROB::insertInst; the TC'23 site, the entry
    # is corrupted as it is written into the ROB):
    #   pc_bitflip/pc_bitflip2 (D25/D26): flip 1/2 random bits of the
    #                  entry's PC field (pcState pc address, ~48-bit space).
    #   pc_stuck (D27, F5): ONE entry's PC bit permanently forced 0/1
    #                  (write-path mask at the entry write + retire readback).
    #   destid_bitflip/destid_bitflip2 (D28/D29): flip 1/2 random bits of
    #                  the entry's int dest physReg identifier.
    #   destid_swap_active (D30): replace it with the dest physReg of
    #                  another ROB-resident in-flight instruction (legal
    #                  domain, designed to bypass the dependency check).
    #   destid_stuck (D31, F5): ONE entry's dest-id bit stuck-at 0/1.
    # U3 (ooo 03-design-matrix B08/B09/FB08/FB09, pipeline timing
    # family B -- squash/commit timing perturbations, data payloads stay
    # correct; 1:1 to the 03 table's early/late/lost/duplicated axes):
    #   squash_timing_{early,late,drop,dup} (B08): ROB::squash timing --
    #     early = same-tick drain start (commitStatus flip, approx=
    #     squash_drain_advanced_1c); late = walk deferred one cycle
    #     (perf-only under the ROBSquashing gate); drop = walk lost,
    #     wrong-path insts stay in the ROB and reach commitHead
    #     (SDC/Crash face, timeout-guarded); dup = same-boundary squash
    #     replayed at clockEdge(+1) (ROB-local, honest divergence: post-
    #     recovery refills get squashed with no refetch).
    #   fp_squash_timing_{early,late,dup} (FB08): B08 + FP/SIMD window
    #     gate (the squash window must contain a Float*/SimdFloat* op);
    #     fp_squash_timing_drop (FB08-c) = the squashed FP inst is NOT
    #     skipped at the IEW execute stage -- its result write lands in
    #     the freed (possibly recycled) vec physreg (alias pollution).
    #     FB08-b (FU-cancel lost) = arch-n/a (no independent FU-cancel
    #     event in gem5), recorded on the audit row.
    #   commit_timing_{early,late,drop,dup} (B09): commit-transaction
    #     sub-events -- early = one extra commit past commitWidth (the
    #     deferred head's grant arrives early; in-order commit => not-
    #     activated/Masked); late = doneSeqNum publish suppressed one
    #     cycle (rename P_prev frees + store commits lag, self-heal);
    #     drop = updateMiscRegs skipped (stale NZCV/FPSR, eligibility
    #     numDestRegs(MiscRegClass)>0); dup = extra retireHead after the
    #     bound commit (unready next head => readyToCommit assert Crash
    #     DUE; ready => leaves the commit stream, mostly Masked).
    #   fp_commit_timing_{early,late,drop,dup} (FB09): B09 + FP binding
    #     of the inst at the hook; FB09-c FPSR face shares the
    #     updateMiscRegs suppression (FP misc writers are rare -- honest
    #     0-activation possible); FB09-b V-mapping face and FB09-d
    #     old-dest face are covered by the U2 FR09 neighbors (audit row).
    mode = Param.String("entry_bitflip",
        "entry_bitflip | exc_suppress | pc_bitflip | pc_bitflip2 | pc_stuck"
        " | destid_bitflip | destid_bitflip2 | destid_swap_active"
        " | destid_stuck (spec_leak deferred)"
        " | squash_timing_early | squash_timing_late | squash_timing_drop"
        " | squash_timing_dup | fp_squash_timing_early"
        " | fp_squash_timing_late | fp_squash_timing_drop"
        " | fp_squash_timing_dup | commit_timing_early | commit_timing_late"
        " | commit_timing_drop | commit_timing_dup"
        " | fp_commit_timing_early | fp_commit_timing_late"
        " | fp_commit_timing_drop | fp_commit_timing_dup")

    field = Param.String("exc_status",
        "result | done | exc_status | dest_phys | spec (entry_bitflip field)")
    distanceFromHead = Param.Int(0,
        "inject into the entry D slots from the ROB head; -1=random. "
        "Stratifies time-to-commit (D=0 = head).")

    probability = Param.Float(1.0, "per-retireHead injection probability")
    firstClock = Param.UInt64(0, "first clock cycle eligible for injection")
    lastClock = Param.UInt64(0, "last cycle (0 = unrestricted)")
    faultMask = Param.UInt64(0, "bitmask for entry_bitflip (0=random single bit)")
    maxFaults = Param.UInt64(0, "max faults; 0 = unlimited. Use 1.")
    rngSeed = Param.UInt64(0, "RNG seed (0 = random_device)")
    writeLog = Param.Bool(True, "Write a fault_injections.log file")
    # W7.4 (ooo 04-design-matrix FP/SIMD Dispatch/ROB, the D87-prerequisite
    # dest-id analog at the rob_insert site): the register-class scope of
    # the destid family (destid_bitflip/bitflip2/swap_active/stuck).
    # "int" = the W5 D28-D31 scope (default, byte-identical behavior);
    # "vec" = the FP/SIMD twins — VecRegClass dest slots (scalar FP, FP
    # SIMD and integer SIMD dests ALL rename onto VecRegClass on AArch64),
    # dest-id domain [0, numVecPhysRegs), the swap_active pool collects
    # vec dests. The PC / done-bit / pointer families stay class-agnostic
    # (the ROB is a unified structure — TC'23).
    targetClass = Param.String("int", "int | vec (dest-id class scope)")
