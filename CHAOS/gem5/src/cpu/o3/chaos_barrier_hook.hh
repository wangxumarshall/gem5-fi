/*
 * chaos_barrier_hook.hh — [MDSPEC][R4-9-FSMC] O06/O07 barrier-completion /
 * order-tag hook registry (header-only TU, same shape as
 * chaos_lsu_trigger.hh's chaosLsuF6Notify: one single-consumer function
 * pointer, self-registered by the armed injector at startup(), all-null =
 * zero regression).
 *
 * WHY A REGISTRY AND NOT A POINTER: MemDepUnit holds no CPU and no injector
 * pointer (mem_dep_unit.hh keeps only `InstructionQueue *iqPtr`; the
 * `CPU *cpu` argument of init() is used solely for addStatGroup —
 * mem_dep_unit.cc:150-170). The S10 precedent solves the identical problem
 * the same way (store_set.cc:34-36: "StoreSet has no CPU or injector
 * pointer — the S10-armed CHAOSLSQFwd self-registers them").
 *
 * NODE (spec sheet 07, models O06/O07): gem5 O3 has NO separate
 * "barrier-completion event" and NO "LSU ordering queue with order tags":
 * the ARM DMB/DSB instructions carry no memory access at all
 * (misc64.isa:229-233 Dmb64 = empty code; misc.isa:1216-1230), and the whole
 * architectural effect of a barrier on this platform is MemDepUnit's
 * barrier-SN bookkeeping:
 *   - insert: `insertBarrierSN` puts the barrier's InstSeqNum into
 *     loadBarrierSNs / storeBarrierSNs (mem_dep_unit.cc:160-183);
 *   - gate:    `hasLoadBarrier()/hasStoreBarrier()` keeps every later
 *     memory op from issuing until the SN is gone (mem_dep_unit.hh:252-256);
 *   - release: `completeInst` erases it (mem_dep_unit.cc:430-457).
 * So the InstSeqNum IS the order tag and the insert/release pair IS the
 * barrier-completion handshake on this platform. That mapping is an HONEST
 * PROXY for the spec's "ordering queue / order tag / valid-ready" wording —
 * recorded in the R4-9-FSMC-C report, never presented as a cycle-exact
 * ordering-queue model.
 */
#ifndef __CPU_O3_CHAOS_BARRIER_HOOK_HH__
#define __CPU_O3_CHAOS_BARRIER_HOOK_HH__

#include <cstdint>

namespace gem5
{

// Barrier SN-insertion point (MemDepUnit::insertBarrierSN). Returns true =>
// the caller must NOT track the SN: the barrier is released before the
// memory ops preceding it have drained, so every later load/store issues
// past it (O06-a "提前 done"; the spec's "提前done会让后续访问越过屏障").
inline bool (*chaosBarrierInsertHook)(uint64_t seq, bool is_read,
                                      bool is_write) = nullptr;

// Barrier SN-release point (MemDepUnit::completeInst, before the erase).
// Return code (int, so the header stays free of the injector's enum):
//   0 = None    — normal path (the original asserts + erase run unchanged);
//   1 = Skip    — the completion is LOST: the SN stays tracked forever, every
//                 later memory op keeps waiting (O06-b "延后/丢失 done" →
//                 the spec's stall/Timeout channel);
//   2 = Swap    — order-tag exchange (O07 proxy): the caller erases *subst
//                 instead of the real SN — another in-flight transaction's
//                 ordering tag is released in this one's place.
// `subst` is an out-param used only for the Swap code (0 = unusable → the
// caller falls back to the normal path).
inline int (*chaosBarrierReleaseHook)(uint64_t seq, bool is_read,
                                      bool is_write, uint64_t *subst) = nullptr;

} // namespace gem5

#endif // __CPU_O3_CHAOS_BARRIER_HOOK_HH__
