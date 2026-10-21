/*
 * Copyright (c) 2004-2006 The Regents of The University of Michigan
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

#include "base/intmath.hh"
#include "base/logging.hh"
#include "base/trace.hh"
#include "cpu/o3/store_set.hh"
#include "cpu/o3/chaos_lsu_trigger.hh"  // LSU W5 S10 StoreSet corruption
// [MDSPEC][R4-5.7] S10 hooks (chaosS10* globals; StoreSet has no CPU or
// injector pointer — the S10-armed CHAOSLSQFwd self-registers them).
#include "cpu/o3/CHAOSLSQFwd/CHAOSLSQFwd.hh"
#include "debug/StoreSet.hh"
#include "mem/cache/tags/indexing_policies/base.hh"
#include "mem/cache/replacement_policies/base.hh"

namespace gem5
{

namespace o3
{

StoreSet::StoreSet(std::string_view name_, uint64_t clear_period,
                   size_t _SSIT_entries, int _SSIT_assoc,
                   replacement_policy::Base *_replPolicy,
                   BaseIndexingPolicy *_indexingPolicy, int _LFST_size)
  : Named(name_),
    SSIT("SSIT", _SSIT_entries, _SSIT_assoc,
	 _replPolicy, _indexingPolicy,
	 SSITEntry(genTagExtractor(_indexingPolicy))),
    clearPeriod(clear_period), SSITSize(_SSIT_entries),
    LFSTSize(_LFST_size)
{
    DPRINTF(StoreSet, "StoreSet: Creating store set object.\n");
    DPRINTF(StoreSet, "StoreSet: SSIT size: %i, LFST size: %i.\n",
            SSITSize, LFSTSize);

    if (!isPowerOf2(SSITSize)) {
        fatal("Invalid SSIT size!\n");
    }

    if (!isPowerOf2(LFSTSize)) {
        fatal("Invalid LFST size!\n");
    }

    LFST.resize(LFSTSize);

    validLFST.resize(LFSTSize);

    for (int i = 0; i < LFSTSize; ++i) {
        validLFST[i] = false;
        LFST[i] = 0;
    }

    memOpsPred = 0;
}

StoreSet::~StoreSet()
{
}

void
StoreSet::init(uint64_t clear_period, size_t _SSIT_entries,
               int _SSIT_assoc, replacement_policy::Base *_replPolicy,
               BaseIndexingPolicy *_indexingPolicy, int _LFST_size)
{
    SSITSize = _SSIT_entries;
    LFSTSize = _LFST_size;
    clearPeriod = clear_period;

    DPRINTF(StoreSet, "StoreSet: Creating store set object.\n");
    DPRINTF(StoreSet, "StoreSet: SSIT size: %i, LFST size: %i.\n",
            SSITSize, LFSTSize);

    SSIT.init(SSITSize, _SSIT_assoc, _replPolicy, _indexingPolicy,
	      SSITEntry(genTagExtractor(_indexingPolicy)));

    LFST.resize(LFSTSize);

    validLFST.resize(LFSTSize);

    for (int i = 0; i < LFSTSize; ++i) {
        validLFST[i] = false;
        LFST[i] = 0;
    }

    memOpsPred = 0;
}


void
StoreSet::violation(Addr store_PC, Addr load_PC)
{
    auto ld_entry = SSIT.findEntry({load_PC});
    auto st_entry = SSIT.findEntry({store_PC});

    bool valid_load_SSID  = ld_entry && ld_entry->isValid();
    bool valid_store_SSID = st_entry && st_entry->isValid();

    // [MDSPEC][R4-5.7] S10 hook (1/3): the TOP of every training event is
    // the ATTEMPT stream (cap + onAttempt live in the injector callback),
    // and — when load_PC is a corrupted S10 entry — the ssit_violation
    // observation (the missed-dependence manifestation, cap-independent).
    // Null (every non-S10 run): one branch, byte-identical behavior.
    if (chaosS10Violation)
        chaosS10Violation(store_PC, load_PC,
                          valid_load_SSID ? ld_entry->getSSID() : 0,
                          valid_load_SSID);

    if (!valid_load_SSID && !valid_store_SSID) {
        // Calculate a new SSID here.
        SSID new_set = calcSSID(load_PC);

        // LSU W5 S10: StoreSet SSID corruption — event-source observation.
        // [MDSPEC][R4-5.7] HISTORICAL NOTE, kept deliberately: this
        // count-only chaosLsuF6Observe (commit 7af6eed4) predates the S10
        // landing and conflates SSIT-training events into the SqForward
        // F6 supply counter (the true W1 SqForward source is the
        // lsq_unit.cc forward branch). Removing it would change the event
        // supply of already-landed F6 cells — out of scope here; recorded
        // in the R4-5.7 report. The INJECTION itself is the S10 hook
        // below (the W5 comment's claimed XOR corruption never existed —
        // the "event source only" blocker this landing lifts).
        chaosLsuF6Observe(ChaOSLsuEvent::SqForward);

        // [MDSPEC][R4-5.7] S10 hook (2/3): SSIT-ID 换值 in the new-SSID
        // assignment arm. The LOAD's freshly assigned SSID may be
        // substituted with ANOTHER LEGAL live store-set ID (workbook 07
        // 实施细则: candidates from the current run, no random bit
        // strings); the STORE entry keeps the true SSID, so the trained
        // pair splits and the load aliases the target store set. The
        // lazy scan enumerates the live SSIDs (valid SSIT entries only —
        // free/idle SSIDs are not candidates by construction).
        SSID load_ssid = new_set;
        if (chaosS10SsidSubst) {
            uint64_t subst = new_set;
            if (chaosS10SsidSubst(store_PC, load_PC, new_set,
                                  [this](std::vector<uint64_t> &out) {
                                      for (const auto &e : SSIT)
                                          if (e.isValid())
                                              out.push_back(e.getSSID());
                                  }, &subst)) {
                // Legal by construction (a live SSIT SSID is < LFSTSize);
                // the assert keeps that contract explicit.
                assert(subst < (uint64_t)LFSTSize);
                load_ssid = subst;
            }
        }

        assert(new_set < LFSTSize);

        SSITEntry *ld_entry = SSIT.findVictim({load_PC});
        ld_entry->setSSID(load_ssid);
        SSIT.insertEntry({load_PC}, ld_entry);

        SSITEntry *st_entry = SSIT.findVictim({store_PC});
        st_entry->setSSID(new_set);
        SSIT.insertEntry({store_PC}, st_entry);

        DPRINTF(StoreSet, "StoreSet: Neither load nor store had a valid "
                "storeset, creating a new one: %i for load %#x, store %#x\n",
                new_set, load_PC, store_PC);
    } else if (valid_load_SSID && !valid_store_SSID) {
        SSID load_SSID = ld_entry->getSSID();
        SSITEntry *st_entry = SSIT.findVictim({store_PC});
        st_entry->setSSID(load_SSID);
        SSIT.insertEntry({store_PC}, st_entry);

        assert(load_SSID < LFSTSize);

        DPRINTF(StoreSet, "StoreSet: Load had a valid store set.  Adding "
                "store to that set: %i for load %#x, store %#x\n",
                load_SSID, load_PC, store_PC);
    } else if (!valid_load_SSID && valid_store_SSID) {
        SSID store_SSID = st_entry->getSSID();
        SSITEntry *ld_entry = SSIT.findVictim({load_PC});
        ld_entry->setSSID(store_SSID);
        SSIT.insertEntry({load_PC}, ld_entry);

        DPRINTF(StoreSet, "StoreSet: Store had a valid store set: %i for "
                "load %#x, store %#x\n",
                store_SSID, load_PC, store_PC);
    } else {
        SSID load_SSID = ld_entry->getSSID();
        SSID store_SSID = st_entry->getSSID();

        assert(load_SSID < LFSTSize && store_SSID < LFSTSize);

        // The store set with the lower number wins
        if (store_SSID > load_SSID) {
            st_entry->setSSID(load_SSID);

            DPRINTF(StoreSet, "StoreSet: Load had smaller store set: %i; "
                    "for load %#x, store %#x\n",
                    load_SSID, load_PC, store_PC);
        } else {
            ld_entry->setSSID(store_SSID);

            DPRINTF(StoreSet, "StoreSet: Store had smaller store set: %i; "
                    "for load %#x, store %#x\n",
                    store_SSID, load_PC, store_PC);
        }
    }
}

void
StoreSet::checkClear()
{
    memOpsPred++;
    if (memOpsPred > clearPeriod) {
        DPRINTF(StoreSet, "Wiping predictor state beacuse %d ld/st executed\n",
                clearPeriod);
        memOpsPred = 0;
        clear();
    }
}

void
StoreSet::insertLoad(Addr load_PC, InstSeqNum load_seq_num)
{
    checkClear();
    // Does nothing.
    return;
}

void
StoreSet::insertStore(Addr store_PC, InstSeqNum store_seq_num, ThreadID tid)
{
    auto st_entry = SSIT.findEntry({store_PC});

    bool valid_entry = st_entry && st_entry->isValid();

    int store_SSID;

    checkClear();

    if (!valid_entry) {
        // Do nothing if there's no valid entry.
        return;
    } else {
        store_SSID = st_entry->getSSID();

        assert(store_SSID < LFSTSize);

        // Update the last store that was fetched with the current one.
        LFST[store_SSID] = store_seq_num;

        validLFST[store_SSID] = 1;

        storeList[store_seq_num] = store_SSID;

        DPRINTF(StoreSet, "Store %#x updated the LFST, SSID: %i\n",
                store_PC, store_SSID);
    }
}

InstSeqNum
StoreSet::checkInst(Addr PC)
{
    auto entry = SSIT.findEntry({PC});
    bool valid_ssit = entry && entry->isValid();

    int inst_SSID;

    if (!valid_ssit) {
        DPRINTF(StoreSet, "Inst %#x has no SSID\n", PC);

        // Return 0 if there's no valid entry.
        return 0;
    } else {
        inst_SSID = entry->getSSID();

        assert(inst_SSID < LFSTSize);

        // The prediction this consult returns (0 = no dependency).
        InstSeqNum dep = validLFST[inst_SSID] ? LFST[inst_SSID] : 0;

        // [MDSPEC][R4-5.7] S10 hook (3/3): consumer observation. When PC
        // is a corrupted S10 entry, the consult READ the corrupted SSIT
        // mapping — emit ssit_consult with the counterfactual prediction
        // (what the TRUE SSID's LFST slot would have returned; LFST is
        // private to StoreSet, so the counterfactual is computed HERE and
        // handed to the injector alongside the actual). Null (every
        // non-S10 run): no work.
        if (chaosS10CorruptedPc && chaosS10Consult) {
            uint64_t true_ssid = 0;
            if (chaosS10CorruptedPc(PC, &true_ssid)) {
                const uint64_t counter_dep =
                    (true_ssid < (uint64_t)LFSTSize &&
                     validLFST[true_ssid])
                        ? (uint64_t)LFST[true_ssid] : 0;
                chaosS10Consult(PC, (uint64_t)inst_SSID, (uint64_t)dep,
                                counter_dep);
            }
        }

        if (!validLFST[inst_SSID]) {

            DPRINTF(StoreSet, "Inst %#x with SSID %i had no "
                    "dependency\n", PC, inst_SSID);

            return 0;
        } else {
            DPRINTF(StoreSet, "Inst %#x with SSID %i had LFST "
                    "inum of %i\n", PC, inst_SSID, LFST[inst_SSID]);

            return dep;
        }
    }
}

void
StoreSet::issued(Addr issued_PC, InstSeqNum issued_seq_num, bool is_store)
{
    // This only is updated upon a store being issued.
    if (!is_store) {
        return;
    }

    auto entry = SSIT.findEntry({issued_PC});
    bool valid_ssit = entry && entry->isValid();

    int store_SSID;

    SeqNumMapIt store_list_it = storeList.find(issued_seq_num);

    if (store_list_it != storeList.end()) {
        storeList.erase(store_list_it);
    }

    // Make sure the SSIT still has a valid entry for the issued store.
    if (!valid_ssit) {
        return;
    }

    store_SSID = entry->getSSID();

    assert(store_SSID < LFSTSize);

    // If the last fetched store in the store set refers to the store that
    // was just issued, then invalidate the entry.
    if (validLFST[store_SSID] && LFST[store_SSID] == issued_seq_num) {
        DPRINTF(StoreSet, "StoreSet: store invalidated itself in LFST.\n");
        validLFST[store_SSID] = false;
    }
}

void
StoreSet::squash(InstSeqNum squashed_num, ThreadID tid)
{
    DPRINTF(StoreSet, "StoreSet: Squashing until inum %i\n",
            squashed_num);

    int idx;
    SeqNumMapIt store_list_it = storeList.begin();

    //@todo:Fix to only delete from correct thread
    while (!storeList.empty()) {
        idx = (*store_list_it).second;

        if ((*store_list_it).first <= squashed_num) {
            break;
        }

        bool younger = LFST[idx] > squashed_num;

        if (validLFST[idx] && younger) {
            DPRINTF(StoreSet, "Squashed [sn:%lli]\n", LFST[idx]);
            validLFST[idx] = false;

            storeList.erase(store_list_it++);
        } else if (!validLFST[idx] && younger) {
            storeList.erase(store_list_it++);
        }
    }
}

void
StoreSet::clear()
{
    SSIT.clear();

    for (int i = 0; i < LFSTSize; ++i) {
        validLFST[i] = false;
    }

    storeList.clear();
}

void
StoreSet::dump()
{
    cprintf("storeList.size(): %i\n", storeList.size());
    SeqNumMapIt store_list_it = storeList.begin();

    int num = 0;

    while (store_list_it != storeList.end()) {
        cprintf("%i: [sn:%lli] SSID:%i\n",
                num, (*store_list_it).first, (*store_list_it).second);
        num++;
        store_list_it++;
    }
}

} // namespace o3
} // namespace gem5
