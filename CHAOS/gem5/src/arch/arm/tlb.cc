/*
 * Copyright (c) 2010-2013, 2016-2025 Arm Limited
 * All rights reserved
 *
 * The license below extends only to copyright in the software and shall
 * not be construed as granting a license to any other intellectual
 * property including but not limited to intellectual property relating
 * to a hardware implementation of the functionality of the software
 * licensed hereunder.  You may use the software subject to the license
 * terms below provided that you ensure that this notice is replicated
 * unmodified and in its entirety in all distributions of the software,
 * modified or unmodified, in source code or in binary form.
 *
 * Copyright (c) 2001-2005 The Regents of The University of Michigan
 * All rights reserved.
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions are
 * met: redistributions of source code must retain the above copyright
 * notice, this list of conditions and the following disclaimer;
 * redistributions in binary form must reproduce the above copyright
 * notice, this list of conditions and the following disclaimer in the
 * documentation and/or other materials provided with the distribution;
 * neither the name of the copyright holders nor the names of its
 * contributors may be used to endorse or promote products derived from
 * this software without specific prior written permission.
 *
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
 * "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
 * LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
 * A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
 * OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
 * SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
 * LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
 * DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
 * THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
 * (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
 * OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 */

#include "arch/arm/tlb.hh"
#include "arch/arm/CHAOSArmTLB/CHAOSArmTLB.hh"  // Phase 3: TLB-entry injector (maybeCorrupt)
#include "arch/arm/CHAOSArmTLB/chaos_tlb_pfn.hh"  // [MMU-PHASE3] M04 decoy legality
#include "cpu/o3/chaos_lsu_trigger.hh"  // LSU W2 F6 event source (TlbHit, FS-only: SE never calls TLB::lookup)

#include <cstdlib>
#include <cxxabi.h>
#include <memory>
#include <sstream>
#include <string>
#include <typeinfo>
#include <vector>

#include "arch/arm/table_walker.hh"
#include "arch/arm/tlbi_op.hh"
#include "arch/arm/utility.hh"
#include "base/trace.hh"
#include "cpu/o3/CHAOSPropagation/CHAOSPropagation.hh"  // [MMU-TRACE v1]
#include "cpu/thread_context.hh"
#include "debug/TLB.hh"
#include "debug/TLBVerbose.hh"
#include "params/ArmTLB.hh"

