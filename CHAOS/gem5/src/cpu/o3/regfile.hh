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

#ifndef __CPU_O3_REGFILE_HH__
#define __CPU_O3_REGFILE_HH__

#include <cstring>
#include <vector>

#include "arch/generic/isa.hh"
#include "base/trace.hh"
#include "cpu/o3/comm.hh"
#include "cpu/regfile.hh"
#include "debug/IEW.hh"

namespace gem5
{

namespace o3
{

class UnifiedFreeList;

/**
 * Simple physical register file class.
 */
class PhysRegFile
{
  private:

    using PhysIds = std::vector<PhysRegId>;
  public:
    using IdRange = std::pair<PhysIds::iterator,
                              PhysIds::iterator>;
  private:
    /** Integer register file. */
    RegFile intRegFile;
    std::vector<PhysRegId> intRegIds;

    /** Floating point register file. */
    RegFile floatRegFile;
    std::vector<PhysRegId> floatRegIds;

    /** Vector register file. */
    RegFile vectorRegFile;
    std::vector<PhysRegId> vecRegIds;

    /** Vector element register file. */
    RegFile vectorElemRegFile;
    std::vector<PhysRegId> vecElemIds;

    /** Predicate register file. */
    RegFile vecPredRegFile;
    std::vector<PhysRegId> vecPredRegIds;

    /** Matrix register file. */
    RegFile matRegFile;
    std::vector<PhysRegId> matRegIds;

    /** Condition-code register file. */
    RegFile ccRegFile;
    std::vector<PhysRegId> ccRegIds;

    /** Misc Reg Ids */
    std::vector<PhysRegId> miscRegIds;

    /**
     * Number of physical general purpose registers
     */
    unsigned numPhysicalIntRegs;

    /**
     * Number of physical floating point registers
     */
    unsigned numPhysicalFloatRegs;

    /**
     * Number of physical vector registers
     */
    unsigned numPhysicalVecRegs;

    /**
     * Number of physical vector element registers
     */
    unsigned numPhysicalVecElemRegs;

    /**
     * Number of physical predicate registers
     */
    unsigned numPhysicalVecPredRegs;

    /**
     * Number of physical matrix registers
     */
    unsigned numPhysicalMatRegs;

    /**
     * Number of physical CC registers
     */
    unsigned numPhysicalCCRegs;

    /** Total number of physical registers. */
    unsigned totalNumRegs;

  public:
    /**
     * Constructs a physical register file with the specified amount of
     * integer and floating point registers.
     */
    PhysRegFile(unsigned _numPhysicalIntRegs,
                unsigned _numPhysicalFloatRegs,
                unsigned _numPhysicalVecRegs,
                unsigned _numPhysicalVecPredRegs,
                unsigned _numPhysicalMatRegs,
                unsigned _numPhysicalCCRegs,
                const BaseISA::RegClasses &classes);

    /**
     * Destructor to free resources
     */
    ~PhysRegFile() {}

    /** Initialize the free list */
    void initFreeList(UnifiedFreeList *freeList);

    /** @return the total number of physical registers. */
    unsigned totalNumPhysRegs() const { return totalNumRegs; }

    /** Accessors for CHAOSPhysReg (physical-register-file fault injector).
     *  These expose the integer physical register id table and its size so
     *  a fault injector can target a physical cell by index (the ITC'23 /
     *  GeFIN abstraction). Direct members are private; these are the only
     *  public route. */
    unsigned numIntPhysRegs() const { return intRegIds.size(); }
    PhysRegIdPtr intPhysRegId(RegIndex idx) { return &intRegIds[idx]; }

    /** Read-tracking hook for CHAOSPhysReg closure verification.
     *  Counts reads of the INJECTED VALUE (not the phys slot): once the
     *  target phys slot is WRITTEN (setReg), the injected value is gone, so
     *  counting stops. This fixes the earlier bug where free-list slots
     *  showed high read counts (the slot gets re-allocated and read many
     *  times, but those reads are of the NEW value, not the injected one).
     *  reads_before_overwrite = # times the injected value was read.
     *  overwritten = whether the slot was written (value destroyed).
     *  Hot-path: target is -1 when no injection in flight → short-circuit. */
    int read_trace_target = -1;       // phys idx being tracked, or -1
    mutable uint64_t reads_before_overwrite = 0;  // reads of the injected value
    mutable bool trace_overwritten = false;      // set true when target slot is written
    void setReadTraceTarget(int idx) {
        read_trace_target = idx; reads_before_overwrite = 0; trace_overwritten = false;
    }
    void clearReadTraceTarget() { read_trace_target = -1; }
    uint64_t getReadsBeforeOverwrite() const { return reads_before_overwrite; }
    bool isTraceOverwritten() const { return trace_overwritten; }

    /** Gets a misc register PhysRegIdPtr. */
    PhysRegIdPtr getMiscRegId(RegIndex reg_idx) {
        return &miscRegIds[reg_idx];
    }

