/*
 * Copyright (c) 2016-2018 ARM Limited
 * All rights reserved
 *
 * The license below extends only to copyright in the software and shall
 * not be construed as granting a license to any other intellectual
 * property including but not limited to intellectual property relating
 * to a hardware implementation of the functionality of the software
 * licensed hereunder. You may use the software subject to the license
 * terms below provided that you ensure that this notice is replicated
 * unmodified and in its entirety in all distributions of the software,
 * modified or unmodified, in source code or in binary form.
 *
 * Copyright (c) 2004-2005 The Regents of The University of Michigan
 * Copyright (c) 2013 Advanced Micro Devices, Inc.
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

#ifndef __CPU_O3_FREE_LIST_HH__
#define __CPU_O3_FREE_LIST_HH__

#include <algorithm>
#include <array>
#include <iostream>
#include <queue>

#include "base/logging.hh"
#include "base/trace.hh"
#include "cpu/o3/comm.hh"
#include "cpu/o3/regfile.hh"
#include "debug/FreeList.hh"
// §2.2 CHAOSFreeList: included so UnifiedFreeList::getReg's inline hook can
// call chaosFreeList->maybeCorrupt(). Non-circular: CHAOSFreeList.hh only
// forward-declares o3::UnifiedFreeList (does NOT include free_list.hh).
#include "cpu/o3/CHAOSFreeList/CHAOSFreeList.hh"
// U2 (R08-b/FR09-b, ooo 03-design-matrix R8/R38 free-list 弹出时序): the
// PRE-pop delay hook reaches CHAOSRenameMap the same way. Non-circular:
// CHAOSRenameMap.hh does NOT include free_list.hh.
#include "cpu/o3/CHAOSRenameMap/CHAOSRenameMap.hh"

namespace gem5
{

// §2.2 CHAOSFreeList forward decl (raw pointer member below).
class CHAOSFreeList;

namespace o3
{

class UnifiedRenameMap;

/**
 * Free list for a single class of registers (e.g., integer
 * or floating point).  Because the register class is implicitly
 * determined by the rename map instance being accessed, all
 * architectural register index parameters and values in this class
 * are relative (e.g., %fp2 is just index 2).
 */
class SimpleFreeList
{
  private:

    /** The actual free list */
    std::queue<PhysRegIdPtr> freeRegs;

  public:
    // §2.2 CHAOSFreeList: set by UnifiedFreeList at injector startup so the
    // getReg() hook knows the class + reaches the injector. Defaults safe
    // (chaosFreeList=nullptr = no injection; classValue=0 = IntRegClass).
    int classValue = 0;
    CHAOSFreeList *chaosFreeList = nullptr;
    // U2 R08-b/FR09-b: the rename-map timing injector's PRE-pop hook.
    // Set by UnifiedFreeList::setChaosRenameMap (injector startup).
    CHAOSRenameMap *chaosRenameMap = nullptr;

    SimpleFreeList() {};

    /** Add a physical register to the free list */
    void addReg(PhysRegIdPtr reg) { freeRegs.push(reg); }

    /** Add physical registers to the free list */
    template<class InputIt>
    void
    addRegs(InputIt first, InputIt last) {
        std::for_each(first, last, [this](typename InputIt::value_type& reg) {
            freeRegs.push(&reg);
        });
    }

    /** Get the next available register from the free list */
    PhysRegIdPtr getReg()
    {
        assert(!freeRegs.empty());
        PhysRegIdPtr free_reg = freeRegs.front();
        // W4 final D22 CHAOSFreeList head_stuck: PRE-pop hook — a stuck
        // head pointer hands out the SAME id every time WITHOUT advancing
        // (the injector mutates free_reg to the frozen id; true return =
        // caller must NOT pop). nullptr / other modes = zero regression.
        if (chaosFreeList
            && chaosFreeList->maybeStuckHead(classValue, free_reg)) {
            return free_reg;
        }
        // U2 (R08-b/FR09-b 弹出延后一拍): on fire the caller does NOT pop
        // — the phys reg stays at the freelist head for the rest of this
        // cycle (同窗另一 rename 可能弹出同号 → 双重分配=静默 SDC 源,
        // 03 原文口径); the injector's next-tick-start event performs the
        // deferred pop (Default_Pri < CPU_Tick_Pri=50 -> before the CPU
        // tick). nullptr / other modes = zero regression.
        if (chaosRenameMap
            && chaosRenameMap->maybeDelayFreePop(classValue, free_reg)) {
            return free_reg;
        }
        freeRegs.pop();
        // §2.2 CHAOSFreeList: post-pop hook. NOTE: rename calls
        // SimpleFreeList::getReg() directly (rename_map.cc:91 via
        // freeList = &(UnifiedFreeList::freeLists[i])), NOT
        // UnifiedFreeList::getReg(type) — so the hook MUST be here. The
        // chaosFreeList ptr + class value are set by UnifiedFreeList's
        // setChaosFreeList() at injector startup (propagated to all
        // per-class SimpleFreeLists). nullptr = no injection (zero regression).
        if (chaosFreeList) chaosFreeList->maybeCorrupt(classValue, free_reg);
        return free_reg;
    }