namespace gem5
{

using namespace ArmISA;

namespace {

// [MMU-TRACE v1] Demangled TLBI operation class name (the TLBIOp subclasses
// have no virtual name()). Honest type identity, never a guessed mnemonic.
std::string
tlbiOpName(const TLBIOp &op)
{
    int status = 0;
    char *demangled = abi::__cxa_demangle(typeid(op).name(), nullptr, nullptr,
                                          &status);
    std::string out;
    if (status == 0 && demangled) {
        out = demangled;
        const size_t pos = out.rfind("::");
        if (pos != std::string::npos)
            out = out.substr(pos + 2);
    } else {
        out = "TLBI";
    }
    std::free(demangled);
    return out;
}

const char *
mmuModeName(BaseMMU::Mode mode)
{
    switch (mode) {
      case BaseMMU::Read:    return "Read";
      case BaseMMU::Write:   return "Write";
      case BaseMMU::Execute: return "Execute";
      default:               return "Unknown";
    }
}

// Normalized TLB instance label (itb / dtb / l2_shared / stage2_*), derived
// from the real SimObject name; falls back to the full name.
std::string
tlbInstanceName(const SimObject &obj)
{
    const std::string name = obj.name();
    static const char *const suffixes[] = {
        "stage2_itb", "stage2_dtb", "l2_shared", "itb", "dtb"
    };
    for (const char *s : suffixes) {
        const std::string suf(s);
        if (name.size() >= suf.size() &&
                name.compare(name.size() - suf.size(), suf.size(), suf) == 0)
            return suf;
    }
    return name;
}

// [MMU-PHASE3][M04] Hex formatting shared by the M04 activation/no-op events.
std::string
mmuHexAddr(Addr v)
{
    std::ostringstream os;
    os << "0x" << std::hex << v;
    return os.str();
}

// [MMU-PHASE3][M04] Is `e` a legal DECOY source for substituting `hit`?
// The decoy must be a live, complete, workload-owned resident translation of
// the SAME TLB layer with the configured PFN:
//   valid, !partial, pfn != 0, pfn == decoy_pfn,
//   same N, same ASID (same address space / process), same regime,
//   same security state, same VMID when the regime uses one,
//   and a DIFFERENT VA page than the target (never a self-substitution).
// Never a fabricated view: every predicate reads the real table entry.
bool
m04DecoyIsLegal(const ArmISA::TlbEntry &e, const ArmISA::TlbEntry &hit,
                Addr decoy_pfn)
{
    if (!e.valid || e.partial)
        return false;
    if (e.pfn == 0 || e.pfn != decoy_pfn)
        return false;
    if (e.N != hit.N)
        return false;
    if (e.pfn == hit.pfn)          // a substitution must change the frame
        return false;
    if (e.asid != hit.asid || e.ss != hit.ss || e.regime != hit.regime)
        return false;
    if (useVMID(hit.regime) && e.vmid != hit.vmid)
        return false;
    if (e.vpn == hit.vpn)          // same VA page => same translation
        return false;
    return true;
}

// [MMU-PHASE3][M04] Does `e` alias the faulted translation in ANOTHER
// resident entry? Same architectural key and the ORIGINAL (pre-substitution)
// PFN: identical VA page, N, ASID, VMID (when used), regime, security state.
bool
m04AliasesHit(const ArmISA::TlbEntry &e, const ArmISA::TlbEntry &hit,
              Addr old_pfn)
{
    if (!e.valid || e.partial || e.pfn == 0 || e.pfn != old_pfn)
        return false;
    if (e.N != hit.N || e.vpn != hit.vpn)
        return false;
    if (e.asid != hit.asid || e.ss != hit.ss || e.regime != hit.regime)
        return false;
    if (useVMID(hit.regime) && e.vmid != hit.vmid)
        return false;
    return true;
}

} // anonymous namespace

TlbEntry*
TLB::Table::accessEntry(const KeyType &key)
{
    auto entry = findEntry(key);

    if (entry && !key.functional) {
        accessEntry(entry);
    }

    return entry;
}

TlbEntry*
TLB::Table::findEntry(const KeyType &key) const
{
    // Exploiting locality to maximaize simulator performance
    if (prev && prev->N == key.pageSize && prev->match(key)) {
        return prev;
    }

    for (auto candidate : indexingPolicy->getPossibleEntries(key)) {
        auto entry = static_cast<TlbEntry*>(candidate);
        // We check for pageSize match outside of the Entry::match
        // as the latter is also used to match entries in TLBI invalidation
        // where we don't care about the pageSize
        if (entry->N == key.pageSize && entry->match(key)) {
            return prev = entry;
        }
    }

    return nullptr;
}

void
TLB::Table::invalidatePrev(const TlbEntry *invalid)
{
    if (!invalid || invalid == prev)
        prev = nullptr;
}

TLB::TLB(const ArmTLBParams &p)
    : BaseTLB(p),
      table(name().c_str(), p.size, p.assoc,
            p.replacement_policy, p.indexing_policy),
      size(p.size),
      isStage2(p.is_stage2),
      _walkCache(false),
      tableWalker(nullptr),
      stats(*this), rangeMRU(1), vmid(0)
{
    for (int lvl = LookupLevel::L0;
         lvl < LookupLevel::Num_ArmLookupLevel; lvl++) {

        auto it = std::find(
            p.partial_levels.begin(),
            p.partial_levels.end(),
            lvl);

        auto lookup_lvl = static_cast<LookupLevel>(lvl);

        if (it != p.partial_levels.end()) {
            // A partial entry from of the current LookupLevel can be
            // cached within the TLB
            partialLevels[lookup_lvl] = true;

            // Make sure this is not the last level (complete translation)
            if (lvl != LookupLevel::Num_ArmLookupLevel - 1) {
                _walkCache = true;
            }
        } else {
            partialLevels[lookup_lvl] = false;
        }
    }

    table.setDebugFlag(::gem5::debug::TLB);
}

TLB::~TLB()
{
}

void
TLB::setTableWalker(TableWalker *table_walker, bool functional)
{
    tableWalker = table_walker;
}

TlbEntry*
TLB::lookup(Lookup lookup_data)
{
    const auto mode = lookup_data.mode;

    // [MMU-PHASE3][M04] The promotion lineage read by multiLookup must name
    // the lookup event of THIS lookup only (0 = no event emitted).
    chaosMmuLastLookupEventId = 0;

    // [MMU-TRACE v1] One lookup id per TLB-level lookup.
    CHAOSPropagation *const mmu_prop = CHAOSPropagation::instance();
    const uint64_t mmu_lookup_id =
        (mmu_prop && mmu_prop->mmuTraceEnabled())
            ? mmu_prop->mmuNewLookupId() : 0;
    // [MMU-TRACE v4] Transaction sequence for TRACE events only. Execute-mode
    // fetch lookups have no Request seq and carry a synthetic one; real data
    // requests always use chaosLookupReqSeq and are therefore bit-identical.
    // Fault-model gates below keep reading chaosLookupReqSeq, never this.
    const uint64_t chaos_trace_seq = chaosLookupReqSeq
        ? chaosLookupReqSeq : chaosLookupSyntheticSeq;

    // [MMU-PHASE3] M03/M04 fault evidence for THIS lookup. Kept separate from
    // mmu_fault_ptag (the M01/M02 latch id below) so the M01 disarm hook
    // never sees a Phase-3 fault id.
    uint64_t mmu_phase3_ptag = 0;
    // True when this hit consumes an entry registered as an M04 fault: the
    // real lookup event carries the fault id and a consume witness follows.
    bool mmu_phase3_consume = false;

    TlbEntry *retval = nullptr;
    // We iterate over all stored sizes, starting from the
    // smallest until the biggest. In this way we prioritize
    // complete translations over partial translations
    for (const auto &page_size : observedPageSizes) {
        lookup_data.pageSize = page_size;
        if (retval = table.accessEntry(lookup_data); retval)
            break;
    }

    // Phase 3 §六.4 item 3: CHAOSArmTLB hook. On a TLB HIT, corrupt the
    // entry's pfn before returning it to the MMU — models a defective TLB
    // cell (address-translation-path fault). nullptr = no injector.
    // [MDSPEC][R4-4] chaosLookupReqSeq/Size carry the Request identity of
    // the translation in flight (set by MMU::getTe around this lookup) so
    // the fault chain registers SEQ-PRIMARY instead of address-only.
    if (retval && chaosTLB) {
        chaosTLB->maybeCorrupt(retval, lookup_data.va,
                               chaosLookupReqSeq, chaosLookupReqSize);
    }

    // [MDSPEC][R4-10-T07] CAM-compare / way-select hook. Runs for BOTH
    // outcomes: false_hit fabricates a hit on a MISS (retval == nullptr),
    // wrong_way returns a different valid way, double_hit observes a
    // fabricated double match. For every non-T07 model this is a strict
    // no-op returning `retval` unchanged (zero budget), so T01-T06/T08/T10
    // stay byte-equivalent. See CHAOSArmTLB::maybeCorruptLookup.
    if (chaosTLB) {
        retval = chaosTLB->maybeCorruptLookup(retval, lookup_data.va,
                                              chaosLookupReqSeq,
                                              chaosLookupReqSize);
    }

    // ================= [MMU-PHASE3] M03: ASID-mismatch false hit ==========
    // [MMU-PHASE3][M03] Lookup-RESULT fault: on a real MISS, return a REAL
    // resident, valid, COMPLETE, NON-GLOBAL entry of this TLB whose only
    // mismatching match() key field is ASID (same VA range/N/regime/security
    // state/VMID, foreign non-global ASID). Nothing is fabricated: the
    // candidate is the actual table entry, and its translation payload (pfn,
    // attributes) is returned intact. No candidate => no activation and the
    // lookup honestly stays a miss. One-shot: mmuFaultActivate returns 0
    // after the first activation, and only a non-zero ptag returns the
    // candidate, so M03 cannot fire twice.
    //
    // R05 (ITLB execute context) needs no special case: the itb instance is
    // the same ArmISA::TLB and reaches this same block.
    if (mmu_prop && !retval && !lookup_data.functional &&
            !lookup_data.ignoreAsn && mmu_prop->mmuFaultModelIs("M03")) {
        const std::string tlb_inst = tlbInstanceName(*this);
        // The requested page size is not known on a miss. The target
        // selector is evaluated with the configured N (when set); the
        // candidate scan enforces that N explicitly below.
        const unsigned key_n = mmu_prop->mmuTargetN() >= 0
            ? (unsigned)mmu_prop->mmuTargetN() : 0u;
        const bool key_ok = mmu_prop->mmuTargetKeyMatch(
            lookup_data.va, (uint16_t)lookup_data.asn,
            (uint16_t)lookup_data.vmid, key_n,
            (unsigned)lookup_data.targetRegime, (unsigned)lookup_data.ss,
            tlb_inst.c_str(), -1, mmuModeName(mode));
        const int want_asid = mmu_prop->mmuM03CandidateAsid();
        TlbEntry *candidate = nullptr;
        if (key_ok && mmu_prop->mmuTargetSeqMatch(chaosLookupReqSeq)) {
            // Deterministic scan: first legal entry in table order. Legal
            // means the ONLY key predicate that differs is the ASID.
            for (auto it = table.begin(); it != table.end(); ++it) {
                TlbEntry *const e = &(*it);
                if (!e->valid || e->partial || e->global) continue;
                if (e->pfn == 0) continue;   // never a phantom frame
                // An entry whose ASID matched would have produced a normal
                // hit; M03 requires a genuinely foreign ASID.
                if (e->asid == (uint16_t)lookup_data.asn) continue;
                if (want_asid >= 0 &&
                        e->asid != (uint16_t)want_asid) continue;
                if (mmu_prop->mmuTargetN() >= 0 &&
                        (int)e->N != mmu_prop->mmuTargetN()) continue;
                if (e->ss != lookup_data.ss) continue;
                if (!e->checkRegime(lookup_data.targetRegime)) continue;
                if (useVMID(lookup_data.targetRegime) &&
                        e->vmid != lookup_data.vmid) continue;
                if (!e->matchAddress(lookup_data)) continue;
                candidate = e;
                break;
            }
        }
        // Eligibility is booked only once a legal candidate exists, so a
        // candidate-less miss never consumes the configured event ordinal.
        if (candidate && mmu_prop->mmuEligibleEvent(3)) {
            // Stable trace identity for the selected entry (same lazy
            // assignment discipline as the returned-hit path below).
            if (candidate->chaosEntryId == 0) {
                candidate->chaosEntryId = mmu_prop->mmuNewEntryId();
                if (candidate->chaosEntryGeneration == 0)
                    candidate->chaosEntryGeneration = 1;
            }
            // A warm miss may have no consumer transaction yet.
            uint64_t tid = chaosMmuTranslationId;
            if (!tid && chaosLookupReqSeq != 0) {
                tid = mmu_prop->mmuBeginConsumerTranslation(
                    chaosLookupReqSeq, lookup_data.va, mmuModeName(mode),
                    false, (uint16_t)lookup_data.asn,
                    (uint16_t)lookup_data.vmid,
                    (unsigned)lookup_data.targetRegime,
                    (unsigned)lookup_data.ss);
                if (tid) {
                    chaosMmuTranslationId = tid;
                    chaosMmuUniqueReqId = mmu_prop->mmuUniqueId(tid);
                }
            }
            const auto hexs = [](Addr v) {
                std::ostringstream os;
                os << "0x" << std::hex << v;
                return os.str();
            };
            const Addr cand_pa = candidate->pAddr(lookup_data.va);
            const uint64_t ptag = mmu_prop->mmuFaultActivate(
                "M03", "tlb_lookup_miss_false_hit", tid,
                chaosLookupReqSeq, lookup_data.va,
                {
                 {"candidate_asid",
                     std::to_string((unsigned)candidate->asid)},
                 {"candidate_entry_id",
                     std::to_string(candidate->chaosEntryId)},
                 {"candidate_generation",
                     std::to_string(candidate->chaosEntryGeneration)},
                 {"candidate_pfn", hexs(candidate->pfn)},
                 {"candidate_pa", hexs(cand_pa)},
                 {"candidate_valid", "1"},
                 {"candidate_partial", "0"},
                 {"candidate_global", "0"},
                 {"lookup_outcome", "false_hit"},
                 {"page_size_n", std::to_string((unsigned)candidate->N)},
                 {"mode", mmuModeName(mode)},
                 {"tlb_instance", tlb_inst},
                 {"asid", std::to_string((unsigned)lookup_data.asn)},
                 {"vmid", std::to_string((unsigned)lookup_data.vmid)},
                 {"regime", CHAOSPropagation::mmuRegimeName(
                     (unsigned)lookup_data.targetRegime)},
                 {"security_state", CHAOSPropagation::mmuSecurityStateName(
                     (unsigned)lookup_data.ss)},
                });
            // Return the candidate ONLY on a real one-shot activation.
            if (ptag) {
                retval = candidate;
                mmu_phase3_ptag = ptag;
            }
        }
    }

    // LSU W2 F6 event source (09 §2.1 map): TLB hit. FS-only by construction
    // — SE translates via translateSe and never reaches TLB::lookup.
    if (retval) {
        chaosLsuF6Observe(ChaOSLsuEvent::TlbHit);
    }

    DPRINTF(TLBVerbose, "Lookup %#x, asn %#x -> %s vmn 0x%x ss %s "
            "ppn %#x size: %#x pa: %#x ap:%d piindex:%d "
            "ns:%d ss:%s g:%d asid: %d "
            "xs: %d regime: %s\n",
            lookup_data.va, lookup_data.asn, retval ? "hit" : "miss",
            lookup_data.vmid, lookup_data.ss,
            retval ? retval->pfn       : 0, retval ? retval->size  : 0,
            retval ? retval->pAddr(lookup_data.va) : 0,
            retval ? retval->ap        : 0,
            retval ? retval->piindex   : 0,
            retval ? retval->ns        : 0,
            retval ? retval->ss : SecurityState::NonSecure,
            retval ? retval->global    : 0, retval ? retval->asid  : 0,
            retval ? retval->xs : 0,
            retval ? regimeToStr(retval->regime) : "None");

    // Updating stats if this was not a functional lookup
    if (!lookup_data.functional) {
        if (!retval) {
            if (mode == BaseMMU::Execute) {
                stats.instMisses++;
            } else if (mode == BaseMMU::Write) {
                stats.writeMisses++;
            } else {
                stats.readMisses++;
            }
        } else {
            if (retval->partial) {
                stats.partialHits++;
            }

            if (mode == BaseMMU::Execute) {
                stats.instHits++;
            } else if (mode == BaseMMU::Write) {
               stats.writeHits++;
            } else {
                stats.readHits++;
            }
        }
    }

    // [MMU-TRACE v2] Stable entry identity is assigned on first observed use
    // regardless of trace emission, so the M01 latch guard works even with
    // the trace disabled. Metadata only; translation behavior is unchanged.
    if (mmu_prop && retval && retval->chaosEntryId == 0) {
        retval->chaosEntryId = mmu_prop->mmuNewEntryId();
        if (retval->chaosEntryGeneration == 0)
            retval->chaosEntryGeneration = 1;
    }

    // [MMU-TRACE v2 / M01] Consumption check runs even when the trace is off:
    // the fault's lifecycle must not depend on observation. A demand lookup
    // (or a traced translation) that hits the retained identity consumes it.
    uint64_t mmu_fault_ptag = 0;
    if (mmu_prop && retval) {
        const bool demand = !lookup_data.functional && !retval->partial;
        if (chaosMmuTranslationId || demand) {
            mmu_prop->mmuM01Consume(
                tlbInstanceName(*this), lookup_data.va,
                (uint16_t)lookup_data.asn, (uint16_t)lookup_data.vmid,
                retval->N, (unsigned)retval->regime, (unsigned)retval->ss,
                retval->chaosEntryId, retval->chaosEntryGeneration,
                chaosMmuTranslationId, &mmu_fault_ptag);
        }
    }

    // [Phase 2.2 / M02] Cross-dynamic entry-lineage consumption. The join
    // is the REAL entry identity (instance + entry_id + generation) plus the
    // full architectural key; a different dynamic instruction that hits the
    // corrupted entry adopts the fault into its OWN transaction, even if the
    // original refill instruction was squashed. VA/PA equality is never the
    // join, and no tick proximity is used.
    bool mmu_lineage_consumed = false;
    if (mmu_prop && retval && !lookup_data.functional &&
            chaosLookupReqSeq != 0) {
        uint64_t lineage_tid = 0;
        const uint64_t lineage_ptag = mmu_prop->mmuM02FindLineage(
            tlbInstanceName(*this), retval->chaosEntryId,
            retval->chaosEntryGeneration, lookup_data.va,
            (uint16_t)lookup_data.asn, (uint16_t)lookup_data.vmid, retval->N,
            (unsigned)retval->regime, (unsigned)retval->ss, retval->pfn,
            chaosLookupReqSeq, mmuModeName(mode), false, &lineage_tid);
        if (lineage_ptag) {
            mmu_fault_ptag = lineage_ptag;
            mmu_lineage_consumed = true;
            if (lineage_tid) {
                chaosMmuTranslationId = lineage_tid;
                chaosMmuUniqueReqId = mmu_prop->mmuUniqueId(lineage_tid);
            }
        }
    }

    // ================= [MMU-PHASE3] M04: resident PFN substitution ========
    // [MMU-PHASE3][M04] Real-HIT fault. Replace the hit entry's pfn with a
    // VALIDATED workload-owned decoy frame. The configured
    // --mmu_m04_decoy_pfn is the ONLY decoy source for formal runs: it must
    // name a live, complete, resident translation of this stage-1 TLB chain
    // with the same N/ASID/regime/security-state/VMID and a different VA
    // page. Zero (unconfigured) or an unvalidatable PFN is a hard no-op: the
    // lookup keeps the honest clean result and an mmu_fault_unactivated event
    // states the exact reason. No entry is mutated without a validated
    // candidate and a real one-shot activation.
    //
    // The mutated entry stays resident; the fault registry is keyed by the
    // REAL entry lifetime (instance + entry id + generation), and a
    // replacement bumps the generation, so persistence ends exactly at
    // invalidation/replacement. Duplicate resident copies of the SAME
    // architectural mapping (this TLB and every reachable stage-1 layer) are
    // substituted too and each new lifetime is registered with an explicit
    // tlb_entry_lineage record. Promoted copies (multiLookup -> insert) are
    // registered in TLB::insert from the real source identity.
    // R05 (ITLB execute context) needs no special case: the itb instance is
    // the same ArmISA::TLB and reaches this same block.
    // [MMU-F1] M01 stale entries use the same persistent-entry registry as
    // M04: the entry retained by a suppressed invalidation must keep its
    // fault identity across later warm hits so the committed consumer edge
    // is traceable. The activation branch below stays M04-only.
    const bool phase3_entry_model = mmu_prop &&
        (mmu_prop->mmuFaultModelIs("M04") ||
         mmu_prop->mmuFaultModelIs("M01"));
    if (mmu_prop && retval && !lookup_data.functional &&
            !retval->partial && phase3_entry_model) {
        const std::string tlb_inst = tlbInstanceName(*this);
        // Stable identity was assigned above for every observed hit.
        const uint64_t entry_id = retval->chaosEntryId;
        const uint32_t entry_gen = retval->chaosEntryGeneration;
        // A previously corrupted entry is consumed by EVERY later hit of the
        // same real entry lifetime, including different dynamic instructions,
        // so this check is deliberately NOT gated by the target selector or
        // the target sequence.
        const uint64_t registered = entry_id
            ? mmu_prop->mmuEntryFaultPtag(tlb_inst, entry_id, entry_gen)
            : 0;
        if (registered) {
            mmu_phase3_ptag = registered;
            mmu_phase3_consume = true;
            // [MMU-F1][OBS-ONLY] A later warm hit on a registered fault
            // entry must own its own consumer transaction, otherwise its
            // LSU/response/writeback/commit rows are invisible and no
            // committed wrong-PA witness exists. The entry is already
            // mutated; fault semantics are unchanged.
            if (chaosMmuTranslationId == 0 && chaosLookupReqSeq != 0) {
                const uint64_t ctid = mmu_prop->mmuBeginConsumerTranslation(
                    chaosLookupReqSeq, lookup_data.va, mmuModeName(mode),
                    false, (uint16_t)lookup_data.asn,
                    (uint16_t)lookup_data.vmid, (unsigned)retval->regime,
                    (unsigned)retval->ss, registered);
                if (ctid) {
                    chaosMmuTranslationId = ctid;
                    chaosMmuUniqueReqId = mmu_prop->mmuUniqueId(ctid);
                }
            }
        } else if (mmu_prop->mmuFaultModelIs("M04") &&
                   mmu_prop->mmuTargetKeyMatch(
                       lookup_data.va, (uint16_t)lookup_data.asn,
                       (uint16_t)lookup_data.vmid, retval->N,
                       (unsigned)retval->regime, (unsigned)retval->ss,
                       tlb_inst.c_str(), (int)retval->lookupLevel,
                       mmuModeName(mode)) &&
                   mmu_prop->mmuTargetSeqMatch(chaosLookupReqSeq)) {
            // [MMU-PHASE3][M04] R05 is an instruction-side hit: an ITLB
            // fetch need not carry a Request dyn-inst sequence
            // (chaosLookupReqSeq == 0). The one-shot lookup-result fault is
            // still real; the consumer transaction is created only when a
            // sequence exists (the tid branch below), and the lookup event
            // remains the consumption witness.
            const Addr decoy_pfn = mmu_prop->mmuM04DecoyPfn();
            TlbEntry *cand_entry = nullptr;
            bool decoy_pfn_seen = false;
            const char *decoy_fail = nullptr;
            if (decoy_pfn == 0) {
                // Formal runs MUST configure the decoy PFN. The historical
                // "first arbitrary legal entry in table order" fallback is
                // forbidden: it is not a workload-owned decoy.
                decoy_fail = "missing_decoy_pfn";
            } else if (decoy_pfn == retval->pfn) {
                // Not a substitution (the decoy names the target frame).
                decoy_fail = "decoy_key_mismatch";
            } else {
                m04FindDecoy(*retval, decoy_pfn, cand_entry, decoy_pfn_seen);
                if (!cand_entry) {
                    decoy_fail = decoy_pfn_seen ? "decoy_key_mismatch"
                                                : "decoy_not_resident";
                }
            }
            if (decoy_fail) {
                // Honest no-op: keep the normal hit result, mutate nothing,
                // activate nothing. The exit report may also emit a generic
                // unactivated row; this specific reason is authoritative.
                if (!chaosM04DecoyNoopReported) {
                    chaosM04DecoyNoopReported = true;
                    mmu_prop->notePropEvt("mmu_fault_unactivated", {
                        {"fault_id", "0"},
                        {"fault_model", "M04"},
                        {"fault_site", "tlb_lookup_hit_pfn_subst"},
                        {"fault_reason", decoy_fail},
                        {"fault_activation_status", "not_activated"},
                        {"outcome", "not_activated"},
                        {"va", mmuHexAddr(lookup_data.va)},
                        {"old_pfn", mmuHexAddr(retval->pfn)},
                        {"decoy_pfn", mmuHexAddr(decoy_pfn)},
                        {"tlb_instance", tlb_inst},
                        {"tlb_entry_id", std::to_string(entry_id)},
                        {"entry_generation", std::to_string(entry_gen)},
                        {"page_size_n", std::to_string((unsigned)retval->N)},
                        {"mode", mmuModeName(mode)},
                        {"asid", std::to_string((unsigned)lookup_data.asn)},
                        {"vmid", std::to_string((unsigned)lookup_data.vmid)},
                        {"regime", CHAOSPropagation::mmuRegimeName(
                            (unsigned)retval->regime)},
                        {"security_state",
                            CHAOSPropagation::mmuSecurityStateName(
                                (unsigned)retval->ss)},
                        {"stage", "1"},
                        {"corr", CHAOSPropagation::CORR_NONE},
                    });
                }
            } else if (mmu_prop->mmuEligibleEvent(4)) {
                // Stable trace identity for the validated candidate (same
                // lazy-assignment discipline as the hit entry above).
                if (cand_entry->chaosEntryId == 0) {
                    cand_entry->chaosEntryId = mmu_prop->mmuNewEntryId();
                    if (cand_entry->chaosEntryGeneration == 0)
                        cand_entry->chaosEntryGeneration = 1;
                }
                // A warm hit has no miss-triggered transaction; create the
                // consumer transaction that owns this access (0 = tracing
                // off / VA outside the traced range).
                uint64_t tid = chaosMmuTranslationId;
                if (!tid && chaosLookupReqSeq != 0) {
                    tid = mmu_prop->mmuBeginConsumerTranslation(
                        chaosLookupReqSeq, lookup_data.va, mmuModeName(mode),
                        false, (uint16_t)lookup_data.asn,
                        (uint16_t)lookup_data.vmid,
                        (unsigned)retval->regime, (unsigned)retval->ss);
                    if (tid) {
                        chaosMmuTranslationId = tid;
                        chaosMmuUniqueReqId = mmu_prop->mmuUniqueId(tid);
                    }
                }
                const auto hexs = [](Addr v) {
                    std::ostringstream os;
                    os << "0x" << std::hex << v;
                    return os.str();
                };
                const Addr old_pfn = retval->pfn;
                const Addr old_pa = retval->pAddr(lookup_data.va);
                const Addr new_pa = (decoy_pfn << retval->N) |
                                    (lookup_data.va & retval->size);
                const Addr cand_va = cand_entry->vpn << cand_entry->N;
                const Addr cand_pa = cand_entry->pAddr(cand_va);
                // Required activation identity. `candidate_va` has no
                // PROP-EVT registry key (see M04_LINEAGE_FIX.md); the
                // candidate entry identity below is the join back to its own
                // lookup/insert rows, which carry the candidate VA.
                std::vector<std::pair<std::string, std::string>> kv = {
                    // Candidate provenance: this model ALWAYS uses the
                    // operator-configured decoy (never a table-order pick).
                    {"fault_field", "decoy_source=configured"},
                    {"old_pfn", hexs(old_pfn)},
                    {"new_pfn", hexs(decoy_pfn)},
                    {"old_pa", hexs(old_pa)},
                    {"new_pa", hexs(new_pa)},
                    {"tlb_instance", tlb_inst},
                    {"tlb_entry_id", std::to_string(entry_id)},
                    {"entry_generation", std::to_string(entry_gen)},
                    {"candidate_entry_id",
                        std::to_string(cand_entry->chaosEntryId)},
                    {"candidate_generation",
                        std::to_string(cand_entry->chaosEntryGeneration)},
                    {"candidate_pfn", hexs(cand_entry->pfn)},
                    {"candidate_pa", hexs(cand_pa)},
                    {"candidate_asid",
                        std::to_string((unsigned)cand_entry->asid)},
                    {"candidate_valid", "1"},
                    {"candidate_partial", "0"},
                    {"candidate_global", cand_entry->global ? "1" : "0"},
                    {"decoy_pfn", hexs(decoy_pfn)},
                    {"decoy_pa", hexs(new_pa)},
                    {"lookup_outcome", "hit_pfn_substitution"},
                    {"page_size_n", std::to_string((unsigned)retval->N)},
                    {"mode", mmuModeName(mode)},
                    {"asid", std::to_string((unsigned)lookup_data.asn)},
                    {"vmid", std::to_string((unsigned)lookup_data.vmid)},
                    {"regime", CHAOSPropagation::mmuRegimeName(
                        (unsigned)retval->regime)},
                    {"security_state", CHAOSPropagation::mmuSecurityStateName(
                        (unsigned)retval->ss)},
                    {"stage", "1"},
                };
                const uint64_t ptag = mmu_prop->mmuFaultActivate(
                    "M04", "tlb_lookup_hit_pfn_subst", tid,
                    chaosLookupReqSeq, lookup_data.va, kv);
                // Mutate ONLY on a real one-shot activation.
                if (ptag) {
                    const uint64_t act_event =
                        mmu_prop->mmuFaultActivationEventId();
                    retval->pfn = decoy_pfn;
                    retval->chaosFaultOriginSeq = chaosLookupReqSeq;
                    mmu_prop->mmuRegisterEntryFault(
                        tlb_inst, entry_id, entry_gen, ptag, act_event,
                        chaosLookupReqSeq, lookup_data.va, "M04");
                    // Propagate the SAME substitution to every duplicate
                    // resident copy of this architectural mapping, so a later
                    // hit on another layer cannot silently restore the clean
                    // translation. Each new lifetime is registered and emits
                    // a tlb_entry_lineage record.
                    m04PropagateAliasLineage(
                        lookup_data, *retval, old_pfn, decoy_pfn, ptag,
                        act_event, chaosLookupReqSeq, tlb_inst, entry_id,
                        entry_gen, mmuModeName(mode));
                    mmu_phase3_ptag = ptag;
                    mmu_phase3_consume = true;
                }
            }
        }
    }

    // ================= [MMU-PHASE3] M05: partial walk-cache consumption ====
    // [MMU-PHASE3][M05] The PTW registered a corrupted L2 partial entry under
    // its real l2_shared entry lifetime. A later lookup that HITS that exact
    // lifetime is the walk-cache consumer: the lookup event carries the fault
    // id and the generic consume witness below joins it to the registration.
    // Only partial entries are considered; the complete-entry paths stay with
    // M01/M02/M04.
    if (mmu_prop && retval && retval->partial &&
            mmu_prop->mmuFaultModelIs("M05")) {
        const uint64_t reg = mmu_prop->mmuEntryFaultPtag(
            tlbInstanceName(*this), retval->chaosEntryId,
            retval->chaosEntryGeneration);
        if (reg) {
            mmu_phase3_ptag = reg;
            mmu_phase3_consume = true;
        }
    }

    // [MMU-TRACE v1] Emit the final per-level lookup result. The entry id is
    // assigned lazily here for entries restored from a checkpoint (the id is
    // deliberately not serialized). This mutates only trace metadata.
    if (mmu_prop && mmu_lookup_id) {
        // [MMU-TRACE v1] Miss-triggered transaction: warm-hit repetitions of
        // a VA create no trace at all. The new identity is published on this
        // TLB so multiLookup propagates it to l2_shared and MMU::getTE reads
        // it back after the lookup.
        if (!retval && chaosMmuTranslationId == 0 && chaos_trace_seq != 0) {
            const uint64_t tid = mmu_prop->mmuBeginMissTranslation(
                chaos_trace_seq, lookup_data.va, mmuModeName(mode), false,
                (uint16_t)lookup_data.asn, (uint16_t)lookup_data.vmid,
                (unsigned)lookup_data.targetRegime, (unsigned)lookup_data.ss);
            if (tid) {
                chaosMmuTranslationId = tid;
                chaosMmuUniqueReqId = mmu_prop->mmuUniqueId(tid);
            }
        }
        const uint64_t mmu_lookup_event = mmu_prop->mmuNoteLookup(
            tlbInstanceName(*this), mmu_lookup_id, chaosMmuTranslationId,
            chaosMmuUniqueReqId, chaos_trace_seq, lookup_data.va,
            (uint16_t)lookup_data.asn, (uint16_t)lookup_data.vmid,
            retval != nullptr, retval ? retval->partial : false,
            retval ? retval->pfn : 0, retval ? retval->N : 0,
            retval ? retval->chaosEntryId : 0,
            retval ? retval->chaosEntryGeneration : 0,
            retval ? (unsigned)retval->lookupLevel : 0,
            (unsigned)lookup_data.targetRegime, (unsigned)lookup_data.ss,
            // [MMU-PHASE3] A Phase-3 (M03/M04) fault id rides on the lookup
            // event too; the M01 disarm hook below stays bound to
            // mmu_fault_ptag (it is itself guarded by mmuFaultModelIs("M01")).
            mmu_fault_ptag ? mmu_fault_ptag : mmu_phase3_ptag);
        if (mmu_fault_ptag)
            mmu_prop->mmuM01EmitDisarm(mmu_fault_ptag, mmu_lookup_event);
        // [MMU-F1][OBS-ONLY] Register the stale entry lifetime so the DTB
        // refill promotion and later warm hits inherit the fault id. The M01
        // fault is already consumed/disarmed here; this only makes the
        // committed consumer edge traceable.
        if (mmu_fault_ptag && retval && mmu_lookup_event &&
                retval->chaosEntryId &&
                mmu_prop->mmuFaultModelIs("M01")) {
            mmu_prop->mmuRegisterEntryFault(
                tlbInstanceName(*this), retval->chaosEntryId,
                retval->chaosEntryGeneration, mmu_fault_ptag,
                mmu_lookup_event, chaosLookupReqSeq, lookup_data.va, "M01");
        }
        // [Phase 2.2] Emit the explicit entry-consumption witness AFTER the
        // real lookup event: its parent is the lookup, and it carries BOTH
        // the origin insert/refill event ids and this lookup event id.
        if (mmu_lineage_consumed)
            mmu_prop->mmuM02NoteConsume(mmu_lookup_event);
        // [MMU-PHASE3][M04] This hit read an entry registered as an M04
        // fault. Emit its consume/reuse witness AFTER the real lookup event,
        // keyed by the real entry lifetime and joined to the lookup. Every
        // hit (origin activation lookup and later instructions alike) gets
        // its own witness; the first is the consume, later ones reuse.
        if (mmu_phase3_consume && mmu_lookup_event && retval) {
            mmu_prop->mmuNoteEntryConsume(
                mmu_prop->mmuEntryFaultConsumeCount() == 0
                    ? "fault_entry_consume" : "fault_entry_reuse",
                tlbInstanceName(*this), retval->chaosEntryId,
                retval->chaosEntryGeneration, lookup_data.va,
                (uint16_t)lookup_data.asn, (uint16_t)lookup_data.vmid,
                retval->N, (unsigned)retval->regime, (unsigned)retval->ss,
                chaos_trace_seq, mmuModeName(mode), mmu_lookup_event);
        }
        // [MMU-PHASE3][M04] Publish the real lookup event for a promoting
        // parent layer (multiLookup reads it before insert()).
        chaosMmuLastLookupEventId = mmu_lookup_event;
    }

    return retval;
}

// [MMU-PHASE3][M04] Resident-decoy scan. Deterministic table order in THIS
// instance, then down the real nextLevel() chain (stage-1 layers only). A
// matching PFN that fails the architectural-key predicates is reported as a
// key mismatch rather than "not resident" (the distinction is honest: the
// frame exists in this layer, but it is not a workload-owned alias of the
// hit's process/regime/security state).
void
TLB::m04FindDecoy(const TlbEntry &hit, Addr decoy_pfn, TlbEntry *&entry,
                  bool &pfn_seen)
{
    for (auto it = table.begin(); it != table.end(); ++it) {
        TlbEntry *const e = &(*it);
        if (e == &hit)
            continue;
        if (e->pfn != decoy_pfn)
            continue;
        pfn_seen = true;
        if (m04DecoyIsLegal(*e, hit, decoy_pfn)) {
            entry = e;
            return;
        }
    }
    TLB *const child = static_cast<TLB *>(nextLevel());
    if (child && !child->isStage2)
        child->m04FindDecoy(hit, decoy_pfn, entry, pfn_seen);
}

// [MMU-PHASE3][M04] Cross-layer lineage. Every other resident COMPLETE copy
// of the faulted architectural mapping (same VA page/N/ASID/VMID/regime/SS)
// that still carries the ORIGINAL pfn is substituted in place, registered
// under its own (instance, entry_id, generation), and reported with an
// explicit tlb_entry_lineage event. This removes the "clean duplicate masks
// the fault" hole at every stage-1 layer reachable from the hit instance.
unsigned
TLB::m04PropagateAliasLineage(const Lookup &key, const TlbEntry &hit,
                              Addr old_pfn, Addr decoy_pfn, uint64_t ptag,
                              uint64_t activation_event, uint64_t origin_seq,
                              const std::string &origin_instance,
                              uint64_t origin_entry_id,
                              uint32_t origin_generation, const char *mode)
{
    CHAOSPropagation *const prop = CHAOSPropagation::instance();
    if (!prop)
        return 0;

    unsigned count = 0;
    const std::string inst = tlbInstanceName(*this);
    for (auto it = table.begin(); it != table.end(); ++it) {
        TlbEntry *const e = &(*it);
        if (e == &hit)
            continue;
        if (!m04AliasesHit(*e, hit, old_pfn))
            continue;
        if (e->chaosEntryId == 0) {
            e->chaosEntryId = prop->mmuNewEntryId();
            if (e->chaosEntryGeneration == 0)
                e->chaosEntryGeneration = 1;
        }
        const Addr e_va = e->vpn << e->N;
        const Addr old_pa = e->pAddr(key.va);
        e->pfn = decoy_pfn;
        if (origin_seq)
            e->chaosFaultOriginSeq = origin_seq;
        const Addr new_pa = e->pAddr(key.va);
        prop->mmuRegisterEntryFault(
            inst, e->chaosEntryId, e->chaosEntryGeneration, ptag,
            activation_event,
            e->chaosFaultOriginSeq ? e->chaosFaultOriginSeq : origin_seq,
            e_va, "M04");
        if (prop->mmuTraceEnabled()) {
            std::ostringstream lineage;
            lineage << origin_instance << ':' << origin_entry_id << ':'
                    << origin_generation << ';'
                    << inst << ':' << e->chaosEntryId << ':'
                    << e->chaosEntryGeneration;
            prop->notePropEvt("tlb_entry_lineage", {
                {"fault_id", std::to_string(ptag)},
                {"fault_model", "M04"},
                {"fault_field", "corrupted_entry_alias"},
                {"fault_reason", "pfn_substitution_propagated"},
                {"lineage_state", "alias_mutated"},
                {"lineage_fault_id", std::to_string(ptag)},
                {"lineage_entries", lineage.str()},
                {"tlb_instance", inst},
                {"tlb_entry_id", std::to_string(e->chaosEntryId)},
                {"entry_generation",
                    std::to_string(e->chaosEntryGeneration)},
                {"retained_entry_id", std::to_string(origin_entry_id)},
                {"retained_entry_generation",
                    std::to_string(origin_generation)},
                {"origin_event_id", std::to_string(activation_event)},
                {"activation_event_id", std::to_string(activation_event)},
                {"source_event_id", std::to_string(activation_event)},
                {"va", mmuHexAddr(e_va)},
                {"asid", std::to_string((unsigned)e->asid)},
                {"vmid", std::to_string((unsigned)e->vmid)},
                {"page_size_n", std::to_string((unsigned)e->N)},
                {"regime", CHAOSPropagation::mmuRegimeName(
                    (unsigned)e->regime)},
                {"security_state", CHAOSPropagation::mmuSecurityStateName(
                    (unsigned)e->ss)},
                {"mode", mode ? mode : ""},
                {"old_pfn", mmuHexAddr(old_pfn)},
                {"new_pfn", mmuHexAddr(decoy_pfn)},
                {"pfn", mmuHexAddr(decoy_pfn)},
                {"old_pa", mmuHexAddr(old_pa)},
                {"new_pa", mmuHexAddr(new_pa)},
                {"corr", CHAOSPropagation::CORR_ENTRY_LINEAGE},
            });
        }
        ++count;
    }

    TLB *const child = static_cast<TLB *>(nextLevel());
    if (child && !child->isStage2) {
        count += child->m04PropagateAliasLineage(
            key, hit, old_pfn, decoy_pfn, ptag, activation_event, origin_seq,
            origin_instance, origin_entry_id, origin_generation, mode);
    }
    return count;
}

TlbEntry*
TLB::multiLookup(const Lookup &lookup_data)
{
    TlbEntry* te = lookup(lookup_data);

    if (te) {
        checkPromotion(te, lookup_data.mode);
    } else {
        if (auto tlb = static_cast<TLB*>(nextLevel())) {
            // [MMU-TRACE v1] Propagate the in-flight translation identity to
            // the next-level TLB (l2_shared); the context is otherwise only
            // set on the L1 TLB by MMU::getTE.
            // [Phase 2.2] Also propagate the Request seq and then CLEAR the
            // child scratch context. Leaving it behind made a later walker
            // mmu->insert() inherit a stale younger transaction (measured:
            // l2_shared insert tlb_entry_insert attributed to a different
            // dynamic instruction with fault_id=0).
            tlb->chaosMmuTranslationId = chaosMmuTranslationId;
            tlb->chaosMmuUniqueReqId = chaosMmuUniqueReqId;
            tlb->chaosLookupReqSeq = chaosLookupReqSeq;
            tlb->chaosLookupReqSize = chaosLookupReqSize;
            tlb->chaosLookupSyntheticSeq = chaosLookupSyntheticSeq;
            te = tlb->multiLookup(lookup_data);
            if (tlb->chaosMmuTranslationId) {
                chaosMmuTranslationId = tlb->chaosMmuTranslationId;
                chaosMmuUniqueReqId = tlb->chaosMmuUniqueReqId;
            }
            tlb->chaosMmuTranslationId = 0;
            tlb->chaosMmuUniqueReqId = 0;
            tlb->chaosLookupReqSeq = 0;
            tlb->chaosLookupReqSize = 0;
            tlb->chaosLookupSyntheticSeq = 0;
            if (te && !lookup_data.functional &&
                (!te->partial || partialLevels[te->lookupLevel])) {
                // Insert entry only if this is not a functional
                // lookup and if the translation is complete (unless this
                // TLB caches partial translations)
                //
                // [Phase 2.2] The promoted entry is a COPY of the child
                // entry; publish that source identity so an M02 lineage is
                // propagated to this layer by exact entry identity.
                CHAOSPropagation *const prop =
                    CHAOSPropagation::instance();
                if (prop)
                    prop->mmuSetPromotionSource(tlbInstanceName(*tlb),
                                                te->chaosEntryId,
                                                te->chaosEntryGeneration);
                // [MMU-PHASE3][M04] Publish the real source identity + real
                // source lookup event to this TLB's insert, so a promoted
                // copy of an M04-substituted entry inherits the fault under
                // its NEW lifetime instead of starting clean. Only when the
                // source entry actually lives in the DIRECT child layer —
                // otherwise the instance label would be wrong and the
                // registry lookup would have to guess (it must not).
                bool src_in_child = false;
                for (auto cit = tlb->table.begin();
                        cit != tlb->table.end(); ++cit) {
                    if (&(*cit) == te) {
                        src_in_child = true;
                        break;
                    }
                }
                if (src_in_child) {
                    chaosPromoteSrcInstance = tlbInstanceName(*tlb);
                    chaosPromoteSrcLookupEvent =
                        tlb->chaosMmuLastLookupEventId;
                }
                insert(lookup_data, *te);
                chaosPromoteSrcInstance.clear();
                chaosPromoteSrcLookupEvent = 0;
                if (prop)
                    prop->mmuClearPromotionSource();
            }
        }
    }

    return te;
}

void
TLB::checkPromotion(TlbEntry *entry, BaseMMU::Mode mode)
{
    TypeTLB acc_type = (mode == BaseMMU::Execute) ?
       TypeTLB::instruction : TypeTLB::data;

    // Hitting an instruction TLB entry on a data access or
    // a data TLB entry on an instruction access:
    // promoting the entry to unified
    if (!(entry->type & acc_type))
       entry->type = TypeTLB::unified;
}

// insert a new TLB entry
void
TLB::insert(const Lookup &lookup_data, TlbEntry &entry)
{
    TlbEntry *victim = table.findVictim(lookup_data);

    // [MMU-TRACE v1] Stable slot identity survives the entry overwrite; the
    // generation increments on every reuse (and on every invalidation).
    CHAOSPropagation *const mmu_prop = CHAOSPropagation::instance();
    const bool mmu_trace = mmu_prop && mmu_prop->mmuTraceEnabled();
    uint64_t entry_id = victim->chaosEntryId;
    uint32_t entry_gen = victim->chaosEntryGeneration;
    // [Phase 2.2] Victim lifetime being replaced (before the generation bump).
    const uint64_t prev_entry_id = victim->chaosEntryId;
    const uint32_t prev_entry_gen = victim->chaosEntryGeneration;
    if (mmu_prop) {
        // Identity is maintained even with the trace disabled (the M01 latch
        // guard needs it); emission below still requires the trace.
        if (entry_id == 0)
            entry_id = mmu_prop->mmuNewEntryId();
        ++entry_gen;
    }

    *victim = entry;
    if (mmu_prop) {
        victim->chaosEntryId = entry_id;
        victim->chaosEntryGeneration = entry_gen;
    }

    table.insertEntry(lookup_data, victim);

    table.invalidatePrev(victim);

    observedPageSizes.insert(entry.N);
    stats.inserts++;

    uint64_t ins_event = 0;
    if (mmu_trace) {
        // [Phase 2.2] A walker-driven insert has an EXPLICIT published
        // context (translation + walk). That context is authoritative and
        // must win over any lookup identity left on this TLB — the stale
        // l2_shared value previously misattributed the insert to a younger
        // dynamic instruction. Only a promotion insert (no walk context)
        // uses the propagated lookup identity.
        const bool have_walk_ctx = mmu_prop->mmuInsertWalkId() != 0 ||
                                   mmu_prop->mmuInsertTid() != 0;
        const uint64_t ins_tid = have_walk_ctx
            ? mmu_prop->mmuInsertTid() : chaosMmuTranslationId;
        const uint64_t ins_uid = have_walk_ctx
            ? mmu_prop->mmuInsertUid() : chaosMmuUniqueReqId;
        const uint64_t ins_walk = mmu_prop->mmuInsertWalkId();
        ins_event = mmu_prop->mmuNoteEntryInsert(
            tlbInstanceName(*this), entry_id, entry_gen, lookup_data.va,
            (uint16_t)lookup_data.asn, (uint16_t)lookup_data.vmid, entry.pfn,
            entry.N, entry.partial, (unsigned)entry.lookupLevel,
            (unsigned)entry.regime, (unsigned)entry.ss, ins_tid, ins_uid,
            ins_walk, prev_entry_id, prev_entry_gen);
    }

    // [MMU-PHASE3][M04] Promotion lineage. multiLookup set the SOURCE
    // instance around this insert. If that source lifetime is registered as
    // an M04 fault, the promoted copy (which already carries the substituted
    // pfn and the origin seq via TlbEntry::chaosFaultOriginSeq) inherits the
    // SAME fault id under its NEW (instance, entry_id, generation), and the
    // cross-layer copy is recorded explicitly. Keyed strictly by the real
    // source identity, never by VA/PA equality.
    if (mmu_prop && !chaosPromoteSrcInstance.empty() &&
            entry.chaosEntryId != 0 && mmu_prop->mmuFaultModelIs("M04")) {
        const uint64_t src_ptag = mmu_prop->mmuEntryFaultPtag(
            chaosPromoteSrcInstance, entry.chaosEntryId,
            entry.chaosEntryGeneration);
        if (src_ptag && entry.valid && !entry.partial && entry.pfn != 0) {
            const uint64_t act_event =
                src_ptag == mmu_prop->mmuActiveFaultPtag()
                    ? mmu_prop->mmuFaultActivationEventId() : 0;
            const Addr src_va = entry.vpn << entry.N;
            const uint64_t src_origin_seq = entry.chaosFaultOriginSeq
                ? entry.chaosFaultOriginSeq : chaosLookupReqSeq;
            // Keep the origin seq on the NEW lifetime too (a later lineage
            // copy of this promoted entry must not lose the real origin).
            victim->chaosFaultOriginSeq = src_origin_seq;
            mmu_prop->mmuRegisterEntryFault(
                tlbInstanceName(*this), entry_id, entry_gen, src_ptag,
                act_event, src_origin_seq, src_va, "M04");
            if (mmu_trace) {
                // Old -> new identity, both endpoints named explicitly. The
                // registry has no `retained_tlb_instance` column, so the old
                // instance travels in `lineage_entries` (and the old id/gen
                // in retained_entry_id/generation); see M04_LINEAGE_FIX.md.
                std::ostringstream lineage;
                lineage << chaosPromoteSrcInstance << ':'
                        << entry.chaosEntryId << ':'
                        << entry.chaosEntryGeneration << ';'
                        << tlbInstanceName(*this) << ':' << entry_id << ':'
                        << entry_gen;
                mmu_prop->notePropEvt("tlb_entry_lineage", {
                    {"fault_id", std::to_string(src_ptag)},
                    {"fault_model", "M04"},
                    {"fault_field", "corrupted_entry_promoted"},
                    {"fault_reason", "tlb_layer_promotion"},
                    {"lineage_state", "promoted"},
                    {"lineage_fault_id", std::to_string(src_ptag)},
                    {"lineage_entries", lineage.str()},
                    {"tlb_instance", tlbInstanceName(*this)},
                    {"tlb_entry_id", std::to_string(entry_id)},
                    {"entry_generation", std::to_string(entry_gen)},
                    {"retained_entry_id",
                        std::to_string(entry.chaosEntryId)},
                    {"retained_entry_generation",
                        std::to_string(entry.chaosEntryGeneration)},
                    {"origin_event_id", std::to_string(act_event)},
                    {"activation_event_id", std::to_string(act_event)},
                    {"source_event_id", std::to_string(act_event)},
                    {"entry_insert_event_id", std::to_string(ins_event)},
                    {"lookup_event_id",
                        std::to_string(chaosPromoteSrcLookupEvent)},
                    {"va", mmuHexAddr(src_va)},
                    {"asid", std::to_string((unsigned)entry.asid)},
                    {"vmid", std::to_string((unsigned)entry.vmid)},
                    {"page_size_n", std::to_string((unsigned)entry.N)},
                    {"regime", CHAOSPropagation::mmuRegimeName(
                        (unsigned)entry.regime)},
                    {"security_state",
                        CHAOSPropagation::mmuSecurityStateName(
                            (unsigned)entry.ss)},
                    {"mode", "promotion"},
                    {"old_pfn", mmuHexAddr(entry.pfn)},
                    {"new_pfn", mmuHexAddr(entry.pfn)},
                    {"pfn", mmuHexAddr(entry.pfn)},
                    {"corr", CHAOSPropagation::CORR_ENTRY_LINEAGE},
                });
            }
        }
    }

    // [MMU-F1][OBS-ONLY] M01 promotion: a stale entry promoted across TLB
    // layers keeps the fault identity under its NEW lifetime, exactly like
    // M04. No lineage event is emitted (M01's witness is the stale-entry
    // consumption + the committed refill); this only preserves the id.
    if (mmu_prop && !chaosPromoteSrcInstance.empty() &&
            entry.chaosEntryId != 0 && mmu_prop->mmuFaultModelIs("M01")) {
        const uint64_t src_ptag = mmu_prop->mmuEntryFaultPtag(
            chaosPromoteSrcInstance, entry.chaosEntryId,
            entry.chaosEntryGeneration);
        if (src_ptag && entry.valid && !entry.partial && entry.pfn != 0) {
            const Addr src_va = entry.vpn << entry.N;
            const uint64_t src_origin_seq = entry.chaosFaultOriginSeq
                ? entry.chaosFaultOriginSeq : chaosLookupReqSeq;
            victim->chaosFaultOriginSeq = src_origin_seq;
            mmu_prop->mmuRegisterEntryFault(
                tlbInstanceName(*this), entry_id, entry_gen, src_ptag, 0,
                src_origin_seq, src_va, "M01");
        }
    }

    if (lookup_data.mode == BaseMMU::Execute) {
        ppInstRefills->notify(1);
    } else {
        ppDataRefills->notify(1);
    }
}

void
TLB::multiInsert(const Lookup &lookup, TlbEntry &entry)
{
    // Insert a partial translation only if the TLB is configured
    // as a walk cache
    if (!entry.partial || partialLevels[entry.lookupLevel]) {
        insert(lookup, entry);
    }

    if (auto next_level = static_cast<TLB*>(nextLevel())) {
        next_level->multiInsert(lookup, entry);
    }
}

void
TLB::printTlb() const
{
    DPRINTF(TLB, "Current TLB contents:\n");
    for (auto& te : table) {
        if (te.valid)
            DPRINTF(TLB, " *  %s\n", te.print());
    }
}

void
TLB::flushAll()
{
    DPRINTF(TLB, "Flushing all TLB entries\n");
    for (auto& te : table) {
        if (te.valid) {
            DPRINTF(TLB, " -  %s\n", te.print());
            // [Phase 2.2] Close any corrupted-entry lineage of this slot.
            if (CHAOSPropagation *const prop =
                    CHAOSPropagation::instance()) {
                prop->mmuEndEntryLineage(tlbInstanceName(*this),
                                          te.chaosEntryId,
                                          te.chaosEntryGeneration,
                                          "flush_all");
            }
            table.invalidate(&te);
            stats.flushedEntries++;
        }
    }

    table.invalidatePrev();

    stats.flushTlb++;
    observedPageSizes.clear();
}

void
TLB::flush(const TLBIOp& tlbi_op)
{
    CHAOSPropagation *const mmu_prop = CHAOSPropagation::instance();
    const bool mmu_trace = mmu_prop && mmu_prop->mmuTraceEnabled() &&
                           chaosTlbiId != 0;
    const std::string mmu_instance = tlbInstanceName(*this);
    const std::string mmu_op = tlbiOpName(tlbi_op);

    bool valid_entry = false;
    for (auto& te : table) {
        if (tlbi_op.match(&te, vmid)) {
            DPRINTF(TLB, " -  %s\n", te.print());
            const Addr te_va = te.vpn << te.N;
            // [MMU-TRACE v2 / M01] One-shot invalidation-suppression
            // decision for the exact complete l2_shared entry. Strict no-op
            // unless mmuFaultModel=M01; dtb/itb are never considered.
            CHAOSPropagation::MmuM01Decision dec;
            if (mmu_prop) {
                dec = mmu_prop->mmuM01OnTlbiMatch(
                    mmu_instance, te_va, te.asid, (uint16_t)te.vmid, te.N,
                    te.valid, te.partial, (unsigned)te.regime,
                    (unsigned)te.ss, chaosTlbiId, te.chaosEntryId,
                    te.chaosEntryGeneration, mmu_op.c_str());
            }
            uint64_t match_event = 0;
            if (mmu_trace) {
                match_event = mmu_prop->mmuNoteTlbiMatch(
                    chaosTlbiId, mmu_instance, mmu_op.c_str(),
                    te.chaosEntryId, te.chaosEntryGeneration, te_va, te.asid,
                    (uint16_t)te.vmid, te.N, (unsigned)te.regime,
                    (unsigned)te.ss, dec.suppress, dec.fault_id,
                    dec.suppress
                        ? (dec.first_arm ? "first_arm" : "armed_window")
                        : nullptr);
            }
            if (dec.suppress) {
                // [MMU-TRACE v3] Causal order is
                //   tlbi_issue -> tlbi_match -> mmu_fault_arm
                //              -> tlbi_suppressed
                // The arm event is emitted only now, after the match event
                // exists, and its parent is that match. The first
                // suppression is a child of the arm; later suppressions of
                // the same retained lifetime are children of their own match.
                uint64_t arm_event = 0;
                if (mmu_prop && dec.first_arm && match_event)
                    arm_event = mmu_prop->mmuM01EmitArm(match_event);
                // The retained entry keeps its identity and generation; the
                // normal invalidation (and its generation bump) is skipped
                // for THIS entry only.
                if (mmu_prop) {
                    mmu_prop->mmuM01NoteSuppressed(
                        mmu_instance, te_va, te.asid, (uint16_t)te.vmid, te.N,
                        (unsigned)te.regime, (unsigned)te.ss, chaosTlbiId,
                        te.chaosEntryId, te.chaosEntryGeneration,
                        mmu_op.c_str(),
                        arm_event ? arm_event : match_event);
                }
            } else {
                const uint32_t gen_before = te.chaosEntryGeneration;
                table.invalidate(&te);

                table.invalidatePrev(&te);

                if (mmu_trace) {
                    const uint64_t inv_event =
                        mmu_prop->mmuNoteTlbiInvalidate(
                            chaosTlbiId, mmu_instance, mmu_op.c_str(),
                            te.chaosEntryId, gen_before,
                            te.chaosEntryGeneration, te_va, te.asid,
                            (uint16_t)te.vmid, (unsigned)te.regime,
                            (unsigned)te.ss);
                    // [Phase 2.2] A real invalidation ends the corrupted
                    // entry lifetime: later generations of the same slot can
                    // never inherit the fault.
                    mmu_prop->mmuEndEntryLineage(
                        mmu_instance, te.chaosEntryId, gen_before,
                        "tlbi_invalidate", inv_event);
                }

                stats.flushedEntries++;
            }
        }
        valid_entry = valid_entry || te.valid;
    }

    stats.flushTlb++;
    if (!valid_entry)
        observedPageSizes.clear();
}

void
TLB::takeOverFrom(BaseTLB *_otlb)
{
}

TLB::TlbStats::TlbStats(TLB &parent)
  : statistics::Group(&parent), tlb(parent),
    ADD_STAT(partialHits, statistics::units::Count::get(),
             "partial translation hits"),
    ADD_STAT(instHits, statistics::units::Count::get(), "Inst hits"),
    ADD_STAT(instMisses, statistics::units::Count::get(), "Inst misses"),
    ADD_STAT(readHits, statistics::units::Count::get(), "Read hits"),
    ADD_STAT(readMisses, statistics::units::Count::get(),  "Read misses"),
    ADD_STAT(writeHits, statistics::units::Count::get(), "Write hits"),
    ADD_STAT(writeMisses, statistics::units::Count::get(), "Write misses"),
    ADD_STAT(inserts, statistics::units::Count::get(),
             "Number of times an entry is inserted into the TLB"),
    ADD_STAT(flushTlb, statistics::units::Count::get(),
             "Number of times a TLB invalidation was requested"),
    ADD_STAT(flushedEntries, statistics::units::Count::get(),
             "Number of entries that have been flushed from TLB"),
    ADD_STAT(readAccesses, statistics::units::Count::get(), "Read accesses",
             readHits + readMisses),
    ADD_STAT(writeAccesses, statistics::units::Count::get(), "Write accesses",
             writeHits + writeMisses),
    ADD_STAT(instAccesses, statistics::units::Count::get(), "Inst accesses",
             instHits + instMisses),
    ADD_STAT(hits, statistics::units::Count::get(),
             "Total TLB (inst and data) hits",
             readHits + writeHits + instHits),
    ADD_STAT(misses, statistics::units::Count::get(),
             "Total TLB (inst and data) misses",
             readMisses + writeMisses + instMisses),
    ADD_STAT(accesses, statistics::units::Count::get(),
             "Total TLB (inst and data) accesses",
             readAccesses + writeAccesses + instAccesses)
{
    // If this is a pure Data TLB, mark the instruction
    // stats as nozero, so that they won't make it in
    // into the final stats file
    if (tlb.type() == TypeTLB::data) {
        instHits.flags(statistics::nozero);
        instMisses.flags(statistics::nozero);

        instAccesses.flags(statistics::nozero);
    }

    // If this is a pure Instruction TLB, mark the data
    // stats as nozero, so that they won't make it in
    // into the final stats file
    if (tlb.type() & TypeTLB::instruction) {
        readHits.flags(statistics::nozero);
        readMisses.flags(statistics::nozero);
        writeHits.flags(statistics::nozero);
        writeMisses.flags(statistics::nozero);

        readAccesses.flags(statistics::nozero);
        writeAccesses.flags(statistics::nozero);
    }

    partialHits.flags(statistics::nozero);
}

void
TLB::regProbePoints()
{
    ppInstRefills.reset(
        new probing::PMU(getProbeManager(), "InstRefills"));

    ppDataRefills.reset(
        new probing::PMU(getProbeManager(), "DataRefills"));
}

Port *
TLB::getTableWalkerPort()
{
    return &tableWalker->getTableWalkerPort();
}

} // namespace gem5
