#include "cpu/o3/rfwb.hh"

#include <cstdlib>
#include <sstream>

#include "cpu/o3/cpu.hh"
#include "cpu/o3/dyn_inst.hh"
#include "cpu/o3/iew.hh"
#include "cpu/o3/inst_queue.hh"
#include "cpu/o3/regfile.hh"
#include "sim/core.hh"

namespace gem5
{

RFWB &
RFWB::instance()
{
    static RFWB inj;
    return inj;
}

RFWB::RFWB()
{
    const char *m = std::getenv("RFWB_MODEL");
    const char *md = std::getenv("RFWB_MODE");
    if (!m || !*m || !md || std::string(md) == "off")
        return;

    model = m;
    mode = md;
    enabled = true;
    countMode = (mode == "count");
    faultMode = (mode == "fault");

    auto env_u64 = [](const char *name, uint64_t dflt) {
        const char *v = std::getenv(name);
        return v && *v ? std::strtoull(v, nullptr, 0) : dflt;
    };
    auto env_int = [](const char *name, int dflt) {
        const char *v = std::getenv(name);
        return v && *v ? std::atoi(v) : dflt;
    };
    const char *s = std::getenv("RFWB_SAMPLE");
    sample = s && *s ? s : "NA";
    const char *tp = std::getenv("RFWB_TRACE");
    tracePath = tp && *tp ? tp : "/tmp/rfwb_trace.csv";

    ordinal = env_u64("RFWB_ORDINAL", 1);
    producerPc = env_u64("RFWB_PRODUCER_PC", 0);
    markerPc = env_u64("RFWB_MARKER_PC", 0);
    consumerPc = env_u64("RFWB_CONSUMER_PC", 0);
    srcIdx = env_int("RFWB_SRC_IDX", 0);
    bit = env_int("RFWB_BIT", 0);
    byteIdx = env_int("RFWB_BYTE", 0);
    targetSeq = env_u64("RFWB_TARGET_SEQ", 0);

    trace.open(tracePath, std::ios::out | std::ios::trunc);
    if (trace.is_open()) {
        trace << "tick,sample,model,mode,event,eligible,ordinal,seq,pc,"
                 "phys_idx,flat_idx,gen,src,value,extra\n";
    }
}

bool
RFWB::matchPC(o3::DynInst *inst, uint64_t pc) const
{
    return pc != 0 && inst && inst->pcState().instAddr() == pc;
}

bool
RFWB::isEligibleModel(const char *m) const
{
    return enabled && model == m;
}

void
RFWB::logRaw(const std::string &line)
{
    if (trace.is_open())
        trace << line << "\n";
}

void
RFWB::log(const char *event, o3::DynInst *inst, PhysRegIdPtr reg,
          int src, uint64_t value, const std::string &extra)
{
    if (!trace.is_open())
        return;
    std::ostringstream os;
    os << curTick() << ',' << sample << ',' << model << ',' << mode << ','
       << event << ',' << eligible << ',' << ordinal << ',';
    if (inst)
        os << inst->seqNum << ",0x" << std::hex
           << inst->pcState().instAddr() << std::dec;
    else
        os << "0,0x0";
    os << ',';
    if (reg)
        os << reg->index() << ',' << reg->flatIndex();
    else
        os << "-1,-1";
    os << ',' << (reg ? generation(reg) : 0) << ',' << src << ','
       << value << ",\"";
    for (char c : extra) {
        if (c == '"' || c == '\\') os << '\\';
        os << c;
    }
    os << "\"";
    logRaw(os.str());
}

RegVal
RFWB::onScalarRead(o3::DynInst *inst, int idx, PhysRegIdPtr reg, RegVal val)
{
    RFWB &r = instance();
    if (!r.enabled)
        return val;

    if (r.isEligibleModel("M001") && r.matchPC(inst, r.markerPc) &&
        idx == r.srcIdx) {
        ++r.eligible;
        r.log("M001_MARKER_READ", inst, reg, idx, val,
              "producer=" + (r.producerReg
                  ? std::to_string(r.producerReg->flatIndex()) : "none"));
        if (r.faultMode && !r.injected && r.eligible == r.ordinal &&
            r.producerReg) {
            RegVal cur = inst->cpu->physRegFile().getReg(r.producerReg);
            RegVal bad = cur ^ (1ULL << r.bit);
            inst->cpu->physRegFile().setReg(r.producerReg, bad);
            r.injected = true;
            r.faultProducerReg = r.producerReg;
            r.faultProducerSeq = r.producerSeq;
            r.faultTick = curTick();
            r.log("M001_INJECT", inst, r.producerReg, idx, bad,
                  "orig=" + std::to_string(cur) + ",bit=" +
                  std::to_string(r.bit));
        }
        if (r.faultProducerReg && reg == r.faultProducerReg) {
            r.log("M001_CONSUMER_READ", inst, reg, idx, val, "pc=" +
                  std::to_string(inst->pcState().instAddr()));
        }
        return val;
    }

    if (r.isEligibleModel("M003") && r.matchPC(inst, r.consumerPc) &&
        idx == r.srcIdx) {
        ++r.eligible;
        RegVal bad = val ^ (1ULL << r.bit);
        r.log("M003_CONSUMER_READ", inst, reg, idx, val,
              "return=" + std::to_string(bad));
        if (r.faultMode && !r.injected && r.eligible == r.ordinal) {
            r.injected = true;
            r.faultProducerReg = r.producerReg;
            r.faultReadReg = reg;
            r.faultProducerSeq = r.producerSeq;
            r.faultTick = curTick();
            r.log("M003_INJECT", inst, reg, idx, bad,
                  "orig=" + std::to_string(val));
            return bad;
        }
        if (r.faultReadReg && reg == r.faultReadReg)
            r.log("M003_PRF_READ", inst, reg, idx, val, "prf_correct=1");
    }
    if (r.isEligibleModel("M001") && r.injected && r.faultProducerReg &&
        reg == r.faultProducerReg)
        r.log("M001_CONSUMER_READ", inst, reg, idx, val, "pc=" +
              std::to_string(inst->pcState().instAddr()));
    if (r.isEligibleModel("M003") && r.injected && r.faultReadReg &&
        reg == r.faultReadReg)
        r.log("M003_PRF_READ", inst, reg, idx, val, "prf_correct=1");
    if (r.isEligibleModel("M005") && r.faultProducerReg &&
        reg == r.faultProducerReg)
        r.log("M005_CONSUMER_READ", inst, reg, idx, val, "prf_read=1");
    return val;
}

void
RFWB::onScalarWrite(o3::DynInst *inst, int idx, PhysRegIdPtr reg, RegVal val)
{
    RFWB &r = instance();
    if (!r.enabled || !reg || !r.matchPC(inst, r.producerPc))
        return;
    if (!(r.isEligibleModel("M001") || r.isEligibleModel("M003") ||
          r.isEligibleModel("M004") || r.isEligibleModel("M005")))
        return;
    r.producerReg = reg;
    r.producerSeq = inst->seqNum;
    r.producerVal = val;
    r.log("PRODUCER_WRITE", inst, reg, idx, val,
          "model=" + r.model);
}

void
RFWB::onScalarWriteAny(o3::DynInst *inst, int idx, PhysRegIdPtr reg,
                       RegVal val)
{
    RFWB &r = instance();
    if (!r.enabled || !r.injected || !reg)
        return;
    if (r.isEligibleModel("M001"))
        r.log("M001_CONSUMER_WRITE", inst, reg, idx, val, "");
    if (r.isEligibleModel("M003"))
        r.log("M003_CONSUMER_WRITE", inst, reg, idx, val, "");
}

void *
RFWB::onWritableVec(o3::DynInst *inst, int idx, PhysRegIdPtr reg)
{
    RFWB &r = instance();
    if (!r.enabled || !r.isEligibleModel("M002") || !reg ||
        reg->classValue() != VecRegClass)
        return nullptr;
    if (r.injected)
        r.log("M002_VEC_WRITE", inst, reg, idx, 0, "post_injection=1");
    if (!r.matchPC(inst, r.producerPc))
        return nullptr;
    auto inserted = r.seenVecEvents.insert(inst->seqNum);
    if (!inserted.second) {
        return inst->rfwbVecShadowActive ? inst->rfwbVecShadow.data()
                                         : nullptr;
    }
    ++r.eligible;
    size_t n = reg->regClass().regBytes();
    r.log("M002_VEC_ELIGIBLE", inst, reg, idx, n,
          "seq=" + std::to_string(inst->seqNum));
    if (r.faultMode && !r.injected && r.eligible == r.ordinal) {
        inst->rfwbVecShadow.assign(n, 0);
        inst->cpu->getReg(reg, inst->rfwbVecShadow.data(),
                          inst->threadNumber);
        inst->rfwbVecShadowActive = true;
        r.log("M002_SHADOW", inst, reg, idx, n,
              "byte=" + std::to_string(r.byteIdx));
        return inst->rfwbVecShadow.data();
    }
    return nullptr;
}

void
RFWB::onExecute(o3::DynInst *inst, bool noFault)
{
    RFWB &r = instance();
    if (!r.enabled || !inst)
        return;
    if (r.isEligibleModel("M004") && r.matchPC(inst, r.producerPc)) {
        r.log("M004_EXECUTED", inst, r.producerReg, 0, r.producerVal,
              "noFault=" + std::to_string(noFault));
    }
    if (!r.isEligibleModel("M002") || !inst->rfwbVecShadowActive)
        return;
    if (!noFault) {
        r.log("M002_ABORT_FAULT", inst, inst->renamedDestIdx(0), 0, 0, "");
    } else {
        size_t n = inst->rfwbVecShadow.size();
        if (r.byteIdx >= 0 && (size_t)r.byteIdx < n)
            inst->rfwbVecShadow[r.byteIdx] = 0;
        PhysRegIdPtr reg = inst->renamedDestIdx(0);
        inst->cpu->setReg(reg, inst->rfwbVecShadow.data(),
                          inst->threadNumber);
        r.injected = true;
        r.faultVecReg = reg;
        r.faultTick = curTick();
        r.log("M002_COMMIT", inst, reg, 0, n,
              "byte=" + std::to_string(r.byteIdx));
    }
    inst->rfwbVecShadowActive = false;
}

bool
RFWB::skipCommit(o3::DynInst *inst)
{
    RFWB &r = instance();
    if (!r.enabled || !r.isEligibleModel("M004") ||
        !r.matchPC(inst, r.producerPc) || inst->isMemRef() ||
        inst->isControl() || inst->isSquashed())
        return false;
    ++r.eligible;
    r.log("M004_ELIGIBLE", inst, r.producerReg, 0, r.producerVal,
          "seq=" + std::to_string(inst->seqNum));
    if (r.faultMode && !r.injected && r.eligible == r.ordinal) {
        r.injected = true;
        r.log("M004_SKIP_INSTTOCOMMIT", inst, r.producerReg, 0,
              r.producerVal, "");
        return true;
    }
    return false;
}

bool
RFWB::skipGlobalReady(o3::DynInst *inst, int destIdx, bool globalBefore)
{
    RFWB &r = instance();
    if (!r.enabled || !r.isEligibleModel("M005") ||
        !r.matchPC(inst, r.producerPc) || destIdx != 0)
        return false;
    ++r.eligible;
    PhysRegIdPtr reg = inst->renamedDestIdx(destIdx);
    bool iq = inst->cpu->o3IEW().instQueue.isRegReady(reg);
    r.log("M005_WB", inst, reg, destIdx, r.producerVal,
          "global_before=" + std::to_string(globalBefore) +
          ",iq_ready=" + std::to_string(iq));
    bool selected = r.faultMode &&
        ((r.targetSeq != 0 && inst->seqNum == r.targetSeq) ||
         (r.targetSeq == 0 && !r.injected && r.eligible == r.ordinal));
    if (selected) {
        r.injected = true;
        r.faultProducerReg = r.producerReg;
        r.faultProducerSeq = r.producerSeq;
        r.faultProducerGen = r.generation(reg);
        r.faultTick = curTick();
        r.log("M005_SKIP_GLOBAL_READY", inst, reg, destIdx,
              r.producerVal, "fault_tick=" + std::to_string(r.faultTick));
        return true;
    }
    return false;
}

void
RFWB::onRenameSrc(o3::DynInst *inst, int srcIdx, PhysRegIdPtr reg,
                  bool globalReady)
{
    RFWB &r = instance();
    if (!r.enabled || !r.isEligibleModel("M005") || !reg)
        return;
    if (r.faultProducerReg &&
        (reg != r.faultProducerReg || r.generation(reg) != r.faultProducerGen))
        return;
    bool iq = inst->cpu->o3IEW().instQueue.isRegReady(reg);
    bool target = r.faultProducerReg && reg == r.faultProducerReg;
    r.log("M005_CONSUMER_RENAME", inst, reg, srcIdx, 0,
          "global=" + std::to_string(globalReady) +
          ",iq=" + std::to_string(iq) +
          ",target=" + std::to_string(target));
}

void
RFWB::onIQRepair(o3::DynInst *inst, PhysRegIdPtr reg)
{
    RFWB &r = instance();
    if (!r.enabled || !r.isEligibleModel("M005") || !reg)
        return;
    if (r.faultProducerReg &&
        (reg != r.faultProducerReg || r.generation(reg) != r.faultProducerGen))
        return;
    bool target = r.faultProducerReg && reg == r.faultProducerReg;
    r.log("M005_IQ_REPAIR", inst, reg, -1, 0,
          "target=" + std::to_string(target));
}

void
RFWB::onVectorRead(o3::DynInst *inst, int idx, PhysRegIdPtr reg,
                   const void *val)
{
    RFWB &r = instance();
    if (!r.enabled || !r.faultVecReg || reg != r.faultVecReg || !val)
        return;
    const uint8_t *p = static_cast<const uint8_t *>(val);
    std::ostringstream os;
    os << "bytes16=";
    for (int i = 0; i < 16; i++) {
        if (i) os << ':';
        os << std::hex << (unsigned)p[i];
    }
    r.log("M002_CONSUMER_READ", inst, reg, idx, 0, os.str());
}

void
RFWB::onCommitStall(o3::DynInst *inst)
{
    RFWB &r = instance();
    if (!r.enabled || !r.isEligibleModel("M004") || !inst)
        return;
    r.log("M004_COMMIT_STALL", inst, nullptr, 0, 0,
          "head=1,canCommit=" + std::to_string(inst->readyToCommit()));
}

void
RFWB::onCommit(o3::DynInst *inst)
{
    RFWB &r = instance();
    if (!r.enabled || !inst)
        return;
    if (r.isEligibleModel("M004") && r.matchPC(inst, r.producerPc))
        r.log("M004_COMMIT", inst, nullptr, 0, 0, "committed=1");
    if (r.isEligibleModel("M005") && r.matchPC(inst, r.consumerPc))
        r.log("M005_CONSUMER_COMMIT", inst, nullptr, 0, 0, "committed=1");
}

uint64_t
RFWB::generation(PhysRegIdPtr reg) const
{
    if (!reg) return 0;
    auto it = physGen.find(reg->flatIndex());
    return it == physGen.end() ? 0 : it->second;
}

void
RFWB::onPhysAlloc(int cls, PhysRegIdPtr reg)
{
    if (!reg) return;
    RFWB &r = instance();
    ++r.physGen[reg->flatIndex()];
    r.physAllocTick[reg->flatIndex()] = curTick();
}

void
RFWB::onPhysFree(int cls, PhysRegIdPtr reg)
{
    if (!reg) return;
    (void)cls;
    instance().physAllocTick[reg->flatIndex()] = curTick();
}

void
RFWB::onSquash(o3::DynInst *inst)
{
    RFWB &r = instance();
    if (!r.enabled || !r.isEligibleModel("M004") || !inst)
        return;
    if (r.matchPC(inst, r.producerPc))
        r.log("M004_SQUASH", inst, nullptr, 0, 0, "squashed=1");
}

} // namespace gem5