    /** Return the number of free registers on the list. */
    unsigned numFreeRegs() const { return freeRegs.size(); }

    /** U2 (R08-b/FR09-b): the deferred-pop replay — pop ONE entry from
     *  the head. Called only by the injector's next-tick-start event
     *  (via UnifiedFreeList::chaosDeferredPop); guarded on non-empty
     *  (if the double-alloc already consumed the head, the deferred pop
     *  absorbs the next one — the propagated corruption is the fault). */
    void chaosDeferredPop() { if (!freeRegs.empty()) freeRegs.pop(); }

    /** True iff there are free registers on the list. */
    bool hasFreeRegs() const { return !freeRegs.empty(); }

    /** True iff the given physical register is currently in the free list
     *  (= not allocated = dead/inactive). Used by CHAOSPhysReg's liveness
     *  probe: a phys reg NOT in the free list is allocated and may be read
     *  by in-flight instructions even if no rename map entry currently
     *  points to it (e.g. an in-flight inst still holds it as a source).
     *  O(N) scan of the queue; only called at inject time, not hot path. */
    bool contains(const PhysRegIdPtr reg) const {
        // std::queue's underlying container is protected; derive a helper to
        // expose it so we can scan (queue doesn't support iteration).
        struct ExposedQueue : public std::queue<PhysRegIdPtr> {
            using std::queue<PhysRegIdPtr>::c;
        };
        const auto &c = static_cast<const ExposedQueue&>(freeRegs).c;
        for (const auto &r : c) {
            if (r == reg) return true;
        }
        return false;
    }
};


/**
 * FreeList class that simply holds the list of free integer and floating
 * point registers.  Can request for a free register of either type, and
 * also send back free registers of either type.  This is a very simple
 * class, but it should be sufficient for most implementations.  Like all
 * other classes, it assumes that the indices for the floating point
 * registers starts after the integer registers end.  Hence the variable
 * numPhysicalIntRegs is logically equivalent to the baseFP dependency.
 * Note that while this most likely should be called FreeList, the name
 * "FreeList" is used in a typedef within the CPU Policy, and therefore no
 * class can be named simply "FreeList".
 * @todo: Give a better name to the base FP dependency.
 */
class UnifiedFreeList
{
  private:

    /** The object name, for DPRINTF.  We have to declare this
     *  explicitly because Scoreboard is not a SimObject. */
    const std::string _name;

    std::array<SimpleFreeList, CCRegClass + 1> freeLists;

    /**
     * The register file object is used only to distinguish integer
     * from floating-point physical register indices.
     */
    PhysRegFile *regFile;

    // §2.2 CHAOSFreeList: raw pointer to the freelist fault injector. Set by
    // the injector's startup() (dynamic_cast<O3CPU*> + physFreeList().
    // setChaosFreeList(this)). nullptr = no injection (zero regression).
    CHAOSFreeList *chaosFreeList = nullptr;

  public:
    /** §2.2 CHAOSFreeList accessor (injector sets it at startup). Propagates
     *  the pointer + class value to each per-class SimpleFreeList so the
     *  getReg() hook (which rename calls DIRECTLY via SimpleFreeList::getReg,
     *  not UnifiedFreeList::getReg) can reach the injector. */
    void setChaosFreeList(CHAOSFreeList *p) {
        chaosFreeList = p;
        for (int i = 0; i < (int)(sizeof(freeLists)/sizeof(freeLists[0])); i++) {
            freeLists[i].chaosFreeList = p;
            freeLists[i].classValue = i;
        }
    }