    RegVal
    getReg(PhysRegIdPtr phys_reg) const
    {
        const RegClassType type = phys_reg->classValue();
        const RegIndex idx = phys_reg->index();

        RegVal val;
        switch (type) {
          case IntRegClass:
            val = intRegFile.reg(idx);
            // CHAOSPhysReg read-trace: count reads of the INJECTED VALUE.
            // Stop counting once the slot is written (injected value destroyed).
            // Hot-path: target<0 when no trace → short-circuit.
            if (read_trace_target >= 0 && !trace_overwritten
                && (int)idx == read_trace_target)
                ++reads_before_overwrite;
            DPRINTF(IEW, "RegFile: Access to int register %i, has data %#x\n",
                    idx, val);
            return val;
          case FloatRegClass:
            val = floatRegFile.reg(idx);
            DPRINTF(IEW, "RegFile: Access to float register %i has data %#x\n",
                    idx, val);
            return val;
          case VecElemClass:
            val = vectorElemRegFile.reg(idx);
            DPRINTF(IEW, "RegFile: Access to vector element register %i "
                    "has data %#x\n", idx, val);
            return val;
          case CCRegClass:
            val = ccRegFile.reg(idx);
            DPRINTF(IEW, "RegFile: Access to cc register %i has data %#x\n",
                    idx, val);
            return val;
          default:
            panic("Unsupported register class type %d.", type);
        }
    }

    void
    getReg(PhysRegIdPtr phys_reg, void *val) const
    {
        const RegClassType type = phys_reg->classValue();
        const RegIndex idx = phys_reg->index();

        switch (type) {
          case IntRegClass:
            *(RegVal *)val = getReg(phys_reg);
            break;
          case FloatRegClass:
            *(RegVal *)val = getReg(phys_reg);
            break;
          case VecRegClass:
            vectorRegFile.get(idx, val);
            DPRINTF(IEW, "RegFile: Access to vector register %i, has "
                    "data %s\n", idx, vectorRegFile.regClass.valString(val));
            break;
          case VecElemClass:
            *(RegVal *)val = getReg(phys_reg);
            break;
          case VecPredRegClass:
            vecPredRegFile.get(idx, val);
            DPRINTF(IEW, "RegFile: Access to predicate register %i, has "
                    "data %s\n", idx, vecPredRegFile.regClass.valString(val));
            break;
          case MatRegClass:
            matRegFile.get(idx, val);
            DPRINTF(IEW, "RegFile: Access to matrix register %i, has "
                    "data %s\n", idx, matRegFile.regClass.valString(val));
            break;
          case CCRegClass:
            *(RegVal *)val = getReg(phys_reg);
            break;
          default:
            panic("Unrecognized register class type %d.", type);
        }
    }

    void *
    getWritableReg(PhysRegIdPtr phys_reg)
    {
        const RegClassType type = phys_reg->classValue();
        const RegIndex idx = phys_reg->index();

        switch (type) {
          case VecRegClass:
            return vectorRegFile.ptr(idx);
          case VecPredRegClass:
            return vecPredRegFile.ptr(idx);
          case MatRegClass:
            return matRegFile.ptr(idx);
          default:
            panic("Unrecognized register class type %d.", type);
        }
    }

    void
    setReg(PhysRegIdPtr phys_reg, RegVal val)
    {
        const RegClassType type = phys_reg->classValue();
        const RegIndex idx = phys_reg->index();

        switch (type) {
          case InvalidRegClass:
            break;
          case IntRegClass:
            // CHAOSPhysReg read-trace: a write to the traced slot destroys
            // the injected value → stop counting reads from this point.
            // (NOT the CHAOSPhysReg's own injection write — that goes through
            // a different path before setReadTraceTarget; the trace target is
            // set AFTER injection, so this write is a program/rename write.)
            if (read_trace_target >= 0 && (int)idx == read_trace_target)
                trace_overwritten = true;
            intRegFile.reg(idx) = val;
            DPRINTF(IEW, "RegFile: Setting int register %i to %#x\n",
                    idx, val);
            break;
          case FloatRegClass:
            floatRegFile.reg(idx) = val;
            DPRINTF(IEW, "RegFile: Setting float register %i to %#x\n",
                    idx, val);
            break;
          case VecElemClass:
            vectorElemRegFile.reg(idx) = val;
            DPRINTF(IEW, "RegFile: Setting vector element register %i to "
                    "%#x\n", idx, val);
            break;
          case CCRegClass:
            ccRegFile.reg(idx) = val;
            DPRINTF(IEW, "RegFile: Setting cc register %i to %#x\n",
                    idx, val);
            break;
          default:
            panic("Unsupported register class type %d.", type);
        }
    }

    void
    setReg(PhysRegIdPtr phys_reg, const void *val)
    {
        const RegClassType type = phys_reg->classValue();
        const RegIndex idx = phys_reg->index();

        switch (type) {
          case IntRegClass:
            setReg(phys_reg, *(RegVal *)val);
            break;
          case FloatRegClass:
            setReg(phys_reg, *(RegVal *)val);
            break;
          case VecRegClass:
            DPRINTF(IEW, "RegFile: Setting vector register %i to %s\n",
                    idx, vectorRegFile.regClass.valString(val));
            vectorRegFile.set(idx, val);
            break;
          case VecElemClass:
            setReg(phys_reg, *(RegVal *)val);
            break;
          case VecPredRegClass:
            DPRINTF(IEW, "RegFile: Setting predicate register %i to %s\n",
                    idx, vecPredRegFile.regClass.valString(val));
            vecPredRegFile.set(idx, val);
            break;
          case MatRegClass:
            DPRINTF(IEW, "RegFile: Setting matrix register %i to %s\n",
                    idx, matRegFile.regClass.valString(val));
            matRegFile.set(idx, val);
            break;
          case CCRegClass:
            setReg(phys_reg, *(RegVal *)val);
            break;
          default:
            panic("Unrecognized register class type %d.", type);
        }
    }
};

} // namespace o3
} // namespace gem5

#endif //__CPU_O3_REGFILE_HH__
