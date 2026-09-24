from m5.params import *
from m5.SimObject import SimObject

class CHAOSRenameMap(SimObject):
    type = 'CHAOSRenameMap'
    cxx_class = 'gem5::CHAOSRenameMap'
    cxx_header = "cpu/o3/CHAOSRenameMap/CHAOSRenameMap.hh"

    cpu = Param.BaseCPU(NULL, "Target CPU (must be an O3CPU)")

    # §2.2 injection mode:
    #   map_bitflip  : after setEntry, remap arch_reg's entry to a DIFFERENT
    #                  valid physReg (XOR a bit of the physReg index — realized
    #                  as a 1-bit remap to another legal physReg, the method1
    #                  "张冠李戴" semantics; §2.2 map_bitflip).
    #   map_bitflip2 : W4.1 D12 (04-design-matrix R13) — flip TWO distinct
    #                  random bits of the physReg index (faultMask with >=2
    #                  set bits = directed control: its two lowest set bits).
    #                  Out-of-range flip on non-power-of-2 numPhysRegs is an
    #                  honest skip (logged, never clamped — hamming distance
    #                  between old/new phys idx is exactly 2 by construction).
    #   swap_to_active: W4.2a D13 (04-design-matrix R14, 换值·固定间隔) —
    #                  re-point arch_reg's entry at the dest physReg of a
    #                  RANDOM in-flight (ROB-resident) instruction (≠ the
    #                  current mapping): a legal, allocated, in-use physReg,
    #                  designed to bypass the dependency-check luck of the
    #                  bit-flip models. ROB empty / no candidate = honest
    #                  skip (logged). Log line carries new_phys=Z(active,
    #                  rob_dist=D) + the full ROB-active dest pool as the
    #                  "new_phys ∈ ROB active set" evidence.
    #   f5_substitute: point arch_reg's entry at ANOTHER CURRENTLY-ALLOCATED
    #                  (= not in the free list) physReg of the same class —
    #                  legal-domain substitution (§2.2 F5).
    #   f4_field_stuck: pin ONE map entry to a wrong physReg permanently
    #                  (every setEntry on that arch_reg re-applies the wrong
    #                  target) — §2.2 f4_field_stuck.
    # spec_leak (§2.3 Phase 4.1, method1 speculative-state leak): suppress
    # ONE history-buffer rollback in Rename::doSquash — the wrong-path µop's
    # dest reg stays mapped, its wrong-path value leaks into the correct
    # path (the rollback-suppression, not a value flip).
    # f5_rat_stuck (W4.3 D15, 04-design-matrix R16, F5 permanent): ONE
    # front-map RAT entry + ONE physReg-index bit stuck-at-0/1 (50/50),
    # armed once at the first in-window eligible write; EVERY subsequent
    # write to that entry — normal rename write AND squash-rollback restore
    # — stores the value with the bit forced (G2 write-path-mask semantics,
    # regfile.hh:360 pattern). Arming is the only fault count increment;
    # applications are logged as exposures (persistence evidence).
    # swap_mispred_event (W4 final D14, 04-design-matrix R15,
    # RAT映射字段·换值·误预测事件触发): the D13 swap_to_active model, but
    # eligible ONLY inside a branch-misprediction squash-restore window
    # (rename.cc arms the context around Rename::squash when
    # commitInfo.mispredictInst != NULL — traps/order-violations/
    # squashAfter never arm it). The event-vs-fixed-interval comparison
    # against D13 is the methodology check "事件触发是否真的更有效率".
    # hb_bitflip / hb_bitflip2 (W4 final D23/D24, 04-design-matrix R24/R25,
    # 重命名检查点·单/双比特翻转): gem5 has NO separate RAT-checkpoint
    # array — the recovery checkpoint IS the historyBuffer entry
    # RenameHistory{instSeqNum, archReg, newPhysReg, prevPhysReg}
    # (rename.hh:301, mechanism-verified N1). The injector flips 1 bit
    # (hb_bitflip) / 2 distinct random bits (hb_bitflip2) of ONE randomly
    # chosen field's physReg index at the checkpoint's CREATION
    # (rename.cc push_front site); the instruction keeps its TRUE dest, so
    # the fault stays DORMANT until doSquash (mispred restore) or
    # removeFromHistory (commit release) consumes the WRONG phys. Out-of-
    # range flip = honest skip (logged, never clamped).
    # stale_read (W4.4 D16, 04-design-matrix R17, event = the next rename
    # overwrite of the entry): that ONE rename write silently fails — the
    # entry keeps the previous occupant's still-legal mapping until the next
    # rename updates it normally; the renaming inst keeps its allocated dest.
    # Downstream readers read the OLD phys: stale but legal data. Not a
    # value swap (D13), not a stuck bit (D15) — the update never lands.
    mode = Param.String("map_bitflip",
        "map_bitflip | map_bitflip2 | swap_to_active | f5_substitute | "
        "f4_field_stuck | spec_leak | f5_rat_stuck | stale_read | "
        "swap_mispred_event | hb_bitflip | hb_bitflip2")

    targetArchReg = Param.Int(-1,
        "which register's map entry to corrupt (-1 = random within the int "
        "class, 0-30). HONEST SEMANTICS (W4.4 finding, 2026-09-24): this is "
        "the FLATTENED int-reg index seen at the rename site (Arm "
        "IntRegClassOps::flatten -> ISA::intRegMap), NOT the architectural "
        "Xn number — empirically flat(X0)=0, flat(X1)=1, flat(X19)=16 on "
        "AArch64 EL0. Low regs coincide; directed high-reg controls (e.g. "
        "the smoke xorshift accumulator X19) must pass the FLAT index (16).")

    probability = Param.Float(1.0,
        "per-setEntry injection probability (use 1.0 with maxFaults=1 so the "
        "single injection lands at firstClock on the next eligible setEntry)")

    firstClock = Param.UInt64(0, "first clock cycle eligible for injection")
    lastClock = Param.UInt64(0, "last cycle (0 = unrestricted)")

    faultMask = Param.UInt64(0,
        "bitmask for map_bitflip: which physReg-index bit to flip (0 = random "
        "bit in [0, log2(numPhysRegs)))")

    maxFaults = Param.UInt64(0,
        "max faults to inject; 0 = unlimited. Use 1 for single-fault campaigns.")
    rngSeed = Param.UInt64(0, "RNG seed (0 = random_device)")

    writeLog = Param.Bool(True, "Write a fault_injections.log file")