    /** U2 (R08-b/FR09-b): CHAOSRenameMap's freelist-timing hook — the
     *  same propagation shape as setChaosFreeList (the PRE-pop delay
     *  gate lives in SimpleFreeList::getReg, called directly by
     *  SimpleRenameMap::rename). */
    void setChaosRenameMap(CHAOSRenameMap *p) {
        for (int i = 0; i < (int)(sizeof(freeLists)/sizeof(freeLists[0])); i++) {
            freeLists[i].chaosRenameMap = p;
            // U2 round-2 fix: classValue was only assigned inside
            // setChaosFreeList — without a CHAOSFreeList attached every
            // per-class list defaulted to classValue=0 (IntRegClass), so
            // the vec pop-delay gate (fr09-late) never matched and the
            // arm silently never fired (round-2: 0 log lines). Idempotent
            // when both injectors are attached.
            freeLists[i].classValue = i;
        }
    }

    /** U2 (R08-b/FR09-b): the deferred-pop replay for class_value's
     *  per-class list (the injector's next-tick-start event). */
    void chaosDeferredPop(int class_value) {
        freeLists[class_value].chaosDeferredPop();
    }

  private:

    /*
     * We give UnifiedRenameMap internal access so it can get at the
     * internal per-class free lists and associate those with its
     * per-class rename maps. See UnifiedRenameMap::init().
     */
    friend class UnifiedRenameMap;

  public:
    /** Constructs a free list.
     *  @param _numPhysicalIntRegs Number of physical integer registers.
     *  @param reservedIntRegs Number of integer registers already
     *                         used by initial mappings.
     *  @param _numPhysicalFloatRegs Number of physical fp registers.
     *  @param reservedFloatRegs Number of fp registers already
     *                           used by initial mappings.
     */
    UnifiedFreeList(const std::string &_my_name, PhysRegFile *_regFile);

    /** Gives the name of the freelist. */
    std::string name() const { return _name; };

    /** Gets a free register of type type. */
    PhysRegIdPtr getReg(RegClassType type) {
        PhysRegIdPtr r = freeLists[type].getReg();
        // §2.2 CHAOSFreeList: post-pop hook. pop_wrong mutates `r` (return a
        // different legal physReg); mark_free re-adds an allocated physReg to
        // the free list (history residue). nullptr = no injection (zero
        // regression).
        if (chaosFreeList) chaosFreeList->maybeCorrupt((int)type, r);
        return r;
    }

    /** Adds a register back to the free list. */
    template<class InputIt>
    void
    addRegs(InputIt first, InputIt last)
    {
        std::for_each(first, last, [this](auto &reg) { addReg(&reg); });
    }

    /** Adds a register back to the free list. */
    void
    addReg(PhysRegIdPtr freed_reg)
    {
        // W4 final D19 CHAOSFreeList drop_release: PRE-push hook — the
        // injector may SUPPRESS this one release (the freed physReg is NOT
        // re-added; the free pool permanently shrinks by one). Covers both
        // runtime release paths (rename.cc removeFromHistory + the
        // freeingInProgress drain). Init is safe: PhysRegFile::initFreeList
        // routes through addRegs->addReg, but chaosFreeList is still
        // nullptr during construction (the injector self-attaches at
        // startup()). nullptr / other modes = zero regression.
        if (chaosFreeList
            && chaosFreeList->maybeDropRelease(
                   (int)freed_reg->classValue(), freed_reg)) {
            return;
        }
        freeLists[freed_reg->classValue()].addReg(freed_reg);
    }

    /** Checks if there are any free registers of type type. */
    bool
    hasFreeRegs(RegClassType type) const
    {
        return freeLists[type].hasFreeRegs();
    }

    /** Returns the number of free registers of type type. */
    unsigned
    numFreeRegs(RegClassType type) const
    {
        return freeLists[type].numFreeRegs();
    }

    /** True iff the given physical register is currently free (inactive).
     *  Used by CHAOSPhysReg liveness probe. See SimpleFreeList::contains. */
    bool
    isFree(RegClassType type, const PhysRegIdPtr reg) const
    {
        return freeLists[type].contains(reg);
    }
};

} // namespace o3
} // namespace gem5

#endif // __CPU_O3_FREE_LIST_HH__
