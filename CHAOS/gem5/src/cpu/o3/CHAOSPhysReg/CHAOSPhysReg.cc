#include "cpu/o3/CHAOSPhysReg/CHAOSPhysReg.hh"
#include "params/CHAOSPhysReg.hh"

#include <iostream>
#include <fstream>
#include <sstream>
#include <iomanip>
#include <vector>
#include <random>
#include <bitset>
#include <cstring>
#include <cstdint>
#include <algorithm>

#include "base/output.hh"
#include "cpu/o3/cpu.hh"
#include "cpu/o3/dyn_inst.hh"     // [FR03] post-execute Vec stuck re-apply
#include "cpu/o3/regfile.hh"
#include "cpu/o3/rename_map.hh"
#include "cpu/o3/CHAOSPhysReg/chaos_vec_stuck.hh"
#include "cpu/o3/CHAOSPropagation/CHAOSPropagation.hh"  // FSU_PROP stream
#include "arch/generic/isa.hh"
#include "sim/core.hh"            // curTick() for L5 first-impact stamping
#include "sim/sim_exit.hh"        // registerExitCallback (W2.5 CHAOS_L0 line)
#include "arch/arm/insts/static_inst.hh"  // [FR01/FR02] real encoding()
#include "cpu/o3/CHAOSFPU/decoded_fp.hh"  // [FR01/FR02] precision decoder

namespace gem5
{

namespace
{
// [FR01/FR02] Decode the consumer's REAL AArch64 encoding. This mirrors
// CHAOSFPU::familyOf (the only definitions of the FP opClass families); a
// non-reliable decode returns 0 and must never be eligible.
chaos_fsu::FpFamily
fsuFamilyOf(OpClass oc)
{
    switch (oc) {
      case FloatAddOp: case FloatCmpOp: case FloatMultOp:
      case FloatMultAccOp: case FloatDivOp: case FloatMiscOp:
      case FloatSqrtOp:
        return chaos_fsu::FpFamily::ScalarFloat;
      case FloatCvtOp:
        return chaos_fsu::FpFamily::Cvt;
      case SimdFloatAluOp: case SimdFloatCmpOp: case SimdFloatCvtOp:
      case SimdFloatMultOp: case SimdFloatMultAccOp: case SimdFloatDivOp:
      case SimdFloatSqrtOp: case SimdFloatMiscOp: case SimdFloatAddOp:
        return oc == SimdFloatCvtOp ? chaos_fsu::FpFamily::Cvt
                                    : chaos_fsu::FpFamily::SimdFloat;
      default:
        return chaos_fsu::FpFamily::Other;
    }
}

std::string
fpFieldName(int bit_in_lane, int precision)
{
    if (precision == 32) {
        if (bit_in_lane == 31) return "sign";
        if (bit_in_lane >= 27) return "exp_hi";
        if (bit_in_lane >= 23) return "exp_lo";
        if (bit_in_lane >= 15) return "mant_hi";
        if (bit_in_lane >= 8) return "mant_mid";
        return "mant_lo";
    }
    if (bit_in_lane == 63) return "sign";
    if (bit_in_lane >= 58) return "exp_hi";
    if (bit_in_lane >= 52) return "exp_lo";
    if (bit_in_lane >= 35) return "mant_hi";
    if (bit_in_lane >= 18) return "mant_mid";
    return "mant_lo";
}

int
decodedConsumerPrecision(const o3::DynInst *inst)
{
    if (!inst || !inst->staticInst)
        return 0;
    auto *asi = dynamic_cast<const ArmISA::ArmStaticInst *>(
        inst->staticInst.get());
    if (!asi)
        return 0;
    const auto d = chaos_fsu::decodedPrecision(
        asi->encoding(), fsuFamilyOf(inst->opClass()));
    return d.reliable ? d.precision_bits : 0;
}
}  // anonymous namespace


    CHAOSPhysReg::CHAOSPhysReg(const CHAOSPhysRegParams &p)
        : SimObject(p),
          cpu(dynamic_cast<o3::CPU *>(p.cpu)),
          fi_mode(stringToMode(p.injectionMode)),
          target_phys_idx(p.targetPhysRegIdx),
          target_arch_idx(p.targetArchRegIdx),
          reg_target_class(stringToRegClassSel(p.regTargetClass)),
          require_allocated(p.requireAllocated),
          vec_lane_width(p.vecLaneWidth),
          vec_lane_offset(p.vecLaneOffset),
          probability(p.probability),
          num_bits_to_change(p.bitsToChange),
          fault_type_enum(stringToFaultType(p.faultType)),
          fault_mask(std::bitset<64>(p.faultMask)),
          bit_flip_prob(0.9),
          stuck_at_zero_prob(0.05),
          stuck_at_one_prob(0.05),
          first_clock(Cycles(p.firstClock)),
          last_clock(Cycles(p.lastClock)),
          max_faults(p.maxFaults),
          faults_injected_count(0),
          rng_seed(p.rngSeed),    write_log(p.writeLog),
    trigger_value_mask(p.triggerValueMask),
    trigger_value_pattern(p.triggerValuePattern),
    semantic_role(p.semanticRole),
    load_id(p.loadId),
          attackEvent([this] { this->attackCheck(); }, name()),
          periodicCheck([this] { this->checkPermanent(); }, name() + ".periodicCheck"),
          readTraceEvent([this] { this->readTraceCheck(); }, name() + ".readTrace"),
          stats(nullptr)
    {
        if (!cpu) {
            throw std::runtime_error(
                "CHAOSPhysReg: cpu is not an O3CPU. CHAOSPhysReg only supports "
                "O3CPU (it needs regFile/renameMap). Cast failed.");
        }
        // [FR01/FR02] Random-target policy. Unknown values fail closed so a
        // typo can never silently fall back to the historical dead-slot
        // selection; an explicit target index contradicts the policy.
        const std::string &ts = p.targetSelection;
        if (ts != "random_allocated" && ts != "ready_consumer") {
            throw std::runtime_error(
                "CHAOSPhysReg: unknown targetSelection '" + ts +
                "' (expected 'random_allocated' or 'ready_consumer')");
        }
        require_ready_consumer = (ts == "ready_consumer");
        if (require_ready_consumer && fi_mode != Mode::Phys) {
            throw std::runtime_error(
                "CHAOSPhysReg: targetSelection=ready_consumer requires "
                "injectionMode=phys");
        }
        if (require_ready_consumer && target_phys_idx >= 0) {
            throw std::runtime_error(
                "CHAOSPhysReg: targetSelection=ready_consumer cannot be "
                "combined with an explicit targetPhysRegIdx");
        }
        target_precision = p.targetPrecision;
        if (target_precision != 0 && target_precision != 16 &&
            target_precision != 32 && target_precision != 64) {
            throw std::runtime_error(
                "CHAOSPhysReg: targetPrecision must be 0/16/32/64, got " +
                std::to_string(target_precision));
        }
        if (target_precision != 0 && !require_ready_consumer) {
            throw std::runtime_error(
                "CHAOSPhysReg: targetPrecision requires "
                "targetSelection=ready_consumer");
        }
        // [FR01/FR02] A precision wider than the corrupted lane would label
        // a 32-bit lane as FP64 (or vice versa). Fail closed before the run.
        if (target_precision != 0 && vec_lane_width < target_precision) {
            throw std::runtime_error(
                "CHAOSPhysReg: targetPrecision " +
                std::to_string(target_precision) +
                " requires vecLaneWidth >= " +
                std::to_string(target_precision) + " (got " +
                std::to_string(vec_lane_width) + ")");
        }
        if (probability > 0.0) {
            log_stream = simout.create("fault_injections.log", false, true);
            if (!log_stream || !log_stream->stream()) {
                panic("CHAOSPhysReg: Could not open log file");
            }
            stats = std::make_unique<CHAOSPhysRegStats>(this);
            rng.seed(rng_seed != 0 ? rng_seed : rd());
            if (num_bits_to_change == -1) {
                std::uniform_int_distribution<int> dist(1, 64);
                num_bits_to_change = dist(rng);
            }
            inter_fault_cycles_dist = std::geometric_distribution<unsigned>(probability);
            unsigned next_fault_cycle_distance = inter_fault_cycles_dist(rng);
            scheduleAttackEvent(first_clock + Cycles(next_fault_cycle_distance));
            scheduleCheckPermanentFault(first_clock + Cycles(1));
            // W2.5 L0 lifecycle: print the pinned CHAOS_L0 line at end of
            // sim via an exit callback (CHAOSProbe/CHAOSMicroSnap
            // precedent). The readTrace poll event canNOT do this on short
            // workloads: it is scheduled 100000 cycles out and never fires
            // once the workload halts (observed on smoke — ReadTraceFinal
            // only appears on runs long enough for one more poll).
            registerExitCallback([this]() { this->l0Final(); });
        }
    }

    CHAOSPhysReg::CHAOSPhysRegStats::CHAOSPhysRegStats(statistics::Group *parent)
        : statistics::Group(parent),
          ADD_STAT(numFaultsInjected, statistics::units::Count::get(),
                   "Total number of faults injected"),
          ADD_STAT(numBitFlips, statistics::units::Count::get(),
                   "Number of bit flip faults injected"),
          ADD_STAT(numStuckAtZero, statistics::units::Count::get(),
                   "Number of stuck-at-0 faults injected"),
          ADD_STAT(numStuckAtOne, statistics::units::Count::get(),
                   "Number of stuck-at-1 faults injected"),
          ADD_STAT(numPermanentFaults, statistics::units::Count::get(),
                   "Total number of permanent faults injected")
    {}

    CHAOSPhysReg::~CHAOSPhysReg() {}

    void
    CHAOSPhysReg::startup()
    {
        SimObject::startup();
        // [FR03] Self-attach so DynInst::execute() can re-assert a permanent
        // Vec stuck target after every vector write.
        if (cpu)
            cpu->setChaosPhysReg(this);
        // If CHAOSPropagation is already attached, make sure the FR03
        // terminal (chain_end) is flushed while its stream is open. If it
        // attaches later, the first install registers the hook instead.
        registerVecExitFlush();
        registerTransientExitFlush();
    }

    namespace
    {
    std::string
    propHex(uint64_t v)
    {
        std::ostringstream os;
        os << "0x" << std::hex << v;
        return os.str();
    }

    // Read one lane from a little-endian vector image. The lane must be
    // inside the 128-bit architectural value.
    uint64_t
    readLane(const uint8_t *vec, int lane_width, int lane)
    {
        if (!vec || lane < 0 || lane_width <= 0 || lane_width > 64)
            return 0;
        const int lane_bytes = lane_width / 8;
        const int base = lane * lane_bytes;
        if (base + lane_bytes > chaos_vec_transient::kVecBytes)
            return 0;
        uint64_t v = 0;
        for (int b = 0; b < lane_bytes; ++b)
            v |= (uint64_t)vec[base + b] << (8 * b);
        return v;
    }
    } // anonymous namespace

    const char *
    CHAOSPhysReg::vecRegClassName(int cls)
    {
        if (cls == VecRegClass) return "vec";
        if (cls == FloatRegClass) return "float";
        if (cls == IntRegClass) return "int";
        return "unknown";
    }

    bool
    CHAOSPhysReg::isFreeListClass(RegClassType cls)
    {
        // PhysRegFile::initFreeList adds exactly these three classes to the
        // unified free list. Every index in range is therefore allocatable;
        // VecElem/VecPred/Mat/CC/Misc are reserved/special and are never
        // legal permanent-cell targets.
        return cls == IntRegClass || cls == FloatRegClass ||
               cls == VecRegClass;
    }

    uint64_t
    CHAOSPhysReg::emitVecModelProp(
        const char *model, const char *freq, const char *kind,
        uint64_t fault_id, uint64_t parent,
        std::vector<std::pair<std::string, std::string>> kv)
    {
        if (!cpu || !cpu->chaosPropagation)
            return 0;
        kv.push_back({"fault_id", std::to_string(fault_id)});
        if (parent != 0)
            kv.push_back({"parent_event_id", std::to_string(parent)});
        kv.push_back({"model_id", model});
        kv.push_back({"freq", freq});
        kv.push_back({"unit", "PRF_Vec"});
        if (!semantic_role.empty())
            kv.push_back({"submodel", semantic_role});
        // [FR01/FR02] IEEE field/precision identity for the audit. The
        // injected bits live inside one lane; the lane width (or the decoded
        // consumer precision) selects the FP32/FP64 field table. FR02-d may
        // cross fields: the label is the lowest bit's field, and every bit
        // identity stays in bit_indices for per-bit auditing.
        const std::string model_s(model);
        if (model_s == "FR01" || model_s == "FR02") {
            if (!load_id.empty())
                kv.push_back({"load_id", load_id});
            const int prec = target_precision != 0 ? target_precision
                : (last_selected_precision != 0 ? last_selected_precision
                   : (vec_transient.lane_width == 32 ? 32 : 64));
            bool has_prec = false, has_field = false;
            for (const auto &p : kv) {
                if (p.first == "precision") has_prec = true;
                if (p.first == "field") has_field = true;
            }
            if (!has_prec)
                kv.push_back({"precision", prec == 32 ? "fp32" : "fp64"});
            const int bit = vec_transient.sel.bits.empty()
                                ? 0
                                : vec_transient.sel.bits[0].bit_in_lane;
            const std::string fname = fpFieldName(bit, prec);
            if (has_field) {
                for (auto &p : kv)
                    if (p.first == "field" &&
                        p.second == "transient_bit_flip")
                        p.second = fname;
            } else {
                kv.push_back({"field", fname});
            }
        }
        // The L0 root establishes the taint; every follow-up event belongs to
        // the same fault (fsu_taint). A lifecycle transition is never a new
        // fault.
        const std::string k(kind);
        kv.push_back({"corr", (k == "fault_installed" ||
                               k == "fault_applied")
                              ? "origin" : "fsu_taint"});
        return cpu->chaosPropagation->notePropEvt(kind, kv);
    }

    uint64_t
    CHAOSPhysReg::emitFsuProp(
        const char *kind, uint64_t fault_id, uint64_t parent,
        std::vector<std::pair<std::string, std::string>> kv)
    {
        const uint64_t eid = emitVecModelProp(
            "FR03", "F5", kind, fault_id, parent, std::move(kv));
        if (eid)
            vec_emit.last_event = eid;
        return eid;
    }

    void
    CHAOSPhysReg::registerVecExitFlush()
    {
        if (vec_emit.exit_flush_registered || !cpu ||
            !cpu->chaosPropagation)
            return;
        cpu->chaosPropagation->registerExitFlush(
            [this]() { this->emitVecTerminal(); });
        vec_emit.exit_flush_registered = true;
    }

    // ------------------------------------------------------------------
    // [FR01/FR02] Transient Vec bit-flip evidence.
    // ------------------------------------------------------------------
    std::string
    CHAOSPhysReg::bitIndices(const chaos_vec_transient::Selection &s)
    {
        std::ostringstream os;
        for (size_t i = 0; i < s.bits.size(); ++i) {
            if (i)
                os << ",";
            os << s.bits[i].flat;
        }
        return os.str();
    }

    std::string
    CHAOSPhysReg::vec128Hex(const uint8_t *v)
    {
        uint64_t lo = 0, hi = 0;
        for (int b = 0; b < 8; ++b)
            lo |= (uint64_t)v[b] << (8 * b);
        for (int b = 0; b < 8; ++b)
            hi |= (uint64_t)v[8 + b] << (8 * b);
        std::ostringstream os;
        os << "0x" << std::hex << std::setw(16) << std::setfill('0') << hi
           << std::setw(16) << lo;
        return os.str();
    }

    void
    CHAOSPhysReg::registerTransientExitFlush()
    {
        if (vec_transient.exit_flush_registered || !cpu ||
            !cpu->chaosPropagation)
            return;
        cpu->chaosPropagation->registerExitFlush(
            [this]() { this->finalizeVecTransient(nullptr); });
        vec_transient.exit_flush_registered = true;
    }

    void
    CHAOSPhysReg::noteVecTransientInstalled(
        ThreadID tid, int phys_idx, int arch_idx, uint32_t generation,
        const chaos_vec_transient::Selection &sel,
        const uint8_t *before, const uint8_t *after)
    {
        // F0 is one injection per run; if a longer campaign installs a new
        // transient while the previous one is still live, close the old chain
        // honestly instead of silently merging two faults.
        if (vec_transient.installed)
            finalizeVecTransient(nullptr);

        const bool flush_registered = vec_transient.exit_flush_registered;
        vec_transient = VecTransientEmission();
        vec_transient.exit_flush_registered = flush_registered;
        vec_transient.installed = true;
        vec_transient.fault_id = next_fsu_fault_id++;
        vec_transient.install_tick = curTick();
        vec_transient.phys_index = phys_idx;
        vec_transient.arch_index = arch_idx;
        vec_transient.install_generation = generation;
        vec_transient.lane_width = sel.lane_width;
        vec_transient.sel = sel;
        vec_transient.install_lane_before =
            readLane(before, sel.lane_width, sel.lane_offset);
        vec_transient.install_lane_after =
            readLane(after, sel.lane_width, sel.lane_offset);
        vec_transient.last_lane_value = vec_transient.install_lane_after;
        std::memcpy(vec_transient.install_full, after, 16);
        vec_transient.install_full_valid = true;
        vec_transient.latest_generation = generation;
        vec_transient.write_exposures_total = 1;
        vec_transient.reads_total = 0;
        vec_transient.read_events = 0;

        const std::string model =
            sel.bits.size() == 1 ? "FR01" : "FR02";
        const uint64_t lane_mask =
            chaos_vec_transient::laneMask(sel, sel.lane_offset);
        std::ostringstream mask_os;
        mask_os << "0x" << std::hex << std::setw(16) << std::setfill('0')
                << sel.mask_hi << std::setw(16) << sel.mask_lo;

        std::vector<std::pair<std::string, std::string>> kv = {
            {"thread_id", std::to_string((int)tid)},
            {"reg_class", "vec"},
            {"phys_reg", std::to_string(phys_idx)},
            {"arch_reg", arch_idx >= 0 ? std::to_string(arch_idx)
                                       : std::string()},
            {"reg_generation", std::to_string(generation)},
            {"lane_width", std::to_string(sel.lane_width)},
            {"lane_offset", std::to_string(sel.lane_offset)},
            {"bit_in_lane", sel.bits.empty()
                                ? std::string()
                                : std::to_string(sel.bits[0].bit_in_lane)},
            {"lane_mask", propHex(lane_mask)},
            {"bit_indices", bitIndices(sel)},
            {"fault_mask", mask_os.str()},
            {"field", "transient_bit_flip"},
            {"before", propHex(vec_transient.install_lane_before)},
            {"after", propHex(vec_transient.install_lane_after)},
            {"correct_before", propHex(vec_transient.install_lane_before)},
            {"full_before", vec128Hex(before)},
            {"full_after", vec128Hex(after)},
            {"value_hash", propHex(vec_transient.install_lane_after)},
            {"before_hash", propHex(vec_transient.install_lane_before)},
            {"after_hash", propHex(vec_transient.install_lane_after)},
            {"activated", "1"},
            {"contained", "0"},
            {"state_before", "cell_correct"},
            {"state_after", "transient_bit_flipped"},
            {"write_exposures_total", "1"},
            {"read_exposures_total", "0"},
            {"phys_reads", "0"},
            {"sample_policy", "one_shot"},
            {"detection_layer", ""},
        };
        vec_transient.root_event = emitVecModelProp(
            model.c_str(), "F0", "fault_applied",
            vec_transient.fault_id, 0, kv);

        // L1 carrier: the cell/generation exists and holds the flipped value.
        std::vector<std::pair<std::string, std::string>> ckv = {
            {"reg_class", "vec"},
            {"phys_reg", std::to_string(phys_idx)},
            {"reg_generation", std::to_string(generation)},
            {"lane_width", std::to_string(sel.lane_width)},
            {"lane_offset", std::to_string(sel.lane_offset)},
            {"lane_mask", propHex(lane_mask)},
            {"bit_indices", bitIndices(sel)},
            {"fault_mask", mask_os.str()},
            {"before", propHex(vec_transient.install_lane_after)},
            {"after", propHex(vec_transient.install_lane_after)},
            {"cell_allocated", "1"},
            {"install_event", std::to_string(vec_transient.root_event)},
            {"phys_reads", "0"},
            {"state_before", "fault_installed"},
            {"state_after", "carrier_ready"},
        };
        vec_transient.carrier_event = emitVecModelProp(
            model.c_str(), "F0", "carrier_state",
            vec_transient.fault_id, vec_transient.root_event, ckv);
        vec_transient.last_event = vec_transient.carrier_event
                                       ? vec_transient.carrier_event
                                       : vec_transient.root_event;
        registerTransientExitFlush();

        if (write_log && log_stream && log_stream->stream()) {
            *(log_stream->stream())
                << "VecTransientInstall: cycle=" << cpu->curCycle()
                << " fault=" << vec_transient.fault_id
                << " model=" << model
                << " phys=" << phys_idx
                << " gen=" << generation
                << " lane=" << sel.lane_offset
                << " lane_width=" << sel.lane_width
                << " bits=" << bitIndices(sel)
                << " mask=" << mask_os.str()
                << " before=" << propHex(vec_transient.install_lane_before)
                << " after=" << propHex(vec_transient.install_lane_after)
                << std::endl;
        }
    }

    bool
    CHAOSPhysReg::maybeInjectBeforeExecute(o3::DynInst *inst)
    {
        if (!cpu || !inst || !require_ready_consumer ||
            !armed_consumer_injection) {
            return false;
        }
        if (vec_transient.installed ||
            (max_faults != 0 && faults_injected_count >= max_faults)) {
            armed_consumer_injection = false;
            return false;
        }
        if (!inst->staticInst)
            return false;
        // Precision is a property of the INSTRUCTION, not the cell: the same
        // V-cell can be read as S (FP32) or D (FP64).
        if (target_precision != 0 &&
            decodedConsumerPrecision(inst) != target_precision) {
            return false;
        }
        gem5::RegClassType target_class = gem5::IntRegClass;
        if (reg_target_class == RegClassSel::FloatingPoint)
            target_class = gem5::FloatRegClass;
        else if (reg_target_class == RegClassSel::Vector)
            target_class = gem5::VecRegClass;
        else if (reg_target_class == RegClassSel::Both)
            return false;  // ambiguous at the execute boundary
        std::vector<int> cells;
        for (int i = 0; i < inst->numSrcRegs(); ++i) {
            PhysRegIdPtr src = inst->renamedSrcIdx(i);
            if (!src || src->classValue() != target_class ||
                src->isAlwaysReady())
                continue;
            const int idx = (int)src->index();
            const int n =
                (target_class == gem5::FloatRegClass)
                    ? (int)cpu->physRegFile().numFloatPhysRegs()
                    : (target_class == gem5::VecRegClass)
                          ? (int)cpu->physRegFile().numVecPhysRegs()
                          : (int)cpu->physRegFile().numIntPhysRegs();
            if (idx < 0 || idx >= n)
                continue;
            PhysRegIdPtr r =
                (target_class == gem5::FloatRegClass)
                    ? cpu->physRegFile().floatPhysRegId(idx)
                    : (target_class == gem5::VecRegClass)
                          ? cpu->physRegFile().vecPhysRegId(idx)
                          : cpu->physRegFile().intPhysRegId(idx);
            if (cpu->physFreeList().isFree(target_class, r))
                continue;
            if (std::find(cells.begin(), cells.end(), idx) == cells.end())
                cells.push_back(idx);
        }
        if (cells.empty())
            return false;
        const int pick = cells[std::uniform_int_distribution<size_t>(
            0, cells.size() - 1)(rng)];
        forced_target_phys_idx = pick;
        forced_target_valid = true;
        armed_consumer_injection = false;
        last_selected_consumer_sn = inst->seqNum;
        last_selected_precision = decodedConsumerPrecision(inst);
        processFault(inst->threadNumber);
        forced_target_valid = false;
        return vec_transient.installed;
    }

    void
    CHAOSPhysReg::noteVecOperandRead(o3::DynInst *inst, PhysRegIdPtr src,
                                     const void *val)
    {
        if (!cpu || !inst || !vec_transient.installed || !src || !val)
            return;
        if (src->classValue() != VecRegClass)
            return;
        if ((int)src->index() != vec_transient.phys_index)
            return;
        // The value the consumer actually read, captured before any later
        // free/realloc/rewrite of the physical cell. For stores the data
        // operand is read in initiateAcc(), i.e. AFTER the post-execute
        // observer already ran, so this hook must emit the event itself.
        const uint8_t *bytes = (const uint8_t *)val;
        const uint64_t lane_val = readLane(
            bytes, vec_transient.lane_width,
            vec_transient.sel.lane_offset);
        const uint32_t gen = cpu->physRegFile().generationOf(src);
        const uint64_t lane_mask = chaos_vec_transient::laneMask(
            vec_transient.sel, vec_transient.sel.lane_offset);
        // The injected defect modifies the low 128-bit architectural value.
        // Compare the FULL value, not just the target bits: an unrelated
        // value can coincidentally share bit 5 (e.g. 0xcd6c522b).
        const bool same_full = vec_transient.install_full_valid &&
            std::memcmp(bytes, vec_transient.install_full,
                        chaos_vec_transient::kVecBytes) == 0;
        const bool overwritten = vec_transient.overwritten;
        int arch_idx = -1;
        if (inst->staticInst) {
            const int n = std::min((int)inst->numSrcRegs(),
                                   (int)inst->staticInst->numSrcRegs());
            for (int i = 0; i < n; ++i) {
                if (inst->renamedSrcIdx(i) != src)
                    continue;
                const RegId &ar = inst->staticInst->srcRegIdx(i);
                if (ar.classValue() == VecRegClass)
                    arch_idx = (int)ar.index();
                break;
            }
        }
        std::ostringstream mask_os;
        mask_os << "0x" << std::hex << std::setw(16)
                << std::setfill('0') << vec_transient.sel.mask_hi
                << std::setw(16) << vec_transient.sel.mask_lo;

        if (!overwritten) {
            if (vec_transient.read_events >= 4096)
                return;
            ++vec_transient.read_events;
            ++vec_transient.reads_total;
            vec_transient.last_lane_value = lane_val;
            if (vec_transient.first_read_sn == 0)
                vec_transient.first_read_sn = inst->seqNum;
            std::vector<std::pair<std::string, std::string>> kv = {
                {"dyn_inst_seq", std::to_string(inst->seqNum)},
                {"pc", propHex(inst->pcState().instAddr())},
                {"opcode", inst->staticInst
                               ? inst->staticInst->getName() : ""},
                {"thread_id", std::to_string((int)inst->threadNumber)},
                {"reg_class", "vec"},
                {"phys_reg", std::to_string(vec_transient.phys_index)},
                {"arch_reg", arch_idx >= 0 ? std::to_string(arch_idx)
                                           : std::string()},
                {"reg_generation", std::to_string(gen)},
                {"consumer_seq", std::to_string(inst->seqNum)},
                {"lane_width", std::to_string(vec_transient.lane_width)},
                {"lane_offset",
                 std::to_string(vec_transient.sel.lane_offset)},
                {"lane_mask", propHex(lane_mask)},
                {"bit_indices", bitIndices(vec_transient.sel)},
                {"fault_mask", mask_os.str()},
                {"field", "transient_bit_flip"},
                {"before", propHex(lane_val)},
                {"after", propHex(lane_val)},
                {"value_hash", propHex(lane_val)},
                {"activated", same_full ? "1" : "0"},
                {"target_bits_flipped", same_full ? "1" : "0"},
                {"install_event",
                 std::to_string(vec_transient.root_event)},
                {"read_exposures_total",
                 std::to_string(vec_transient.reads_total)},
                {"write_exposures_total",
                 std::to_string(vec_transient.write_exposures_total)},
                {"state_before", "cell_flipped"},
                {"state_after", same_full ? "operand_read_flipped"
                                          : "operand_read_clean"},
            };
            const uint64_t parent = vec_transient.last_event
                                        ? vec_transient.last_event
                                        : vec_transient.root_event;
            const uint64_t eid = emitVecModelProp(
                (vec_transient.sel.bits.size() == 1 ? "FR01" : "FR02"),
                "F0", "operand_read", vec_transient.fault_id, parent, kv);
            if (eid) {
                vec_transient.last_event = eid;
                vec_transient.read_event_sn = inst->seqNum;
                if (same_full)
                    vec_transient.l5.record(inst->seqNum, eid, gen,
                                            lane_val);
                vec_transient.consumers_recorded =
                    vec_transient.l5.consumersRecorded();
            }
        } else {
            ++vec_transient.post_overwrite_reads_total;
            if (vec_transient.post_overwrite_reads_emitted >= 4096)
                return;
            ++vec_transient.post_overwrite_reads_emitted;
            const bool flipped_lane =
                (lane_val & lane_mask) ==
                (vec_transient.install_lane_after & lane_mask);
            if (flipped_lane && same_full)
                ++vec_transient.post_overwrite_affected_reads;
            std::vector<std::pair<std::string, std::string>> kv = {
                {"dyn_inst_seq", std::to_string(inst->seqNum)},
                {"pc", propHex(inst->pcState().instAddr())},
                {"opcode", inst->staticInst
                               ? inst->staticInst->getName() : ""},
                {"thread_id", std::to_string((int)inst->threadNumber)},
                {"reg_class", "vec"},
                {"phys_reg", std::to_string(vec_transient.phys_index)},
                {"arch_reg", arch_idx >= 0 ? std::to_string(arch_idx)
                                           : std::string()},
                {"reg_generation", std::to_string(gen)},
                {"consumer_seq", std::to_string(inst->seqNum)},
                {"lane_width", std::to_string(vec_transient.lane_width)},
                {"lane_offset",
                 std::to_string(vec_transient.sel.lane_offset)},
                {"lane_mask", propHex(lane_mask)},
                {"bit_indices", bitIndices(vec_transient.sel)},
                {"fault_mask", mask_os.str()},
                {"field", "transient_bit_flip"},
                {"before", propHex(lane_val)},
                {"after", propHex(lane_val)},
                {"value_hash", propHex(lane_val)},
                {"activated", "0"},
                {"install_event",
                 std::to_string(vec_transient.root_event)},
                {"post_overwrite_reads_total", std::to_string(
                     vec_transient.post_overwrite_reads_total)},
                {"post_overwrite_reads_emitted", std::to_string(
                     vec_transient.post_overwrite_reads_emitted)},
                {"post_overwrite_affected_reads", std::to_string(
                     vec_transient.post_overwrite_affected_reads)},
                {"target_bits_flipped", flipped_lane ? "1" : "0"},
                {"same_generation", "0"},
                {"state_before", "cell_reallocated"},
                {"state_after", flipped_lane && same_full
                                    ? "affected_read" : "clean_read"},
            };
            const uint64_t parent = vec_transient.last_event
                                        ? vec_transient.last_event
                                        : vec_transient.overwrite_event;
            const uint64_t eid = emitVecModelProp(
                (vec_transient.sel.bits.size() == 1 ? "FR01" : "FR02"),
                "F0", "post_overwrite_read", vec_transient.fault_id,
                parent, kv);
            if (eid) {
                vec_transient.last_event = eid;
                vec_transient.read_event_sn = inst->seqNum;
            }
        }
        if (write_log && log_stream && log_stream->stream()
            && vec_transient.operand_snapshot_count < 16) {
            ++vec_transient.operand_snapshot_count;
            *(log_stream->stream())
                << "VecOperandReadSnapshot: cycle=" << cpu->curCycle()
                << " sn=" << inst->seqNum
                << " pc=" << std::hex << inst->pcState().instAddr()
                << std::dec
                << " op=" << (inst->staticInst
                                  ? inst->staticInst->getName() : "")
                << " phys=" << vec_transient.phys_index
                << " install_gen=" << vec_transient.install_generation
                << " lane=" << propHex(lane_val)
                << " same_full=" << (same_full ? 1 : 0)
                << " overwritten=" << (overwritten ? 1 : 0)
                << std::endl;
        }
    }

    void
    CHAOSPhysReg::observeVecTransient(o3::DynInst *inst)
    {
        if (!cpu || !inst || !vec_transient.installed)
            return;
        auto &rf = cpu->physRegFile();
        const int target = vec_transient.phys_index;
        if (target < 0 || target >= (int)rf.numVecPhysRegs())
            return;
        const size_t bytes = rf.vecRegBytes();
        if (bytes < (size_t)chaos_vec_transient::kVecBytes)
            return;
        std::vector<uint8_t> buf(bytes, 0);
        // [FR01/FR02] Prefer the value captured at the exact operand-read
        // point for THIS instruction. Reading the cell again post-execute can
        // see a different generation (freed/reallocated/rewritten meanwhile).
        auto operandValue = [&](PhysRegIdPtr r) -> std::pair<uint64_t, uint32_t>
        {
            if (vec_transient.operand_snapshot_valid &&
                vec_transient.operand_snapshot_sn == inst->seqNum) {
                return {vec_transient.operand_snapshot_lane,
                        vec_transient.operand_snapshot_gen};
            }
            rf.readVecRegRaw(r, buf.data());
            return {readLane(buf.data(), vec_transient.lane_width,
                             vec_transient.sel.lane_offset),
                    rf.generationOf(r)};
        };
        const std::string model =
            vec_transient.sel.bits.size() == 1 ? "FR01" : "FR02";

        // Does this instruction itself write the target cell? Vector
        // destinations are written through a raw getWritableReg() pointer
        // during execute(), so a same-cell read+write cannot be separated
        // after the fact. Treat the write as the terminal observation and do
        // not manufacture a consumer read from the post-write value.
        bool writes_target = false;
        for (int i = 0; i < (int)inst->numDestRegs(); ++i) {
            PhysRegIdPtr dest = inst->renamedDestIdx(i);
            if (dest && dest->classValue() == VecRegClass &&
                (int)dest->index() == target) {
                writes_target = true;
                break;
            }
        }

        // Lifecycle: a free/realloc changes the cell generation. The old
        // corrupted cell no longer exists, so this is a real terminal, not a
        // missing observation. Emit it once, before any read/write branch.
        const uint32_t current_generation =
            rf.generationOf(rf.vecPhysRegId(target));
        if (!vec_transient.generation_changed &&
            current_generation != vec_transient.install_generation) {
            vec_transient.generation_changed = true;
            vec_transient.latest_generation = current_generation;
            const uint64_t lane_mask = chaos_vec_transient::laneMask(
                vec_transient.sel, vec_transient.sel.lane_offset);
            std::vector<std::pair<std::string, std::string>> gkv = {
                {"reg_class", "vec"},
                {"phys_reg", std::to_string(target)},
                {"reg_generation", std::to_string(current_generation)},
                {"generation_old",
                 std::to_string(vec_transient.install_generation)},
                {"generation_new", std::to_string(current_generation)},
                {"generation_changes", "1"},
                {"lane_width", std::to_string(vec_transient.lane_width)},
                {"lane_offset",
                 std::to_string(vec_transient.sel.lane_offset)},
                {"lane_mask", propHex(lane_mask)},
                {"bit_indices", bitIndices(vec_transient.sel)},
                {"install_event",
                 std::to_string(vec_transient.root_event)},
                {"field", "transient_bit_flip"},
                {"before", propHex(vec_transient.last_lane_value)},
                {"after", propHex(vec_transient.last_lane_value)},
                {"activated", "0"},
                {"state_before", "old_generation_cell"},
                {"state_after", "cell_reallocated"},
            };
            const uint64_t parent = vec_transient.last_event
                                        ? vec_transient.last_event
                                        : vec_transient.root_event;
            const uint64_t eid = emitVecModelProp(
                model.c_str(), "F0", "generation_change",
                vec_transient.fault_id, parent, gkv);
            if (eid) {
                vec_transient.generation_change_event = eid;
                vec_transient.last_event = eid;
            }
        }

        // L2: fallback source-operand observation. The authoritative read
        // event is emitted by noteVecOperandRead() at the exact getRegOperand
        // point. Skip here when that hook already covered this instruction,
        // and never emit for stores: a store's vector data operand is read in
        // initiateAcc(), i.e. AFTER this post-execute observer.
        const bool read_captured =
            vec_transient.read_event_sn == inst->seqNum;
        if (!writes_target && !inst->isStore() && !read_captured) {
            for (int i = 0; i < (int)inst->numSrcRegs(); ++i) {
                PhysRegIdPtr src = inst->renamedSrcIdx(i);
                if (!src || src->classValue() != VecRegClass)
                    continue;
                if ((int)src->index() != target)
                    continue;
                // Generation is provenance, NOT a filter. `generationOf()`
                // reads the cell's CURRENT generation at post-execute time;
                // the cell can be freed/reallocated between the consumer's
                // read (during execute) and this hook. Discarding such a read
                // loses a real consumer: on W1 (v13) the output hash changed
                // while the chain recorded no read and falsely ended in
                // free_realloc. Only a real WRITE to the cell (handled below)
                // removes the flipped value; a generation bump alone does not.
                if (vec_transient.overwritten) {
                    // Post-overwrite visibility: the defect is gone by
                    // construction, but only an observed read proves that no
                    // consumer still sees a flipped target bit.
                    ++vec_transient.post_overwrite_reads_total;
                    if (vec_transient.post_overwrite_reads_emitted >= 4096)
                        continue;
                    ++vec_transient.post_overwrite_reads_emitted;
                    const auto [lane_val, gen] = operandValue(src);
                    const uint64_t lane_mask =
                        chaos_vec_transient::laneMask(
                            vec_transient.sel,
                            vec_transient.sel.lane_offset);
                    const bool flipped_lane =
                        (lane_val & lane_mask) ==
                        (vec_transient.install_lane_after & lane_mask);
                    const bool same_generation =
                        gen == vec_transient.install_generation;
                    if (flipped_lane && same_generation)
                        ++vec_transient.post_overwrite_affected_reads;
                    int arch_idx = -1;
                    if (inst->staticInst &&
                        i < (int)inst->staticInst->numSrcRegs()) {
                        const RegId &ar =
                            inst->staticInst->srcRegIdx(i);
                        if (ar.classValue() == VecRegClass)
                            arch_idx = (int)ar.index();
                    }
                    std::ostringstream mask_os;
                    mask_os << "0x" << std::hex << std::setw(16)
                            << std::setfill('0') << vec_transient.sel.mask_hi
                            << std::setw(16) << vec_transient.sel.mask_lo;
                    std::vector<std::pair<std::string, std::string>> pkv = {
                        {"dyn_inst_seq", std::to_string(inst->seqNum)},
                        {"pc", propHex(inst->pcState().instAddr())},
                        {"opcode", inst->staticInst
                                       ? inst->staticInst->getName() : ""},
                        {"thread_id",
                         std::to_string((int)inst->threadNumber)},
                        {"reg_class", "vec"},
                        {"phys_reg", std::to_string(target)},
                        {"arch_reg", arch_idx >= 0
                                         ? std::to_string(arch_idx)
                                         : std::string()},
                        {"reg_generation", std::to_string(gen)},
                        {"consumer_seq", std::to_string(inst->seqNum)},
                        {"lane_width",
                         std::to_string(vec_transient.lane_width)},
                        {"lane_offset", std::to_string(
                             vec_transient.sel.lane_offset)},
                        {"lane_mask", propHex(lane_mask)},
                        {"bit_indices", bitIndices(vec_transient.sel)},
                        {"fault_mask", mask_os.str()},
                        {"field", "transient_bit_flip"},
                        {"before", propHex(lane_val)},
                        {"after", propHex(lane_val)},
                        {"value_hash", propHex(lane_val)},
                        {"activated", "0"},
                        {"install_event",
                         std::to_string(vec_transient.root_event)},
                        {"post_overwrite_reads_total", std::to_string(
                             vec_transient.post_overwrite_reads_total)},
                        {"post_overwrite_reads_emitted", std::to_string(
                             vec_transient.post_overwrite_reads_emitted)},
                        {"post_overwrite_affected_reads", std::to_string(
                             vec_transient.post_overwrite_affected_reads)},
                        {"target_bits_flipped",
                         flipped_lane ? "1" : "0"},
                        {"same_generation",
                         same_generation ? "1" : "0"},
                        {"state_before", same_generation
                             ? "cell_clean" : "cell_reallocated"},
                        {"state_after", flipped_lane && same_generation
                             ? "affected_read" : "clean_read"},
                    };
                    const uint64_t parent = vec_transient.last_event
                                                ? vec_transient.last_event
                                                : vec_transient.overwrite_event;
                    const uint64_t eid = emitVecModelProp(
                        model.c_str(), "F0", "post_overwrite_read",
                        vec_transient.fault_id, parent, pkv);
                    if (eid)
                        vec_transient.last_event = eid;
                    continue;
                }
                if (vec_transient.read_events >= 4096)
                    continue;
                ++vec_transient.read_events;
                ++vec_transient.reads_total;
                const auto [lane_val, gen] = operandValue(src);
                vec_transient.last_lane_value = lane_val;
                if (vec_transient.first_read_sn == 0)
                    vec_transient.first_read_sn = inst->seqNum;
                int arch_idx = -1;
                if (inst->staticInst &&
                    i < (int)inst->staticInst->numSrcRegs()) {
                    const RegId &ar = inst->staticInst->srcRegIdx(i);
                    if (ar.classValue() == VecRegClass)
                        arch_idx = (int)ar.index();
                }
                const uint64_t lane_mask = chaos_vec_transient::laneMask(
                    vec_transient.sel, vec_transient.sel.lane_offset);
                // `activated` must mean "this read really consumed the
                // flipped bits", not merely "the instruction had the cell as
                // a source". Fallback path: exact lane equality with the
                // installed value in the installed generation (bit-mask
                // equality alone falsely matches unrelated values that share
                // bit 5).
                const bool affected =
                    gen == vec_transient.install_generation &&
                    lane_val == vec_transient.install_lane_after;
                std::vector<std::pair<std::string, std::string>> kv = {
                    {"dyn_inst_seq", std::to_string(inst->seqNum)},
                    {"pc", propHex(inst->pcState().instAddr())},
                    {"opcode", inst->staticInst
                                   ? inst->staticInst->getName() : ""},
                    {"thread_id", std::to_string((int)inst->threadNumber)},
                    {"reg_class", "vec"},
                    {"phys_reg", std::to_string(target)},
                    {"arch_reg", arch_idx >= 0 ? std::to_string(arch_idx)
                                               : std::string()},
                    {"reg_generation", std::to_string(gen)},
                    {"consumer_seq", std::to_string(inst->seqNum)},
                    {"lane_width", std::to_string(vec_transient.lane_width)},
                    {"lane_offset",
                     std::to_string(vec_transient.sel.lane_offset)},
                    {"bit_in_lane", vec_transient.sel.bits.empty()
                                        ? std::string()
                                        : std::to_string(
                                              vec_transient.sel.bits[0]
                                                  .bit_in_lane)},
                    {"lane_mask", propHex(lane_mask)},
                    {"bit_indices", bitIndices(vec_transient.sel)},
                    {"field", "transient_bit_flip"},
                    {"before", propHex(lane_val)},
                    {"after", propHex(lane_val)},
                    {"value_hash", propHex(lane_val)},
                    {"activated", affected ? "1" : "0"},
                    {"target_bits_flipped", affected ? "1" : "0"},
                    {"install_event",
                     std::to_string(vec_transient.root_event)},
                    {"read_exposures_total",
                     std::to_string(vec_transient.reads_total)},
                    {"write_exposures_total",
                     std::to_string(vec_transient.write_exposures_total)},
                    {"phys_reads",
                     std::to_string(rf.getReadsBeforeOverwrite())},
                    {"state_before", "cell_flipped"},
                    {"state_after", affected ? "operand_read_flipped"
                                             : "operand_read_clean"},
                };
                const uint64_t parent = vec_transient.last_event
                                            ? vec_transient.last_event
                                            : vec_transient.root_event;
                const uint64_t eid = emitVecModelProp(
                    model.c_str(), "F0", "operand_read",
                    vec_transient.fault_id, parent, kv);
                if (eid) {
                    vec_transient.last_event = eid;
                    // Only a read that really saw the flipped target bits is
                    // an L5 consumer. A clean read of the cell (e.g. after a
                    // reallocation) must not produce a false commit witness.
                    if (!vec_transient.overwritten && affected)
                        vec_transient.l5.record(inst->seqNum, eid, gen,
                                                lane_val);
                    vec_transient.consumers_recorded =
                        vec_transient.l5.consumersRecorded();
                }
            }
        }

        // L1 overwrite: a real program write replaces the transient value.
        // Nothing is re-applied; the defect ends here.
        bool overwrote_now = false;
        if (!vec_transient.overwritten) {
            for (int i = 0; i < (int)inst->numDestRegs(); ++i) {
                PhysRegIdPtr dest = inst->renamedDestIdx(i);
                if (!dest || dest->classValue() != VecRegClass)
                    continue;
                if ((int)dest->index() != target)
                    continue;
                const uint32_t gen = rf.generationOf(dest);
                // ANY real write to the physical cell removes the transient
                // value, whether or not the cell was freed/reallocated in
                // between. The old generation-based filter left a reallocated
                // cell's write untracked, so later reads were misclassified.
                // `generation_old/new` below records the lifecycle provenance.
                rf.readVecRegRaw(dest, buf.data());
                const uint64_t after_val = readLane(
                    buf.data(), vec_transient.lane_width,
                    vec_transient.sel.lane_offset);
                const uint64_t before_val = vec_transient.last_lane_value;
                vec_transient.last_lane_value = after_val;
                vec_transient.overwritten = true;
                vec_transient.overwrite_sn = inst->seqNum;
                vec_transient.overwrite_tick = curTick();
                vec_transient.write_exposures_total = 2;
                // Vector dest writes bypass setReg(); freeze the container
                // read-trace so the L0 line never counts post-overwrite reads
                // as reads of the injected value.
                rf.noteTraceOverwrite();
                int arch_idx = -1;
                if (inst->staticInst &&
                    i < (int)inst->staticInst->numDestRegs()) {
                    const RegId &ar = inst->staticInst->destRegIdx(i);
                    if (ar.classValue() == VecRegClass)
                        arch_idx = (int)ar.index();
                }
                const uint64_t lane_mask = chaos_vec_transient::laneMask(
                    vec_transient.sel, vec_transient.sel.lane_offset);
                const uint64_t target_bits_before =
                    vec_transient.install_lane_after & lane_mask;
                const uint64_t target_bits_after = after_val & lane_mask;
                std::ostringstream mask_os;
                mask_os << "0x" << std::hex << std::setw(16)
                        << std::setfill('0') << vec_transient.sel.mask_hi
                        << std::setw(16) << vec_transient.sel.mask_lo;
                std::vector<std::pair<std::string, std::string>> kv = {
                    {"dyn_inst_seq", std::to_string(inst->seqNum)},
                    {"pc", propHex(inst->pcState().instAddr())},
                    {"opcode", inst->staticInst
                                   ? inst->staticInst->getName() : ""},
                    {"thread_id", std::to_string((int)inst->threadNumber)},
                    {"reg_class", "vec"},
                    {"phys_reg", std::to_string(target)},
                    {"arch_reg", arch_idx >= 0 ? std::to_string(arch_idx)
                                               : std::string()},
                    {"reg_generation", std::to_string(gen)},
                    {"generation_old",
                     std::to_string(vec_transient.install_generation)},
                    {"generation_new", std::to_string(gen)},
                    {"producer_seq", std::to_string(inst->seqNum)},
                    {"lane_width", std::to_string(vec_transient.lane_width)},
                    {"lane_offset",
                     std::to_string(vec_transient.sel.lane_offset)},
                    {"bit_in_lane", vec_transient.sel.bits.empty()
                                        ? std::string()
                                        : std::to_string(
                                              vec_transient.sel.bits[0]
                                                  .bit_in_lane)},
                    {"lane_mask", propHex(lane_mask)},
                    {"bit_indices", bitIndices(vec_transient.sel)},
                    {"fault_mask", mask_os.str()},
                    {"field", "transient_bit_flip"},
                    {"before", propHex(before_val)},
                    {"after", propHex(after_val)},
                    {"value_hash", propHex(after_val)},
                    {"full_before",
                     vec_transient.install_full_valid
                         ? vec128Hex(vec_transient.install_full)
                         : std::string()},
                    {"full_after", vec128Hex(buf.data())},
                    {"target_bits_before", propHex(target_bits_before)},
                    {"target_bits_after", propHex(target_bits_after)},
                    {"target_bits_restored",
                     target_bits_after != target_bits_before ? "1" : "0"},
                    {"activated", "1"},
                    {"install_event",
                     std::to_string(vec_transient.root_event)},
                    {"read_exposures_total",
                     std::to_string(vec_transient.reads_total)},
                    {"write_exposures_total",
                     std::to_string(vec_transient.write_exposures_total)},
                    {"phys_reads",
                     std::to_string(rf.getReadsBeforeOverwrite())},
                    {"detection_layer", "L1"},
                    {"contained", "1"},
                    {"containment_layer", "L1"},
                    {"containment_reason", "phys_cell_rewritten"},
                    {"outcome", "contained"},
                    {"state_before", "transient_flipped"},
                    {"state_after", "overwritten_by_real_write"},
                };
                const uint64_t parent = vec_transient.last_event
                                            ? vec_transient.last_event
                                            : vec_transient.root_event;
                const uint64_t eid = emitVecModelProp(
                    model.c_str(), "F0", "overwrite",
                    vec_transient.fault_id, parent, kv);
                if (eid) {
                    vec_transient.overwrite_event = eid;
                    vec_transient.last_event = eid;
                }
                overwrote_now = true;
                if (write_log && log_stream && log_stream->stream()) {
                    *(log_stream->stream())
                        << "VecTransientOverwrite: cycle=" << cpu->curCycle()
                        << " fault=" << vec_transient.fault_id
                        << " phys=" << target
                        << " gen=" << gen
                        << " sn=" << inst->seqNum
                        << " before=" << propHex(before_val)
                        << " after=" << propHex(after_val)
                        << " (transient terminated; no re-apply)"
                        << std::endl;
                }
                break;
            }
        }

        // Consecutive writes after the terminating overwrite: prove the
        // transient is never re-applied. The C++ never arms a write-path
        // mask, but only observed post-overwrite writes make that claim
        // auditable.
        if (!overwrote_now && vec_transient.overwritten && writes_target) {
            for (int i = 0; i < (int)inst->numDestRegs(); ++i) {
                PhysRegIdPtr dest = inst->renamedDestIdx(i);
                if (!dest || dest->classValue() != VecRegClass)
                    continue;
                if ((int)dest->index() != target)
                    continue;
                ++vec_transient.post_overwrite_writes_total;
                if (vec_transient.post_overwrite_writes_emitted >= 64)
                    break;
                ++vec_transient.post_overwrite_writes_emitted;
                const uint32_t gen = rf.generationOf(dest);
                rf.readVecRegRaw(dest, buf.data());
                const uint64_t after_val = readLane(
                    buf.data(), vec_transient.lane_width,
                    vec_transient.sel.lane_offset);
                const uint64_t lane_mask = chaos_vec_transient::laneMask(
                    vec_transient.sel, vec_transient.sel.lane_offset);
                const bool flipped_lane =
                    (after_val & lane_mask) ==
                    (vec_transient.install_lane_after & lane_mask);
                if (flipped_lane)
                    ++vec_transient.post_overwrite_writes_affected;
                std::vector<std::pair<std::string, std::string>> wkv = {
                    {"dyn_inst_seq", std::to_string(inst->seqNum)},
                    {"pc", propHex(inst->pcState().instAddr())},
                    {"opcode", inst->staticInst
                                   ? inst->staticInst->getName() : ""},
                    {"thread_id", std::to_string((int)inst->threadNumber)},
                    {"reg_class", "vec"},
                    {"phys_reg", std::to_string(target)},
                    {"reg_generation", std::to_string(gen)},
                    {"lane_width", std::to_string(vec_transient.lane_width)},
                    {"lane_offset",
                     std::to_string(vec_transient.sel.lane_offset)},
                    {"lane_mask", propHex(lane_mask)},
                    {"bit_indices", bitIndices(vec_transient.sel)},
                    {"field", "transient_bit_flip"},
                    {"before", propHex(after_val)},
                    {"after", propHex(after_val)},
                    {"value_hash", propHex(after_val)},
                    {"activated", "0"},
                    {"install_event",
                     std::to_string(vec_transient.root_event)},
                    {"post_overwrite_writes_total", std::to_string(
                         vec_transient.post_overwrite_writes_total)},
                    {"post_overwrite_writes_emitted", std::to_string(
                         vec_transient.post_overwrite_writes_emitted)},
                    {"post_overwrite_writes_affected", std::to_string(
                         vec_transient.post_overwrite_writes_affected)},
                    {"target_bits_flipped", flipped_lane ? "1" : "0"},
                    {"state_before", "cell_clean"},
                    {"state_after", flipped_lane ? "reapplied"
                                                 : "clean_write"},
                };
                const uint64_t parent = vec_transient.last_event
                                            ? vec_transient.last_event
                                            : vec_transient.overwrite_event;
                const uint64_t eid = emitVecModelProp(
                    model.c_str(), "F0", "write_after_overwrite",
                    vec_transient.fault_id, parent, wkv);
                if (eid)
                    vec_transient.last_event = eid;
                break;
            }
        }
    }

    void
    CHAOSPhysReg::noteVecTransientCommit(ThreadID tid, o3::DynInst *inst)
    {
        if (!vec_transient.installed)
            return;
        const auto r = vec_transient.l5.noteCommit(inst->seqNum);
        if (!r.matched)
            return;
        vec_transient.commit_events = vec_transient.l5.commitEvents();
        vec_transient.consumers_recorded =
            vec_transient.l5.consumersRecorded();
        if (vec_transient.first_impact_sn == 0) {
            vec_transient.first_impact_sn = inst->seqNum;
            vec_transient.first_impact_tick = curTick();
            const uint64_t basis = vec_transient.install_tick;
            vec_transient.first_impact_latency =
                (basis != 0 && curTick() >= basis)
                    ? (uint64_t)(curTick() - basis) : 0;
        }
        const std::string model =
            vec_transient.sel.bits.size() == 1 ? "FR01" : "FR02";
        const uint64_t lane_mask = chaos_vec_transient::laneMask(
            vec_transient.sel, vec_transient.sel.lane_offset);
        std::vector<std::pair<std::string, std::string>> kv = {
            {"consumer_seq", std::to_string(inst->seqNum)},
            {"dyn_inst_seq", std::to_string(inst->seqNum)},
            {"commit_seq", std::to_string(r.ordinal)},
            {"thread_id", std::to_string((int)tid)},
            {"pc", propHex(inst->pcState().instAddr())},
            {"opcode", inst->staticInst ? inst->staticInst->getName() : ""},
            {"reg_class", "vec"},
            {"phys_reg", std::to_string(vec_transient.phys_index)},
            {"reg_generation", std::to_string(r.generation)},
            {"lane_width", std::to_string(vec_transient.lane_width)},
            {"lane_offset", std::to_string(vec_transient.sel.lane_offset)},
            {"lane_mask", propHex(lane_mask)},
            {"bit_indices", bitIndices(vec_transient.sel)},
            {"install_event", std::to_string(vec_transient.root_event)},
            {"field", "transient_bit_flip"},
            {"before", propHex(r.value)},
            {"after", propHex(r.value)},
            {"value_hash", propHex(r.value)},
            {"activated", "1"},
            {"read_exposures_total",
             std::to_string(vec_transient.reads_total)},
            {"write_exposures_total",
             std::to_string(vec_transient.write_exposures_total)},
            {"commit_events", std::to_string(vec_transient.commit_events)},
            {"squash_events", std::to_string(vec_transient.squash_events)},
            {"consumers_recorded",
             std::to_string(vec_transient.consumers_recorded)},
            {"first_impact_sn",
             std::to_string(vec_transient.first_impact_sn)},
            {"first_impact_tick",
             std::to_string(vec_transient.first_impact_tick)},
            {"first_impact_latency",
             std::to_string(vec_transient.first_impact_latency)},
            {"detection_layer", "L5"},
            {"outcome", "errant_commit"},
            {"contained", "0"},
            {"state_before", "operand_read_flipped"},
            {"state_after", "committed"},
        };
        const uint64_t eid = emitVecModelProp(
            model.c_str(), "F0", "commit", vec_transient.fault_id,
            r.l2_event, kv);
        if (eid) {
            vec_transient.last_event = eid;
            if (vec_transient.l5_witness_event == 0)
                vec_transient.l5_witness_event = eid;
        }
    }

    void
    CHAOSPhysReg::noteVecTransientSquash(ThreadID tid, o3::DynInst *inst)
    {
        if (!vec_transient.installed)
            return;
        const auto r = vec_transient.l5.noteSquash(inst->seqNum);
        if (!r.matched)
            return;
        vec_transient.squash_events = vec_transient.l5.squashEvents();
        vec_transient.commit_events = vec_transient.l5.commitEvents();
        vec_transient.consumers_recorded =
            vec_transient.l5.consumersRecorded();
        const std::string model =
            vec_transient.sel.bits.size() == 1 ? "FR01" : "FR02";
        const uint64_t lane_mask = chaos_vec_transient::laneMask(
            vec_transient.sel, vec_transient.sel.lane_offset);
        std::vector<std::pair<std::string, std::string>> kv = {
            {"consumer_seq", std::to_string(inst->seqNum)},
            {"dyn_inst_seq", std::to_string(inst->seqNum)},
            {"thread_id", std::to_string((int)tid)},
            {"pc", propHex(inst->pcState().instAddr())},
            {"opcode", inst->staticInst ? inst->staticInst->getName() : ""},
            {"reg_class", "vec"},
            {"phys_reg", std::to_string(vec_transient.phys_index)},
            {"reg_generation", std::to_string(r.generation)},
            {"lane_width", std::to_string(vec_transient.lane_width)},
            {"lane_offset", std::to_string(vec_transient.sel.lane_offset)},
            {"lane_mask", propHex(lane_mask)},
            {"bit_indices", bitIndices(vec_transient.sel)},
            {"install_event", std::to_string(vec_transient.root_event)},
            {"field", "transient_bit_flip"},
            {"before", propHex(r.value)},
            {"after", propHex(r.value)},
            {"value_hash", propHex(r.value)},
            {"squashed", "1"},
            {"squash_events", std::to_string(vec_transient.squash_events)},
            {"commit_events", std::to_string(vec_transient.commit_events)},
            {"read_exposures_total",
             std::to_string(vec_transient.reads_total)},
            {"write_exposures_total",
             std::to_string(vec_transient.write_exposures_total)},
            {"detection_layer", ""},
            {"outcome", "squashed"},
            {"contained", "0"},
            {"state_before", "operand_read_flipped"},
            {"state_after", "squashed"},
        };
        const uint64_t eid = emitVecModelProp(
            model.c_str(), "F0", "squash", vec_transient.fault_id,
            r.l2_event, kv);
        if (eid)
            vec_transient.last_event = eid;
    }

    void
    CHAOSPhysReg::finalizeVecTransient(const char *terminal_override)
    {
        if (!vec_transient.installed)
            return;
        const std::string model =
            vec_transient.sel.bits.size() == 1 ? "FR01" : "FR02";
        std::string terminal;
        if (terminal_override && *terminal_override) {
            terminal = terminal_override;
        } else if (vec_transient.l5.commitEvents() > 0) {
            terminal = "committed";
        } else if (vec_transient.overwritten) {
            terminal = "overwritten";
        } else if (vec_transient.l5.squashEvents() > 0) {
            // A squashed consumer is its own terminal; it used to be folded
            // into exposed_unconsumed/not_consumed and became unauditable.
            terminal = "squashed";
        } else if (vec_transient.reads_total > 0) {
            // A real consumer read outranks a later free/realloc: the cell
            // lifecycle ended, but the fault was exposed first. Ordering
            // free_realloc above reads made the W1 v13 SDC (hash changed)
            // look contained.
            terminal = "exposed_unconsumed";
        } else if (vec_transient.generation_changed) {
            terminal = "free_realloc";
        } else {
            terminal = "not_consumed";
        }
        const bool committed = terminal == "committed";
        const bool contained = terminal == "overwritten";
        auto &rf = cpu->physRegFile();
        std::vector<std::pair<std::string, std::string>> kv = {
            {"reg_class", "vec"},
            {"phys_reg", std::to_string(vec_transient.phys_index)},
            {"reg_generation",
             std::to_string(vec_transient.install_generation)},
            {"lane_width", std::to_string(vec_transient.lane_width)},
            {"lane_offset",
             std::to_string(vec_transient.sel.lane_offset)},
            {"lane_mask", propHex(chaos_vec_transient::laneMask(
                              vec_transient.sel,
                              vec_transient.sel.lane_offset))},
            {"bit_indices", bitIndices(vec_transient.sel)},
            {"install_event", std::to_string(vec_transient.root_event)},
            {"field", "transient_bit_flip"},
            {"terminal", terminal},
            {"outcome", committed ? "errant_commit_seen"
                          : contained ? "detected_contained"
                          : terminal == "squashed" ? "squashed"
                          : terminal == "free_realloc" ? "released"
                                      : "run_end"},
            // chain_end is a lifecycle marker, never a layer claim (the
            // checker rejects chain_end with detection_layer=L5).
            {"detection_layer", ""},
            {"contained", contained ? "1" : "0"},
            {"read_exposures_total",
             std::to_string(vec_transient.reads_total)},
            {"write_exposures_total",
             std::to_string(vec_transient.write_exposures_total)},
            {"phys_reads",
             std::to_string(rf.getReadsBeforeOverwrite())},
            {"commit_events", std::to_string(vec_transient.l5.commitEvents())},
            {"squash_events", std::to_string(vec_transient.l5.squashEvents())},
            {"post_overwrite_reads_total",
             std::to_string(vec_transient.post_overwrite_reads_total)},
            {"post_overwrite_reads_emitted",
             std::to_string(vec_transient.post_overwrite_reads_emitted)},
            {"post_overwrite_affected_reads",
             std::to_string(vec_transient.post_overwrite_affected_reads)},
            {"post_overwrite_writes_total",
             std::to_string(vec_transient.post_overwrite_writes_total)},
            {"post_overwrite_writes_emitted",
             std::to_string(vec_transient.post_overwrite_writes_emitted)},
            {"post_overwrite_writes_affected",
             std::to_string(vec_transient.post_overwrite_writes_affected)},
            {"generation_changes",
             vec_transient.generation_changed ? "1" : "0"},
            {"consumers_recorded",
             std::to_string(vec_transient.l5.consumersRecorded())},
            {"first_impact_sn",
             std::to_string(vec_transient.first_impact_sn)},
            {"first_impact_tick",
             std::to_string(vec_transient.first_impact_tick)},
            {"first_impact_latency",
             std::to_string(vec_transient.first_impact_latency)},
            {"l5_witness_event",
             std::to_string(vec_transient.l5_witness_event)},
            {"affected_sn", std::to_string(vec_transient.overwrite_sn)},
            {"state_before", "transient_lifecycle"},
            {"state_after", terminal},
        };
        emitVecModelProp(model.c_str(), "F0", "chain_end",
                         vec_transient.fault_id,
                         vec_transient.last_event, kv);
        vec_transient.installed = false;
    }

    void
    CHAOSPhysReg::noteVecStuckInstalled(
        uint32_t generation, uint64_t correct_lane,
        uint64_t stuck_lane, bool cell_allocated)
    {
        auto &rf = cpu->physRegFile();
        const auto &t = rf.vec_stuck;
        const bool already_registered = vec_emit.exit_flush_registered;
        vec_emit = VecStuckEmission();
        vec_emit.exit_flush_registered = already_registered;
        vec_emit.installed = true;
        vec_emit.fault_id = next_fsu_fault_id++;
        vec_emit.install_generation = generation;
        vec_emit.observed_generation = generation;
        vec_emit.install_tick = curTick();
        vec_emit.reads_total = rf.getVecStuckReads();
        vec_emit.reads_reported = vec_emit.reads_total;
        vec_emit.read_exposures_total = vec_emit.reads_total;
        // A fresh installation starts a fresh L5 ledger: consumers from a
        // previous fault never enter this chain.
        l5.reset();
        // The installation write itself is exposure #1 of generation 0.
        vec_emit.exposure_id = 1;
        vec_emit.exposures_total = 1;
        vec_emit.exposures_sampled = 1;
        vec_emit.write_exposures_total = 1;
        const bool activated = !chaos_vec_stuck::satisfied(
            correct_lane, t.lane_mask, t.polarity);
        if (activated) {
            vec_emit.activated_total = 1;
            vec_emit.activated_events = 1;
            vec_emit.first_activated_emitted = true;
            vec_emit.first_activated_tick = curTick();
            vec_emit.last_exposure_sn = 0;
        }

        std::vector<std::pair<std::string, std::string>> kv = {
            {"reg_class", vecRegClassName(t.reg_class)},
            {"phys_reg", std::to_string(t.phys_index)},
            {"reg_generation", std::to_string(generation)},
            {"lane_width", std::to_string(t.lane_width)},
            {"lane_offset", std::to_string(t.lane_offset)},
            {"bit_in_lane", std::to_string(t.bit_in_lane)},
            {"lane_mask", propHex(t.lane_mask)},
            {"lane_mask_scope", "lane"},
            {"fixed_mask", propHex(t.lane_mask)},
            {"fault_mask", propHex(t.lane_mask)},
            {"bit_indices",
             std::to_string(t.lane_offset * t.lane_width + t.bit_in_lane)},
            {"precision", "fp32"},
            {"stuck_polarity", std::to_string((int)t.polarity)},
            {"field", "permanent_stuck"},
            {"correct_before", propHex(correct_lane)},
            {"stuck_after", propHex(stuck_lane)},
            {"before", propHex(correct_lane)},
            {"after", propHex(stuck_lane)},
            {"activated", activated ? "1" : "0"},
            {"exposure_id", "1"},
            {"exposure_count", "1"},
            {"activated_exposure_count", activated ? "1" : "0"},
            {"first_activated_at_install", activated ? "1" : "0"},
            {"exposures_total", "1"},
            {"exposures_sampled", "1"},
            {"exposures_dropped", "0"},
            {"write_exposures_total", "1"},
            {"read_exposures_total",
             std::to_string(vec_emit.read_exposures_total)},
            {"generation_changes", "0"},
            {"cell_allocated", cell_allocated ? "1" : "0"},
            {"cell_free", cell_allocated ? "0" : "1"},
            {"stuck_reapplied", "1"},
            {"install_is_exposure", "1"},
            {"sample_policy", "first_of_generation+first_activated+cap"},
            {"state_before", "warmup_cell"},
            {"state_after", "fault_installed"},
        };
        vec_emit.install_event =
            emitFsuProp("fault_installed", vec_emit.fault_id, 0, kv);

        // [FR03] The installation write is exposure #1. Emit it as an
        // explicit branch event (same contract as FP06's first exposure) so
        // `exposures_sampled` always equals the number of exposure events in
        // the stream. Its dyn_inst_seq is genuinely unknown (installation
        // happens on an event, not an instruction); first_activated_sn stays
        // empty and `first_activated_at_install=1` records the distinction.
        std::vector<std::pair<std::string, std::string>> ekv = kv;
        ekv.push_back(
            {"install_event", std::to_string(vec_emit.install_event)});
        ekv.push_back({"dyn_inst_seq", ""});
        ekv.push_back({"consumer_seq", ""});
        ekv.push_back({"producer_seq", ""});
        emitFsuProp("exposure", vec_emit.fault_id,
                    vec_emit.install_event, ekv);

        std::vector<std::pair<std::string, std::string>> ckv = {
            {"reg_class", vecRegClassName(t.reg_class)},
            {"phys_reg", std::to_string(t.phys_index)},
            {"reg_generation", std::to_string(generation)},
            {"lane_width", std::to_string(t.lane_width)},
            {"lane_offset", std::to_string(t.lane_offset)},
            {"bit_in_lane", std::to_string(t.bit_in_lane)},
            {"lane_mask", propHex(t.lane_mask)},
            {"lane_mask_scope", "lane"},
            {"fixed_mask", propHex(t.lane_mask)},
            {"fault_mask", propHex(t.lane_mask)},
            {"bit_indices",
             std::to_string(t.lane_offset * t.lane_width + t.bit_in_lane)},
            {"precision", "fp32"},
            {"stuck_polarity", std::to_string((int)t.polarity)},
            {"field", "permanent_stuck"},
            {"before", propHex(stuck_lane)},
            {"after", propHex(stuck_lane)},
            {"activated", activated ? "1" : "0"},
            {"install_event", std::to_string(vec_emit.install_event)},
            {"cell_allocated", cell_allocated ? "1" : "0"},
            {"cell_free", cell_allocated ? "0" : "1"},
            {"state_before", "allocated"},
            {"state_after", "carrier_armed"},
        };
        const uint64_t carrier =
            emitFsuProp("carrier_state", vec_emit.fault_id, 0, ckv);
        vec_emit.generation_root_event =
            vec_emit.install_event ? vec_emit.install_event : carrier;
        vec_emit.last_carrier_event = carrier;
        vec_emit.last_event = carrier ? carrier : vec_emit.install_event;
        registerVecExitFlush();

        if (write_log && log_stream && log_stream->stream()) {
            std::ostringstream os;
            os << "VecStuckInstall: cycle=" << cpu->curCycle()
               << " fault=" << vec_emit.fault_id
               << " phys=" << t.phys_index
               << " gen=" << generation
               << " lane=" << t.lane_offset
               << " mask=0x" << std::hex << t.lane_mask
               << " polarity=" << (int)t.polarity << std::dec
               << " correct=0x" << std::hex << correct_lane
               << " stuck=0x" << stuck_lane << std::dec
               << " activated=" << (activated ? 1 : 0) << std::endl;
            *(log_stream->stream()) << os.str();
        }
    }

    void
    CHAOSPhysReg::observeVecGeneration(uint32_t generation)
    {
        if (!vec_emit.installed || generation == vec_emit.observed_generation)
            return;
        auto &rf = cpu->physRegFile();
        if (rf.vec_stuck.phys_index < 0 ||
            rf.vec_stuck.phys_index >= (int)rf.numVecPhysRegs())
            return;
        const uint32_t old_generation = vec_emit.observed_generation;
        const auto &t = rf.vec_stuck;
        PhysRegIdPtr target_reg = rf.vecPhysRegId(t.phys_index);
        const bool free_now =
            cpu->physFreeList().isFree(VecRegClass, target_reg);
        ++vec_emit.generation_changes;
        vec_emit.observed_generation = generation;
        // A new allocation generation gets a fresh exposure chain. The
        // per-generation exposure_id restarts; no old producer/consumer edge
        // is joined to the new generation.
        vec_emit.exposure_id = 0;
        if (vec_emit.generation_changes_sampled < kVecGenerationEventCap) {
            std::vector<std::pair<std::string, std::string>> kv = {
                {"reg_class", vecRegClassName(t.reg_class)},
                {"phys_reg", std::to_string(t.phys_index)},
                {"reg_generation", std::to_string(generation)},
                {"generation_old", std::to_string(old_generation)},
                {"generation_new", std::to_string(generation)},
                {"generation_changes",
                 std::to_string(vec_emit.generation_changes)},
                {"lane_width", std::to_string(t.lane_width)},
                {"lane_offset", std::to_string(t.lane_offset)},
                {"bit_in_lane", std::to_string(t.bit_in_lane)},
                {"lane_mask", propHex(t.lane_mask)},
                {"fixed_mask", propHex(t.lane_mask)},
                {"stuck_polarity", std::to_string((int)t.polarity)},
                {"field", "permanent_stuck"},
                {"cell_free", free_now ? "1" : "0"},
                {"cell_allocated", free_now ? "0" : "1"},
                {"install_event", std::to_string(vec_emit.install_event)},
                {"state_before", "allocated_generation"},
                {"state_after", free_now ? "freed" : "reallocated"},
                {"activated", ""},
            };
            // Lifecycle link only (old generation's chain root); the new
            // generation's producer/consumer edges start from here.
            const uint64_t parent = vec_emit.generation_root_event;
            const uint64_t eid =
                emitFsuProp("generation_change", vec_emit.fault_id,
                            parent, kv);
            // The new generation's L2/L5 chain roots at this lifecycle
            // event. Never reuse the old generation's carrier as parent,
            // even when the generation_change sample cap dropped this event.
            vec_emit.last_carrier_event = 0;
            if (eid) {
                ++vec_emit.generation_changes_sampled;
                vec_emit.generation_root_event = eid;
            }
        }
    }

    void
    CHAOSPhysReg::noteVecStuckCarrier(uint32_t generation,
                                      PhysRegIdPtr phys_reg)
    {
        if (!vec_emit.installed || !phys_reg)
            return;
        auto &rf = cpu->physRegFile();
        const uint64_t reads = rf.getVecStuckReads();
        if (reads <= vec_emit.reads_reported)
            return;
        const uint64_t delta = reads - vec_emit.reads_reported;
        vec_emit.reads_total = reads;
        vec_emit.reads_reported = reads;
        if (vec_emit.read_events >= kVecReadEventCap)
            return;
        ++vec_emit.read_events;
        const auto &t = rf.vec_stuck;
        const size_t bytes = rf.vecRegBytes();
        uint64_t lane = 0;
        if (bytes >= 16) {
            std::vector<uint8_t> buf(bytes, 0);
            rf.readVecRegRaw(phys_reg, buf.data());
            const int lane_bytes = t.lane_width / 8;
            const int base = t.lane_offset * lane_bytes;
            if (base + lane_bytes <= (int)bytes)
                std::memcpy(&lane, buf.data() + base, lane_bytes);
        }
        std::vector<std::pair<std::string, std::string>> kv = {
            {"reg_class", vecRegClassName(t.reg_class)},
            {"phys_reg", std::to_string(t.phys_index)},
            {"reg_generation", std::to_string(generation)},
            {"lane_width", std::to_string(t.lane_width)},
            {"lane_offset", std::to_string(t.lane_offset)},
            {"bit_in_lane", std::to_string(t.bit_in_lane)},
            {"lane_mask", propHex(t.lane_mask)},
            {"fixed_mask", propHex(t.lane_mask)},
            {"stuck_polarity", std::to_string((int)t.polarity)},
            {"field", "permanent_stuck"},
            {"before", propHex(lane)},
            {"after", propHex(lane)},
            {"phys_reads", std::to_string(reads)},
            {"phys_reads_delta", std::to_string(delta)},
            {"read_exposures_total", std::to_string(reads)},
            {"write_exposures_total",
             std::to_string(vec_emit.write_exposures_total)},
            {"cell_allocated", "1"},
            {"state_before", "written_stuck"},
            {"state_after", "read"},
        };
        const uint64_t eid =
            emitFsuProp("carrier_state", vec_emit.fault_id,
                        vec_emit.generation_root_event, kv);
        if (eid)
            vec_emit.last_carrier_event = eid;
    }

    void
    CHAOSPhysReg::emitVecTerminal()
    {
        if (!vec_emit.installed)
            return;
        auto &rf = cpu->physRegFile();
        // Flush the final read/carrier delta before the terminal.
        if (rf.vec_stuck.valid &&
            rf.vec_stuck.phys_index >= 0 &&
            rf.vec_stuck.phys_index < (int)rf.numVecPhysRegs()) {
            const uint32_t gen =
                rf.generationOf(rf.vecPhysRegId(rf.vec_stuck.phys_index));
            observeVecGeneration(gen);
            noteVecStuckCarrier(gen, rf.vecPhysRegId(rf.vec_stuck.phys_index));
        }
        vec_emit.exposures_dropped =
            vec_emit.exposures_total - vec_emit.exposures_sampled;
        // Exact final counters. Reads and writes are never merged:
        //   write_exposures_total = installation write + every re-apply
        //   read_exposures_total  = every real consumer read of the cell
        vec_emit.write_exposures_total = vec_emit.exposures_total;
        vec_emit.read_exposures_total = vec_emit.reads_total;
        vec_emit.commit_events = l5.commitEvents();
        vec_emit.squash_events = l5.squashEvents();
        vec_emit.consumers_recorded = l5.consumersRecorded();
        // Honest terminal. "committed" requires a REAL L5 commit event; a
        // squash is never promoted to a commit, and a squash does not clear
        // the permanent defect (clearPermanentFaults below is run-end only).
        const char *terminal = l5.terminal(vec_emit.activated_total);
        std::vector<std::pair<std::string, std::string>> kv = {
            {"reg_class", "vec"},
            {"phys_reg", std::to_string(rf.vec_stuck.phys_index)},
            {"reg_generation",
             std::to_string(vec_emit.observed_generation)},
            {"generation_changes",
             std::to_string(vec_emit.generation_changes)},
            {"lane_width", std::to_string(rf.vec_stuck.lane_width)},
            {"lane_offset", std::to_string(rf.vec_stuck.lane_offset)},
            {"bit_in_lane", std::to_string(rf.vec_stuck.bit_in_lane)},
            {"lane_mask", propHex(rf.vec_stuck.lane_mask)},
            {"fixed_mask", propHex(rf.vec_stuck.lane_mask)},
            {"stuck_polarity", std::to_string((int)rf.vec_stuck.polarity)},
            {"field", "permanent_stuck"},
            {"install_event", std::to_string(vec_emit.install_event)},
            {"exposure_count", std::to_string(vec_emit.exposures_total)},
            {"exposures_total", std::to_string(vec_emit.exposures_total)},
            {"exposures_sampled", std::to_string(vec_emit.exposures_sampled)},
            {"exposures_dropped", std::to_string(vec_emit.exposures_dropped)},
            {"activated_exposure_count",
             std::to_string(vec_emit.activated_total)},
            // Empty when the only activation was the installation write
            // (it has no instruction seqNum); never fabricate a zero SN.
            {"first_activated_sn",
             vec_emit.first_activated_sn
                 ? std::to_string(vec_emit.first_activated_sn)
                 : std::string()},
            {"last_exposure_sn", std::to_string(vec_emit.last_exposure_sn)},
            {"first_activated_at_install",
             vec_emit.first_activated_sn ? "0"
                 : (vec_emit.activated_total ? "1" : "0")},
            {"affected_sn", std::to_string(vec_emit.last_exposure_sn)},
            {"phys_reads", std::to_string(vec_emit.reads_total)},
            {"phys_reads_delta", "0"},
            {"read_exposures_total",
             std::to_string(vec_emit.read_exposures_total)},
            {"write_exposures_total",
             std::to_string(vec_emit.write_exposures_total)},
            {"first_impact_sn", std::to_string(vec_emit.first_impact_sn)},
            {"first_impact_tick", std::to_string(vec_emit.first_impact_tick)},
            {"first_impact_latency",
             std::to_string(vec_emit.first_impact_latency)},
            {"l5_witness_event",
             std::to_string(vec_emit.l5_witness_event)},
            {"commit_events", std::to_string(vec_emit.commit_events)},
            {"squash_events", std::to_string(vec_emit.squash_events)},
            {"consumers_recorded",
             std::to_string(vec_emit.consumers_recorded)},
            {"sample_policy", "first_of_generation+first_activated+cap"},
            {"terminal", terminal},
            {"outcome", terminal},
            {"contained", "0"},
            {"detection_layer", ""},
        };
        emitFsuProp("chain_end", vec_emit.fault_id, 0, kv);
        vec_emit.installed = false;
        // The L5 ledger is end-of-run state only; the permanent cell itself
        // is cleared below (the ONLY non-reset clear path).
        l5.reset();
        // End of run: this is the ONLY place (besides an explicit reset) that
        // removes the permanent defect. Squash/free/realloc never do.
        rf.clearPermanentFaults();
    }

    void
    CHAOSPhysReg::maybeReapplyStuck(o3::DynInst *inst)
    {
        if (!cpu || !inst)
            return;
        // [FR01/FR02] Read-only transient evidence: real consumer reads and
        // the real program write that overwrites the flipped cell. This runs
        // even when no permanent (FR03) target is armed.
        observeVecTransient(inst);
        auto &rf = cpu->physRegFile();
        if (!rf.vec_stuck.valid)
            return;
        const auto &t = rf.vec_stuck;
        if (t.phys_index < 0 || t.phys_index >= (int)rf.numVecPhysRegs())
            return;
        PhysRegIdPtr target_reg = rf.vecPhysRegId(t.phys_index);
        const uint32_t target_generation = rf.generationOf(target_reg);
        // Free/realloc is observed at the first execute after the change (or
        // at exit). The generation change is an explicit lifecycle event and
        // restarts the exposure chain; it does not depend on this particular
        // instruction touching the cell.
        observeVecGeneration(target_generation);
        noteVecStuckCarrier(target_generation, target_reg);

        // L2: real source-operand reads of the permanently stuck cell.
        for (int i = 0; i < (int)inst->numSrcRegs(); ++i) {
            PhysRegIdPtr src = inst->renamedSrcIdx(i);
            if (!src || src->classValue() != VecRegClass)
                continue;
            if (!rf.isVecStuckTarget(src))
                continue;
            if (vec_emit.operand_read_events >= kVecOperandReadCap)
                continue;
            ++vec_emit.operand_read_events;
            const uint32_t src_generation = rf.generationOf(src);
            // Snapshot the value the consumer really reads. The permanent
            // cell is forced on every write, so a read normally shows the
            // stuck polarity; recorded consumers are those reads that happen
            // after at least one activated exposure (i.e. the defect has
            // demonstrably changed a correct value). An un-activated read is
            // still emitted as an operand_read observation, but never turns
            // into an errant L5 commit.
            uint64_t read_lane = 0;
            bool read_satisfied = false;
            const size_t bytes = rf.vecRegBytes();
            if (bytes >= 16) {
                std::vector<uint8_t> buf(bytes, 0);
                rf.readVecRegRaw(src, buf.data());
                const int lane_bytes = t.lane_width / 8;
                const int base = t.lane_offset * lane_bytes;
                if (base + lane_bytes <= (int)bytes) {
                    std::memcpy(&read_lane, buf.data() + base, lane_bytes);
                    read_satisfied = chaos_vec_stuck::satisfied(
                        read_lane, t.lane_mask, t.polarity);
                }
            }
            int arch_idx = -1;
            if (inst->staticInst &&
                i < (int)inst->staticInst->numSrcRegs()) {
                const RegId &ar = inst->staticInst->srcRegIdx(i);
                if (ar.classValue() == VecRegClass)
                    arch_idx = (int)ar.index();
            }
            // Parent at the most recent real L1 carrier (same generation),
            // otherwise at the generation root. Never at an old generation's
            // carrier after a generation change.
            const uint64_t l2_parent = vec_emit.last_carrier_event
                ? vec_emit.last_carrier_event
                : vec_emit.generation_root_event;
            std::vector<std::pair<std::string, std::string>> kv = {
                {"dyn_inst_seq", std::to_string(inst->seqNum)},
                {"pc", propHex(inst->pcState().instAddr())},
                {"opcode", inst->staticInst
                               ? inst->staticInst->getName() : ""},
                {"thread_id", std::to_string((int)inst->threadNumber)},
                {"reg_class", "vec"},
                {"phys_reg", std::to_string(src->index())},
                {"reg_generation", std::to_string(src_generation)},
                {"arch_reg", arch_idx >= 0 ? std::to_string(arch_idx) : ""},
                {"producer_seq", ""},   // read observation: producer unknown
                {"consumer_seq", std::to_string(inst->seqNum)},
                {"lane_width", std::to_string(t.lane_width)},
                {"lane_offset", std::to_string(t.lane_offset)},
                {"bit_in_lane", std::to_string(t.bit_in_lane)},
                {"lane_mask", propHex(t.lane_mask)},
                {"fixed_mask", propHex(t.lane_mask)},
                {"stuck_polarity", std::to_string((int)t.polarity)},
                {"field", "permanent_stuck"},
                {"before", propHex(read_lane)},
                {"after", propHex(read_lane)},
                {"value_hash", propHex(read_lane)},
                {"activated", ""},
                {"install_event", std::to_string(vec_emit.install_event)},
                {"read_exposures_total",
                 std::to_string(rf.getVecStuckReads())},
                {"write_exposures_total",
                 std::to_string(vec_emit.write_exposures_total)},
                {"cell_allocated", "1"},
                {"state_before", "written_stuck"},
                {"state_after",
                 read_satisfied ? "operand_read_stuck" : "operand_read_clean"},
            };
            const uint64_t l2_eid = emitFsuProp(
                "operand_read", vec_emit.fault_id, l2_parent, kv);
            // Record the consumer for the real L5 hooks. Only a read that
            // observes the forced bits after a real activated exposure is a
            // tainted consumer of the permanent defect.
            if (l2_eid && read_satisfied && vec_emit.activated_total > 0) {
                l5.record(inst->seqNum, l2_eid, src_generation, read_lane);
                vec_emit.consumers_recorded = l5.consumersRecorded();
            }
        }

        // L1/L4: every write to the target physical cell re-applies the same
        // permanent mask, across generations.
        for (int i = 0; i < (int)inst->numDestRegs(); ++i) {
            PhysRegIdPtr dest = inst->renamedDestIdx(i);
            if (!dest || dest->is(InvalidRegClass))
                continue;
            if (dest->classValue() != VecRegClass)
                continue;
            if (!rf.isVecStuckTarget(dest))
                continue;
            const uint32_t gen = rf.generationOf(dest);
            observeVecGeneration(gen);

            // Snapshot the CORRECT value the instruction wrote, then force
            // the stuck bits. A write whose target bits already equal the
            // stuck polarity is an exposure but NOT an activation.
            const size_t bytes = rf.vecRegBytes();
            if (bytes < 16)
                continue;
            std::vector<uint8_t> before(bytes, 0);
            rf.readVecRegRaw(dest, before.data());
            const int lane_bytes = t.lane_width / 8;
            const int base = t.lane_offset * lane_bytes;
            uint64_t lane_before = 0;
            std::memcpy(&lane_before, before.data() + base, lane_bytes);
            const bool activated = !chaos_vec_stuck::satisfied(
                lane_before, t.lane_mask, t.polarity);
            if (!rf.reapplyVecStuck(dest))
                continue;
            // reapplyVecStuck wrote the PRF; re-read for the event's after.
            uint64_t lane_after = 0;
            std::vector<uint8_t> after(bytes, 0);
            rf.readVecRegRaw(dest, after.data());
            std::memcpy(&lane_after, after.data() + base, lane_bytes);

            ++vec_stuck_writes;
            if (activated)
                ++vec_stuck_activated;
            ++vec_emit.exposure_id;
            ++vec_emit.exposures_total;
            // Write exposures are counted separately from reads: install
            // write + this re-apply. `read_exposures_total` is the exact
            // container-side read count at this instant.
            vec_emit.write_exposures_total = vec_emit.exposures_total;
            if (activated)
                ++vec_emit.activated_total;
            vec_emit.last_exposure_sn = inst->seqNum;
            bool first_activated = false;
            if (activated && !vec_emit.first_activated_emitted) {
                vec_emit.first_activated_emitted = true;
                vec_emit.first_activated_sn = inst->seqNum;
                vec_emit.first_activated_tick = curTick();
                first_activated = true;
            }
            const bool first_of_generation =
                vec_emit.exposure_id == 1;
            const bool activated_sample =
                activated && vec_emit.activated_events < kVecActivatedEventCap;
            // Bound every stream: ordinary exposures by kVecExposureEventCap,
            // first-of-generation markers by kVecGenerationEventCap, plus the
            // always-kept first activated exposure. Counts stay exact.
            const bool sample =
                first_activated || activated_sample ||
                vec_emit.exposures_sampled < kVecExposureEventCap ||
                (first_of_generation &&
                 vec_emit.generation_changes_sampled < kVecGenerationEventCap);
            if (activated_sample)
                ++vec_emit.activated_events;

            if (write_log && log_stream && log_stream->stream() &&
                vec_stuck_writes <= 64) {
                std::ostringstream os;
                os << "VecStuckApply: cycle=" << cpu->curCycle()
                   << " phys=" << t.phys_index
                   << " gen=" << gen
                   << " exposure=" << vec_emit.exposure_id
                   << " lane=" << t.lane_offset
                   << " mask=0x" << std::hex << t.lane_mask << std::dec
                   << " polarity=" << (int)t.polarity
                   << " before=0x" << std::hex << lane_before
                   << " after=0x" << lane_after << std::dec
                   << " activated=" << (activated ? 1 : 0) << std::endl;
                *(log_stream->stream()) << os.str();
            }

            if (!(sample || activated_sample)) {
                ++vec_emit.exposures_dropped;
                continue;
            }
            ++vec_emit.exposures_sampled;
            vec_emit.exposures_dropped =
                vec_emit.exposures_total - vec_emit.exposures_sampled;

            int arch_idx = -1;
            if (inst->staticInst &&
                i < (int)inst->staticInst->numDestRegs()) {
                const RegId &ar = inst->staticInst->destRegIdx(i);
                if (ar.classValue() == VecRegClass)
                    arch_idx = (int)ar.index();
            }
            std::vector<std::pair<std::string, std::string>> kv = {
                {"dyn_inst_seq", std::to_string(inst->seqNum)},
                {"pc", propHex(inst->pcState().instAddr())},
                {"opcode", inst->staticInst
                               ? inst->staticInst->getName() : ""},
                {"thread_id", std::to_string((int)inst->threadNumber)},
                {"reg_class", "vec"},
                {"phys_reg", std::to_string(dest->index())},
                {"reg_generation", std::to_string(gen)},
                {"arch_reg", arch_idx >= 0 ? std::to_string(arch_idx) : ""},
                {"producer_seq", std::to_string(inst->seqNum)},
                {"consumer_seq", ""},   // write observation: consumer unknown
                {"lane_width", std::to_string(t.lane_width)},
                {"lane_offset", std::to_string(t.lane_offset)},
                {"bit_in_lane", std::to_string(t.bit_in_lane)},
                {"lane_mask", propHex(t.lane_mask)},
                {"fixed_mask", propHex(t.lane_mask)},
                {"stuck_polarity", std::to_string((int)t.polarity)},
                {"field", "permanent_stuck"},
                {"before", propHex(lane_before)},
                {"after", propHex(lane_after)},
                {"correct_before", propHex(lane_before)},
                {"stuck_after", propHex(lane_after)},
                {"activated", activated ? "1" : "0"},
                {"install_event", std::to_string(vec_emit.install_event)},
                {"exposure_id", std::to_string(vec_emit.exposure_id)},
                {"exposure_count", std::to_string(vec_emit.exposures_total)},
                {"activated_exposure_count",
                 std::to_string(vec_emit.activated_total)},
                {"first_activated_sn",
                 std::to_string(vec_emit.first_activated_sn)},
                {"last_exposure_sn",
                 std::to_string(vec_emit.last_exposure_sn)},
                {"affected_sn", std::to_string(inst->seqNum)},
                {"exposures_total",
                 std::to_string(vec_emit.exposures_total)},
                {"exposures_sampled",
                 std::to_string(vec_emit.exposures_sampled)},
                {"exposures_dropped",
                 std::to_string(vec_emit.exposures_dropped)},
                {"write_exposures_total",
                 std::to_string(vec_emit.write_exposures_total)},
                {"read_exposures_total",
                 std::to_string(rf.getVecStuckReads())},
                {"generation_changes",
                 std::to_string(vec_emit.generation_changes)},
                {"cell_allocated", "1"},
                {"cell_free", "0"},
                {"stuck_reapplied", "1"},
                {"sample_policy", "first_of_generation+first_activated+cap"},
                {"state_before", "correct_write"},
                {"state_after", "stuck_write"},
            };
            const uint64_t parent = first_of_generation
                ? vec_emit.generation_root_event : 0;
            const uint64_t write_eid =
                emitFsuProp("phys_write", vec_emit.fault_id, parent, kv);
            uint64_t last = write_eid;
            if (first_of_generation || first_activated) {
                const uint64_t reapplied = emitFsuProp(
                    "stuck_reapplied", vec_emit.fault_id, last, kv);
                if (reapplied)
                    last = reapplied;
            }
            const uint64_t ex = emitFsuProp(
                "execute", vec_emit.fault_id, last, kv);
            if (ex)
                last = ex;
            emitFsuProp("prf_writeback", vec_emit.fault_id, last, kv);
        }
    }

    // [FR03] L5 real commit. Reached only from Commit::commitHead() AFTER the
    // instruction really committed. Only a seqNum previously recorded as a
    // consumer of the permanently stuck cell (a real operand_read after an
    // activated exposure) can produce an L5 witness. The event is parented at
    // that consumer's L2 operand_read, so the direct chain is L1→L2→L5.
    void
    CHAOSPhysReg::noteCommit(ThreadID tid, o3::DynInst *inst)
    {
        if (!cpu || !inst)
            return;
        // [FR01/FR02] A real L5 commit of a recorded transient consumer.
        noteVecTransientCommit(tid, inst);
        if (!vec_emit.installed)
            return;
        const auto r = l5.noteCommit(inst->seqNum);
        if (!r.matched)
            return;
        auto &rf = cpu->physRegFile();
        const auto &t = rf.vec_stuck;
        const bool first_impact = vec_emit.first_impact_sn == 0;
        if (first_impact) {
            // First real architectural impact. Latency is measured from the
            // first activated exposure when one exists, otherwise from the
            // installation (documented explicitly; never fabricated).
            vec_emit.first_impact_sn = inst->seqNum;
            vec_emit.first_impact_tick = curTick();
            const uint64_t basis = vec_emit.first_activated_tick
                ? vec_emit.first_activated_tick : vec_emit.install_tick;
            vec_emit.first_impact_latency =
                (basis != 0 && curTick() >= basis)
                    ? (uint64_t)(curTick() - basis) : 0;
        }
        vec_emit.commit_events = l5.commitEvents();
        vec_emit.consumers_recorded = l5.consumersRecorded();
        std::vector<std::pair<std::string, std::string>> kv = {
            {"consumer_seq", std::to_string(inst->seqNum)},
            {"dyn_inst_seq", std::to_string(inst->seqNum)},
            // commit_seq is this fault chain's real L5 commit ordinal. It is
            // deliberately distinct from dyn_inst_seq (ROB sequence number).
            {"commit_seq", std::to_string(r.ordinal)},
            {"thread_id", std::to_string((int)tid)},
            {"pc", propHex(inst->pcState().instAddr())},
            {"opcode",
             inst->staticInst ? inst->staticInst->getName() : ""},
            {"reg_class", "vec"},
            {"phys_reg", std::to_string(t.phys_index)},
            // Generation captured when the consumer read the cell, NOT the
            // cell's current generation. An old consumer can never be
            // re-labelled as a new-generation event.
            {"reg_generation", std::to_string(r.generation)},
            {"install_event", std::to_string(vec_emit.install_event)},
            {"lane_width", std::to_string(t.lane_width)},
            {"lane_offset", std::to_string(t.lane_offset)},
            {"bit_in_lane", std::to_string(t.bit_in_lane)},
            {"lane_mask", propHex(t.lane_mask)},
            {"fixed_mask", propHex(t.lane_mask)},
            {"stuck_polarity", std::to_string((int)t.polarity)},
            {"field", "permanent_stuck"},
            {"before", propHex(r.value)},
            {"after", propHex(r.value)},
            {"value_hash", propHex(r.value)},
            {"activated", "1"},
            {"exposures_total",
             std::to_string(vec_emit.exposures_total)},
            {"exposures_sampled",
             std::to_string(vec_emit.exposures_sampled)},
            {"exposures_dropped",
             std::to_string(vec_emit.exposures_dropped)},
            {"write_exposures_total",
             std::to_string(vec_emit.write_exposures_total)},
            {"read_exposures_total",
             std::to_string(rf.getVecStuckReads())},
            {"activated_exposure_count",
             std::to_string(vec_emit.activated_total)},
            {"first_activated_sn",
             vec_emit.first_activated_sn
                 ? std::to_string(vec_emit.first_activated_sn)
                 : std::string()},
            {"last_exposure_sn",
             std::to_string(vec_emit.last_exposure_sn)},
            {"affected_sn", std::to_string(vec_emit.first_impact_sn)},
            {"first_impact_sn", std::to_string(vec_emit.first_impact_sn)},
            {"first_impact_tick", std::to_string(vec_emit.first_impact_tick)},
            {"first_impact_latency",
             std::to_string(vec_emit.first_impact_latency)},
            {"squash_events", std::to_string(l5.squashEvents())},
            {"sample_policy",
             "first_of_generation+first_activated+cap"},
            {"detection_layer", "L5"},
            {"outcome", "errant_commit"},
            {"contained", "0"},
            {"state_before", "read_stuck"},
            {"state_after", "committed"},
        };
        const uint64_t eid = emitFsuProp(
            "commit", vec_emit.fault_id, r.l2_event, kv);
        if (eid && vec_emit.l5_witness_event == 0)
            vec_emit.l5_witness_event = eid;
    }

    // [FR03] L5 squash observation. Read-only: it never clears the permanent
    // defect, never consumes a fault, and NEVER emits a commit. A squash of a
    // recorded consumer produces kind=squash with squashed=1; detection_layer
    // is left empty because no architectural detection happened at squash.
    void
    CHAOSPhysReg::noteSquash(ThreadID tid, o3::DynInst *inst)
    {
        if (!cpu || !inst)
            return;
        // [FR01/FR02] A squash is never a commit and never clears the fault.
        noteVecTransientSquash(tid, inst);
        if (!vec_emit.installed)
            return;
        const auto r = l5.noteSquash(inst->seqNum);
        if (!r.matched)
            return;
        auto &rf = cpu->physRegFile();
        const auto &t = rf.vec_stuck;
        vec_emit.squash_events = l5.squashEvents();
        vec_emit.commit_events = l5.commitEvents();
        vec_emit.consumers_recorded = l5.consumersRecorded();
        std::vector<std::pair<std::string, std::string>> kv = {
            {"consumer_seq", std::to_string(inst->seqNum)},
            {"dyn_inst_seq", std::to_string(inst->seqNum)},
            {"thread_id", std::to_string((int)tid)},
            {"pc", propHex(inst->pcState().instAddr())},
            {"opcode",
             inst->staticInst ? inst->staticInst->getName() : ""},
            {"reg_class", "vec"},
            {"phys_reg", std::to_string(t.phys_index)},
            {"reg_generation", std::to_string(r.generation)},
            {"install_event", std::to_string(vec_emit.install_event)},
            {"lane_width", std::to_string(t.lane_width)},
            {"lane_offset", std::to_string(t.lane_offset)},
            {"bit_in_lane", std::to_string(t.bit_in_lane)},
            {"lane_mask", propHex(t.lane_mask)},
            {"fixed_mask", propHex(t.lane_mask)},
            {"stuck_polarity", std::to_string((int)t.polarity)},
            {"field", "permanent_stuck"},
            {"before", propHex(r.value)},
            {"after", propHex(r.value)},
            {"value_hash", propHex(r.value)},
            {"squashed", "1"},
            {"squash_events", std::to_string(l5.squashEvents())},
            {"commit_events", std::to_string(l5.commitEvents())},
            {"write_exposures_total",
             std::to_string(vec_emit.write_exposures_total)},
            {"read_exposures_total",
             std::to_string(rf.getVecStuckReads())},
            // Not detected at L5; no detection layer claimed.
            {"detection_layer", ""},
            {"outcome", "squashed"},
            {"contained", "0"},
            {"state_before", "read_stuck"},
            {"state_after", "squashed"},
        };
        emitFsuProp("squash", vec_emit.fault_id, r.l2_event, kv);
    }

    CHAOSPhysReg::FaultType
    CHAOSPhysReg::stringToFaultType(const std::string &s) {
        if (s == "bit_flip") return FaultType::BitFlip;
        else if (s == "stuck_at_zero") return FaultType::StuckAtZero;
        else if (s == "stuck_at_one") return FaultType::StuckAtOne;
        return FaultType::Random;
    }

    const char*
    CHAOSPhysReg::faultTypeToString(CHAOSPhysReg::FaultType f) {
        switch (f) {
            case FaultType::BitFlip: return "bit_flip";
            case FaultType::StuckAtZero: return "stuck_at_zero";
            case FaultType::StuckAtOne: return "stuck_at_one";
            case FaultType::Random: return "random";  // G7: handle enum (clear -Wswitch)
        }
        return "random";
    }

    CHAOSPhysReg::Mode
    CHAOSPhysReg::stringToMode(const std::string &s) {
        if (s == "arch_commit") return Mode::ArchCommit;
        else if (s == "arch_frontend") return Mode::ArchFrontend;
        return Mode::Phys;
    }

    CHAOSPhysReg::RegClassSel
    CHAOSPhysReg::stringToRegClassSel(const std::string &s) {
        if (s == "floating_point") return RegClassSel::FloatingPoint;
        else if (s == "vector") return RegClassSel::Vector;
        else if (s == "both") return RegClassSel::Both;
        return RegClassSel::Integer;
    }

    void
    CHAOSPhysReg::scheduleAttackEvent(Cycles delay)
    {
        if (!attackEvent.scheduled())
            schedule(attackEvent, cpu->clockEdge(delay));
    }

    void
    CHAOSPhysReg::unscheduleAttackEvent()
    {
        if (attackEvent.scheduled()) attackEvent.squash();
        if (periodicCheck.scheduled()) periodicCheck.squash();
        // NOTE: readTraceEvent is intentionally NOT squashed here — it must
        // keep counting reads of the injected phys slot until the workload
        // ends (all threads halt). It is squashed only from readTraceCheck
        // when the workload has halted.
    }

    void
    CHAOSPhysReg::scheduleCheckPermanentFault(Cycles delay)
    {
        if (!periodicCheck.scheduled())
            schedule(periodicCheck, cpu->clockEdge(delay));
    }

    uint64_t
    CHAOSPhysReg::generateRandomMask(std::mt19937 &gen, int bits_to_change, int len)
    {
        uint64_t mask = 0;
        std::uniform_int_distribution<int> bitDist(0, len - 1);
        while (bits_to_change-- > 0) mask |= (1ULL << bitDist(gen));
        return mask;
    }

    // Core: resolve a target PHYSICAL register id according to the fi_mode,
    // then read-modify-write it directly in the physical register file.
    // This is the key difference from CHAOSReg (which wrote the commitRenameMap
    // phys reg via ThreadContext::setReg — a backdoor that doesn't propagate
    // to in-flight instructions on O3).
    void
    CHAOSPhysReg::processFault(ThreadID tid)
    {
        if (vec_transient_fatal)
            return;
        // 1. Resolve target register class (integer / floating_point / vector).
        // 'both' picks one at random per injection across the three classes (a
        // real cell doesn't know its class either; this mirrors the ITC'23/GeFIN
        // phys abstraction). Reserved/special classes (VecElem/VecPred/Mat/
        // CC/Misc) are never legal permanent-cell targets.
        gem5::RegClassType target_class = gem5::IntRegClass;
        if (reg_target_class == RegClassSel::FloatingPoint) {
            target_class = gem5::FloatRegClass;
        } else if (reg_target_class == RegClassSel::Vector) {
            target_class = gem5::VecRegClass;
        } else if (reg_target_class == RegClassSel::Both) {
            switch (std::uniform_int_distribution<>(0, 2)(rng)) {
              case 0: target_class = gem5::IntRegClass; break;
              case 1: target_class = gem5::FloatRegClass; break;
              default: target_class = gem5::VecRegClass; break;
            }
        }
        if (!isFreeListClass(target_class))
            return;

        // 2. Resolve target physical register id.
        PhysRegIdPtr phys_reg = nullptr;
        int chosen_phys_idx = -1;     // for logging
        int chosen_arch_idx = -1;     // for logging (arch modes)

        if (fi_mode == Mode::Phys) {
            // Inject by physical register index. A real defective cell has no
            // notion of architectural registers; whoever is allocated to this
            // slot gets hit. This is the ITC'23/GeFIN abstraction.
            int n;
            if (target_class == gem5::FloatRegClass)
                n = (int)cpu->physRegFile().numFloatPhysRegs();
            else if (target_class == gem5::VecRegClass)
                n = (int)cpu->physRegFile().numVecPhysRegs();
            else
                n = (int)cpu->physRegFile().numIntPhysRegs();
            if (n <= 0) return;
            // phys random: ACTIVE-ONLY sampling (Phase 5.6 fix). The naive
            // uniform pick over ALL slots wastes the single fault on a free
            // slot when the O3 window is sparsely filled (steady-state FS:
            // FreeListSize 170/200 — the first method2 PRF-arm runs injected
            // an Inactive slot = effective no-op). Re-sample up to K times
            // for an allocated (non-free) slot; if all K miss (window
            // truly empty), reschedule instead of burning the fault.
            if (forced_target_valid) {
                // [FR01/FR02] The consumer's execute boundary chose this
                // exact source cell; install here so the very next
                // staticInst->execute() reads the flipped value.
                chosen_phys_idx = forced_target_phys_idx;
            } else if (target_phys_idx >= 0) {
                chosen_phys_idx = target_phys_idx;
            } else if (require_ready_consumer) {
                // [FR01/FR02] Workbook trigger: "target Vec phys reg active,
                // ready AND a later consumer read". Enumerate the exact
                // candidate set (ready pending source, allocated cell) and
                // choose uniformly from it. No candidate -> defer without
                // consuming the fault. The old K-random-samples + fallback
                // could land on a dead cell (formal seed1 target 34, gen 1,
                // value 0: never read), which is not an eligible event.
                // The eligible event is the (instruction, source operand)
                // pair, not merely the cell: one cell can be consumed by
                // FP32 and FP64 instructions, so submodel precision must be
                // decided from the real AArch64 encoding of the consumer.
                std::vector<o3::InstructionQueue::ReadySource> pending;
                cpu->o3IEW().instQueue.collectReadyPendingSources(
                    target_class, pending);
                std::vector<o3::InstructionQueue::ReadySource> eligible;
                for (const auto &s : pending) {
                    PhysRegIdPtr cand_reg =
                        (target_class == gem5::FloatRegClass)
                            ? cpu->physRegFile().floatPhysRegId(s.phys_index)
                            : (target_class == gem5::VecRegClass)
                                  ? cpu->physRegFile().vecPhysRegId(
                                        s.phys_index)
                                  : cpu->physRegFile().intPhysRegId(
                                        s.phys_index);
                    if (cpu->physFreeList().isFree(target_class, cand_reg))
                        continue;
                    if (target_precision != 0 &&
                        decodedConsumerPrecision(s.inst.get()) !=
                            target_precision) {
                        continue;  // submodel precision mismatch
                    }
                    eligible.push_back(s);
                }
                last_selection_candidates = eligible.size();
                if (eligible.empty()) {
                    ++skip_no_ready_consumer_count;
                    wait_for_allocation = true;  // >=100-cycle retry pacing
                    // The O3 IQ issues ready FP ops immediately, so a ready
                    // *unissued* source is rare. Arm the execute-boundary
                    // hook: the first precision-qualified consumer will get
                    // the fault installed into its source cell just before
                    // its own read.
                    armed_consumer_injection = true;
                    if (write_log && log_stream && log_stream->stream()
                        && (skip_no_ready_consumer_count <= 8
                            || skip_no_ready_consumer_count % 10000 == 0)) {
                        int n64 = 0, n32 = 0, n0 = 0;
                        for (const auto &s : pending) {
                            const int p = decodedConsumerPrecision(
                                s.inst.get());
                            if (p == 64) ++n64;
                            else if (p == 32) ++n32;
                            else ++n0;
                        }
                        *(log_stream->stream())
                            << "VecTargetNoReadyConsumer: cycle="
                            << cpu->curCycle()
                            << " class="
                            << (target_class == gem5::VecRegClass ? "vec"
                                : target_class == gem5::FloatRegClass
                                      ? "float" : "int")
                            << " skips=" << skip_no_ready_consumer_count
                            << " pending=" << pending.size()
                            << " p64=" << n64 << " p32=" << n32
                            << " p_other=" << n0
                            << " want=" << target_precision
                            << " (no eligible ready pending source in IQ; "
                               "retry, fault not consumed)" << std::endl;
                    }
                    return;
                }
                const auto &pick = eligible[
                    std::uniform_int_distribution<size_t>(
                        0, eligible.size() - 1)(rng)];
                chosen_phys_idx = pick.phys_index;
                last_selected_consumer_sn = pick.inst->seqNum;
                last_selected_precision =
                    decodedConsumerPrecision(pick.inst.get());
            } else {
                const int K_ACTIVE_RETRY = 32;
                chosen_phys_idx = -1;
                int fallback_allocated = -1;
                for (int t = 0; t < K_ACTIVE_RETRY; t++) {
                    int cand = std::uniform_int_distribution<>(0, n - 1)(rng);
                    PhysRegIdPtr cand_reg =
                        (target_class == gem5::FloatRegClass)
                            ? cpu->physRegFile().floatPhysRegId(cand)
                            : (target_class == gem5::VecRegClass)
                                  ? cpu->physRegFile().vecPhysRegId(cand)
                                  : cpu->physRegFile().intPhysRegId(cand);
                    if (cpu->physFreeList().isFree(target_class, cand_reg))
                        continue;
                    if (fallback_allocated < 0)
                        fallback_allocated = cand;
                    // Prefer a cell that an unissued instruction will really
                    // read: the workbook trigger requires a later consumer
                    // read, not merely an allocated slot.
                    if (cpu->o3IEW().instQueue.physRegHasPendingSource(
                            target_class, cand)) {
                        chosen_phys_idx = cand;
                        break;
                    }
                }
                if (chosen_phys_idx < 0)
                    chosen_phys_idx = fallback_allocated;
                if (chosen_phys_idx < 0) {
                    // window empty (all K samples free): honest skip —
                    // reschedule, do NOT consume the fault
                    return;  // caller's periodic event reschedules
                }
            }
            if (chosen_phys_idx >= n) return;
            if (target_class == gem5::FloatRegClass)
                phys_reg = cpu->physRegFile().floatPhysRegId(chosen_phys_idx);
            else if (target_class == gem5::VecRegClass)
                phys_reg = cpu->physRegFile().vecPhysRegId(chosen_phys_idx);
            else
                phys_reg = cpu->physRegFile().intPhysRegId(chosen_phys_idx);

            // Liveness probe: is this physical slot currently FREE (inactive)
            // or ALLOCATED (active)? Correct criterion per project notes: a phys
            // reg NOT in the free list is allocated — it may be held as a source
            // by in-flight renamed-but-unexecuted instructions even if no rename
            // map entry currently maps it (older version superseded but not yet
            // released). So "not free" = active = may be read. (The earlier
            // "rename map reverse-walk" criterion was too narrow and mislabeled
            // some live slots as dead, producing the dead-slot SDC anomaly.)
            bool is_free = cpu->physFreeList().isFree(target_class, phys_reg);
            free_list_size_at_inject = cpu->physFreeList().numFreeRegs(
                target_class);
            // [FR03] Real-target policy: with requireAllocated, never burn the
            // fault on a slot that is currently free. The attack event
            // reschedules and retries (maxFaults is not consumed here), so a
            // fixed targetPhysRegIdx eventually lands while an in-flight
            // instruction really holds the cell. Default false keeps the
            // historical behaviour byte-identical.
            if (require_allocated && is_free) {
                wait_for_allocation = true;
                ++skip_free_count;
                // Bounded diagnostics: never one line per retry.
                if (write_log && log_stream && log_stream->stream()
                    && (skip_free_count <= 8
                        || skip_free_count % 100000 == 0)) {
                    *(log_stream->stream())
                        << "VecStuckSkipFree: cycle=" << cpu->curCycle()
                        << " class=" << (target_class == gem5::VecRegClass
                                          ? "vec"
                                          : target_class == gem5::FloatRegClass
                                            ? "float" : "int")
                        << " phys=" << chosen_phys_idx
                        << " skips=" << skip_free_count
                        << " (requireAllocated: retry in >=100 cycles, "
                           "fault not consumed)"
                        << std::endl;
                }
                return;
            }
            if (!is_free) {
                // active — also record which arch reg (if any) maps to it now,
                // for diagnostics (walk rename map; best-effort, not the
                // liveness source of truth).
                gem5::ThreadContext *tc = cpu->getContext(tid);
                if (tc) {
                    gem5::BaseISA *isa = tc->getIsaPtr();
                    if (isa) {
                        const auto &rc = isa->regClasses();
                        const gem5::RegClass *ic = rc[target_class];
                        int na = ic ? ic->numRegs() : 0;
                        // X0-X30 (cap 31) for int; V0-V31 (cap 32) for
                        // float AND vector (AArch64 V/D/Q share the file).
                        int cap;
                        if (target_class == gem5::IntRegClass)
                            cap = (na < 31 ? na : 31);
                        else
                            cap = (na < 32 ? na : 32);
                        for (int a = 0; a < cap; a++) {
                            gem5::RegId ar(*ic, a);
                            const gem5::RegId flat = ar.flatten(*isa);
                            PhysRegIdPtr pm =
                                cpu->frontRenameMap()[tid].lookup(flat);
                            if (pm && pm->index() == chosen_phys_idx) {
                                chosen_arch_idx = a;
                                break;
                            }
                        }
                    }
                }
            } else {
                chosen_arch_idx = -2;  // sentinel: free/inactive
            }
        } else {
            // arch_frontend: renameMap.lookup      (in-flight mapping)
            // arch_commit:   commitRenameMap.lookup (committed mapping = CHAOSReg)
            gem5::ThreadContext *thread_context = cpu->getContext(tid);
            if (!thread_context) return;
            gem5::BaseISA *isa = thread_context->getIsaPtr();
            if (!isa) return;
            const auto &reg_classes = isa->regClasses();
            const gem5::RegClass *reg_class = reg_classes[target_class];
            if (!reg_class || reg_class->numRegs() == 0) return;
            int arch_idx = target_arch_idx;
            if (arch_idx < 0 || arch_idx >= reg_class->numRegs()) return;
            chosen_arch_idx = arch_idx;
            gem5::RegId arch_reg(*reg_class, arch_idx);
            // flatten to match the per-class rename map's indexing
            const gem5::RegId flat = arch_reg.flatten(*isa);
            if (fi_mode == Mode::ArchFrontend)
                phys_reg = cpu->frontRenameMap()[tid].lookup(flat);
            else // ArchCommit
                phys_reg = cpu->commitRenameMapAccess()[tid].lookup(flat);
            if (!phys_reg) return;
            chosen_phys_idx = phys_reg->index();
        }

        if (!phys_reg) return;

        // 3. Read current physical reg value, apply fault, write back.
        // VecRegClass holds a whole vector in a buffer (not a scalar RegVal),
        // so it goes through the getReg/setReg void*-overload; the fault mask
        // is applied to the first 8 bytes (one 64-bit word — enough to corrupt
        // the low lane of a NEON/SVE vector and propagate as SDC). int/float/
        // vecelem stay on the scalar RegVal path.
        FaultType chosen = fault_type_enum;
        if (fault_type_enum == FaultType::Random) {
            int idx = random_fault_distribution(rng);
            chosen = static_cast<FaultType>(idx);
        }

        uint64_t mask = fault_mask.any()
            ? fault_mask.to_ullong()
            : generateRandomMask(rng, num_bits_to_change, 64);

        if (target_class == gem5::VecRegClass) {
            // Buffer path: read the WHOLE vector, corrupt ONE lane, write back.
            // The buffer MUST be sized to the actual vector phys reg byte width
            // (AArch64 VecRegClass = up to 256B for SVE-2048b). The old fixed
            // `uint8_t buf[64]` overflowed by 192B on getReg (report issue #3).
            // Phase 2 item 1: NEON lane stratification — the fault is applied
            // to ONE lane of vec_lane_width bits at lane vec_lane_offset,
            // instead of always the low 64-bit word. So a per-lane SDC study
            // (plan §7.4 BM-NEON: 4x32/2x64/8x16 lanes) is possible.
            size_t vbytes = cpu->physRegFile().vecRegBytes();
            if (vbytes < sizeof(uint64_t)) vbytes = sizeof(uint64_t);  // paranoia
            std::vector<uint8_t> buf(vbytes, 0);
            cpu->physRegFile().getReg(phys_reg, buf.data());
            // Resolve the lane: width in bits -> bytes; clamp to vector width.
            // The legacy stuck paths keep the historical "invalid -> 32"
            // fallback; the FR01/FR02 transient path fails closed instead.
            const bool lane_width_valid = vec_lane_width == 8 ||
                vec_lane_width == 16 || vec_lane_width == 32 ||
                vec_lane_width == 64;
            int lw = lane_width_valid ? vec_lane_width : 32;
            int lane_bytes = lw / 8;
            int max_lanes = (int)(vbytes / lane_bytes);
            if (max_lanes < 1) max_lanes = 1;
            int lane = vec_lane_offset;
            if (lane < 0 || lane >= max_lanes)
                lane = std::uniform_int_distribution<>(0, max_lanes - 1)(rng);
            // The fault mask applies within the lane's bit window. Treat the
            // lane as a lane_bytes-wide little-endian integer; apply the
            // 64-bit mask truncated/padded to lane_bytes, then read-modify-write
            // only those bytes. (mask was generated for the scalar path as a
            // 64-bit value; for a 32-bit lane we use the low 32 bits, etc.)
            uint8_t *lane_ptr = buf.data() + (size_t)lane * lane_bytes;
            uint64_t lane_val = 0;
            for (int b = 0; b < lane_bytes; ++b)
                lane_val |= ((uint64_t)lane_ptr[b]) << (8 * b);
            uint64_t lane_mask = (lw < 64) ? (mask & ((1ULL << lw) - 1)) : mask;
            const uint64_t correct_lane = lane_val;
            const uint32_t install_generation =
                cpu->physRegFile().generationOf(phys_reg);
            bool vec_stuck_armed = false;
            if (chosen == FaultType::BitFlip) {
                // [FR01/FR02] TRANSIENT one-shot flip. The fault domain is the
                // architectural 128-bit Vec value, and every bit is selected
                // (or validated) as a distinct identity. Nothing is armed on
                // the write path: the next real write genuinely removes the
                // defect. A request that cannot be honoured fails CLOSED.
                using namespace chaos_vec_transient;
                if (!lane_width_valid) {
                    vec_transient_fatal = true;
                    if (write_log && log_stream && log_stream->stream()) {
                        *(log_stream->stream())
                            << "VecFaultFailClosed: cycle=" << cpu->curCycle()
                            << " phys=" << chosen_phys_idx
                            << " lane_width=" << vec_lane_width
                            << " reason=invalid_lane_width"
                            << " (no injection; fault not consumed)"
                            << std::endl;
                    }
                    return;
                }
                Geometry geom = (vec_lane_offset >= 0) ? Geometry::SameLane
                                                       : Geometry::Any;
                Geometry hinted;
                if (parseGeometry(semantic_role, num_bits_to_change,
                                  hinted))
                    geom = hinted;
                Selection sel;
                if (fault_mask.any()) {
                    // The explicit mask is authoritative; its popcount and
                    // geometry must match the requested bit count exactly.
                    sel = selectionFromMask(lw, vec_lane_offset,
                                            num_bits_to_change, geom,
                                            mask, 0);
                } else {
                    sel = select(rng, lw, vec_lane_offset,
                                 num_bits_to_change, geom, semantic_role);
                }
                if (!sel.ok) {
                    vec_transient_fatal = true;
                    if (write_log && log_stream && log_stream->stream()) {
                        *(log_stream->stream())
                            << "VecFaultFailClosed: cycle=" << cpu->curCycle()
                            << " model=" << (num_bits_to_change == 1
                                             ? "FR01" : "FR02")
                            << " phys=" << chosen_phys_idx
                            << " lane_width=" << lw
                            << " lane_offset=" << vec_lane_offset
                            << " bits=" << num_bits_to_change
                            << " explicit_mask=0x" << std::hex << mask
                            << std::dec
                            << " reason=" << sel.reason
                            << " (no injection; fault not consumed)"
                            << std::endl;
                    }
                    return;
                }
                if (vbytes < (size_t)kVecBytes) {
                    vec_transient_fatal = true;
                    return;
                }
                uint8_t before16[kVecBytes];
                uint8_t after16[kVecBytes];
                std::memcpy(before16, buf.data(), kVecBytes);
                if (!applyToVec(buf.data(), buf.size(), sel)) {
                    vec_transient_fatal = true;
                    return;
                }
                std::memcpy(after16, buf.data(), kVecBytes);
                cpu->physRegFile().setReg(phys_reg, buf.data());
                stats->numBitFlips++;
                noteVecTransientInstalled(
                    tid, chosen_phys_idx, chosen_arch_idx,
                    install_generation, sel, before16, after16);
                if (write_log && log_stream && log_stream->stream()) {
                    *(log_stream->stream())
                        << "  [vec transient lane=" << sel.lane_offset
                        << " width=" << sel.lane_width << "bits bits="
                        << bitIndices(sel) << " mask=0x" << std::hex
                        << sel.mask_lo << std::dec
                        << " (no permanent arm)]" << std::endl;
                }
            } else {
                switch (chosen) {
                  case FaultType::StuckAtZero:
                    lane_val &= ~lane_mask;
                    stats->numStuckAtZero++;
                    stats->numPermanentFaults++;
                    permanent_faults[{tid, chosen_phys_idx}] =
                        {chosen, mask, true, target_class};
                    // [FR03] Arm the PERMANENT physical-cell write-path mask.
                    // The post-execute hook re-forces it after every later
                    // write to this physical cell. The generation is recorded
                    // as allocation/exposure identity only; free/realloc does
                    // NOT clear the defect (workbook table 3 FR03).
                    cpu->physRegFile().armVecStuck(
                        chosen_phys_idx, install_generation,
                        lw, lane, lane_mask, 0);
                    vec_stuck_armed = true;
                    break;
                  case FaultType::StuckAtOne:
                    lane_val |= lane_mask;
                    stats->numStuckAtOne++;
                    stats->numPermanentFaults++;
                    permanent_faults[{tid, chosen_phys_idx}] =
                        {chosen, mask, true, target_class};
                    cpu->physRegFile().armVecStuck(
                        chosen_phys_idx, install_generation,
                        lw, lane, lane_mask, 1);
                    vec_stuck_armed = true;
                    break;
                  case FaultType::BitFlip:
                    // Unreachable (handled above); kept so the fault-type
                    // vocabulary stays explicit in this switch.
                    lane_val ^= lane_mask;
                    stats->numBitFlips++;
                    break;
                  default: break;
                }
                for (int b = 0; b < lane_bytes; ++b)
                    lane_ptr[b] = (uint8_t)((lane_val >> (8 * b)) & 0xff);
                cpu->physRegFile().setReg(phys_reg, buf.data());
                if (vec_stuck_armed) {
                    // L0/L1 emission: one fault_id, fixed mask/polarity,
                    // explicit install generation. Install write = exposure 1.
                    noteVecStuckInstalled(
                        install_generation, correct_lane, lane_val,
                        !cpu->physFreeList().isFree(target_class, phys_reg));
                }
                // log the lane for the evidence trail
                if (write_log) {
                    *(log_stream->stream())
                        << "  [vec lane " << lane << "/" << max_lanes
                        << " width=" << lw << "bits mask=0x" << std::hex
                        << lane_mask << std::dec << "]" << std::endl;
                }
            }
        } else {
            // Scalar path (int / float / vecelem).
            gem5::RegVal reg_val = cpu->physRegFile().getReg(phys_reg);

            // §1.3/§2.1B F3 data-dependent trigger (method2 undervoltage):
            // inject ONLY when (val & triggerValueMask) == triggerValuePattern.
            // mask=0 (default) = unconditional (original behavior, zero regression).
            if (trigger_value_mask != 0) {
                if ((reg_val & trigger_value_mask) != trigger_value_pattern) {
                    if (write_log) {
                        *(log_stream->stream())
                            << "  [F3 trigger miss: val=0x" << std::hex
                            << reg_val << " & mask=0x" << trigger_value_mask
                            << " != pattern=0x" << trigger_value_pattern
                            << std::dec << " — no injection]" << std::endl;
                    }
                    return;  // data-dependent condition not met — skip
                }
                if (write_log) {
                    *(log_stream->stream())
                        << "  [F3 trigger HIT: val=0x" << std::hex << reg_val
                        << " matches (mask=0x" << trigger_value_mask
                        << ", pattern=0x" << trigger_value_pattern
                        << std::dec << ")]" << std::endl;
                }
            }

            switch (chosen) {
              case FaultType::StuckAtZero:
                reg_val &= ~mask;
                stats->numStuckAtZero++;
                stats->numPermanentFaults++;
                permanent_faults[{tid, chosen_phys_idx}] =
                    {chosen, mask, true, target_class};
                // G2: arm the write-path stuck mask so the bit is forced on
                // EVERY subsequent write to this phys slot — the correct
                // permanent (cell-stuck) model. Survives program re-writes,
                // rename reuse, and spec/commit. Polarity 0 = stuck_at_zero.
                cpu->physRegFile().setStuckTarget(target_class, chosen_phys_idx,
                                                  (uint64_t)mask, 0);
                break;
              case FaultType::StuckAtOne:
                reg_val |= mask;
                stats->numStuckAtOne++;
                stats->numPermanentFaults++;
                permanent_faults[{tid, chosen_phys_idx}] =
                    {chosen, mask, true, target_class};
                // G2: write-path stuck mask, polarity 1 = stuck_at_one.
                cpu->physRegFile().setStuckTarget(target_class, chosen_phys_idx,
                                                  (uint64_t)mask, 1);
                break;
              case FaultType::BitFlip:
                reg_val ^= mask;
                stats->numBitFlips++;
                break;
              default: break;
            }
            cpu->physRegFile().setReg(phys_reg, reg_val);
        }
        stats->numFaultsInjected++;
        ++faults_injected_count;

        // Start read-tracing this phys slot until workload end, to measure
        // whether the injected cell is actually read after injection.
        // (Closure check: SDC|read>0 should be similar for layer2 & layer3,
        //  SDC|read==0 should be ~0.) The readTraceEvent reschedules itself
        // every 1000 cycles until all threads halt, then writes the final
        // read count to the log.
        traced_phys_idx = chosen_phys_idx;
        reads_before_overwrite = 0;
        trace_overwritten = false;
        overwrite_recorded = false;
        overwritten_at_cycle = 0;
        cpu->physRegFile().setReadTraceTarget(target_class, chosen_phys_idx);
        // W2.5 L0 lifecycle interface (chaos_l0.hh): register the injected
        // item through the shared registration entry. The read/overwrite
        // hooks are CONTAINER-owned (PhysRegFile::getReg/setReg count inside
        // regfile.hh against this key) — this injector mirrors them via
        // chaosL0Sync at each poll and prints the final line from l0Final.
        chaosL0Register(l0, (uint64_t)chosen_phys_idx);
        if (!readTraceEvent.scheduled()) {
            schedule(readTraceEvent, cpu->clockEdge(Cycles(100000)));
        }

        if (write_log) {
            *(log_stream->stream())
                << "Cycle: " << cpu->curCycle()
                << ", CPU: " << cpu->name()
                << ", Thread: " << tid
                << ", Mode: " << (fi_mode == Mode::Phys ? "phys"
                              : fi_mode == Mode::ArchFrontend ? "arch_frontend"
                              : "arch_commit")
                << ", RegClass: " << (target_class == gem5::FloatRegClass
                                       ? "fp"
                                       : (target_class == gem5::VecRegClass
                                          ? "vec" : "int"))
                << ", PhysReg[" << chosen_phys_idx << "]"
                << (fi_mode == Mode::Phys
                    ? (chosen_arch_idx == -2
                       ? " (Inactive/free slot)"
                       : (chosen_arch_idx >= 0
                          ? " (Active, mapped from ArchReg[" + std::to_string(chosen_arch_idx) + "])"
                          : " (Active, held by in-flight inst, no current rename-map entry)"))
                    : (chosen_arch_idx >= 0
                       ? " (<= ArchReg[" + std::to_string(chosen_arch_idx) + "])"
                       : ""))
                << ", semanticRole: " << (semantic_role.empty() ? "-" : semantic_role)
                    << ", FaultType: " << faultTypeToString(chosen)
                << ", Mask: " << std::bitset<64>(mask)
                << ", FreeListSize: " << free_list_size_at_inject
                << ", targetSelection: "
                << (require_ready_consumer ? "ready_consumer"
                                           : "random_allocated")
                << ", selectionCandidates: " << last_selection_candidates
                << ", targetPrecision: " << target_precision
                << ", consumerSeq: " << last_selected_consumer_sn
                << ", consumerPrecision: " << last_selected_precision
                << ", faults_injected: " << faults_injected_count
                << std::endl;
        }
    }

    void
    CHAOSPhysReg::attackCheck()
    {
        if (!probability) return;
        for (ThreadID tid = 0; tid < cpu->numThreads; ++tid) {
            gem5::ThreadContext *thread_context = cpu->getContext(tid);
            if (!thread_context || thread_context->status() == ThreadContext::Halted)
                continue;
            processFault(tid);
        }
        // [FR01/FR02] A geometry/mask that cannot be honoured is a hard
        // manifest error: stop attacking instead of retrying forever or
        // silently degrading a two-bit fault to one bit. The fail-closed
        // line was already written by processFault.
        if (vec_transient_fatal) {
            unscheduleAttackEvent();
            return;
        }
        // maxFaults cap (mirrors CHAOSReg)
        if (max_faults != 0 && faults_injected_count >= max_faults) {
            unscheduleAttackEvent();
            return;
        }
        bool any_active = false;
        for (ThreadID tid = 0; tid < cpu->numThreads; ++tid) {
            gem5::ThreadContext *thread_context = cpu->getContext(tid);
            if (thread_context && thread_context->status() != ThreadContext::Halted) {
                any_active = true; break;
            }
        }
        if (any_active) {
            Cycles next = Cycles(inter_fault_cycles_dist(rng));
            if (wait_for_allocation) {
                // [FR03] Pacing: waiting for a free target must advance
                // simulation; a same-tick retry loop is never acceptable.
                if (next < Cycles(100))
                    next = Cycles(100);
                wait_for_allocation = false;
            }
            if (last_clock == 0 || (next + cpu->curCycle()) <= last_clock)
                scheduleAttackEvent(next);
        } else {
            unscheduleAttackEvent();
        }
    }

    void
    CHAOSPhysReg::checkPermanent()
    {
        // NOTE: periodic re-apply is the WRONG stuck mechanism (see project
        // notes). The correct one is a write-path mask hook in
        // PhysRegFile::setReg. This periodic re-apply is kept only as a
        // fallback for the 'arch_*' modes' compatibility and will NOT make
        // stuck faults truly permanent on O3 for the same reason CHAOSReg's
        // didn't propagate (commits vs in-flight). Phys-fi_mode stuck also needs
        // the write-path mask to be correct.
        for (auto &entry : permanent_faults) {
            if (!entry.second.update) continue;
            // [FR03] int/float/vec write-path masks are authoritative; this
            // legacy poll is only a fallback for the int space. Never treat a
            // vec index as an int index (the old bug wrote the int PRF).
            if (entry.second.reg_class != IntRegClass) continue;
            ThreadID tid = entry.first.first;
            int phys_idx = entry.first.second;
            if (phys_idx < 0 || phys_idx >= cpu->physRegFile().numIntPhysRegs()) continue;
            PhysRegIdPtr phys_reg = cpu->physRegFile().intPhysRegId(phys_idx);
            try {
                gem5::RegVal v = cpu->physRegFile().getReg(phys_reg);
                switch (entry.second.fault_type) {
                    case FaultType::StuckAtZero: v &= ~entry.second.mask; break;
                    case FaultType::StuckAtOne:  v |= entry.second.mask; break;
                    default: break;
                }
                cpu->physRegFile().setReg(phys_reg, v);
                entry.second.update = false; // (kept for compatibility; TODO remove + write-path mask)
            } catch (...) {}
            scheduleCheckPermanentFault(Cycles(1));
        }
    }

    void
    CHAOSPhysReg::readTraceCheck()
    {
        // Poll the PhysRegFile's read counter for the INJECTED VALUE.
        // Counting stops once the slot is written (injected value destroyed),
        // so reads_before_overwrite = # reads of the injected value specifically.
        reads_before_overwrite = cpu->physRegFile().getReadsBeforeOverwrite();
        // Capture the cycle at the moment the value is overwritten (once).
        if (cpu->physRegFile().isTraceOverwritten() && !overwrite_recorded) {
            overwritten_at_cycle = cpu->curCycle();
            overwrite_recorded = true;
        }
        // W2.5 L0: mirror the container-owned counters into the L0 state
        // (poll-granular overwrite stamp — tighter than the exit-callback
        // sync in l0Final; see 07-l0-lifecycle-interface.md §3.3).
        chaosL0Sync(l0, cpu->physRegFile().getReadsBeforeOverwrite(),
                    cpu->physRegFile().isTraceOverwritten(), cpu->curCycle());
        if (write_log) {
            *(log_stream->stream())
                << "ReadTracePoll: cycle " << cpu->curCycle()
                << " PhysReg[" << traced_phys_idx
                << "] reads_before_overwrite=" << reads_before_overwrite
                << " overwritten=" << (overwrite_recorded ? 1 : 0)
                << (overwrite_recorded ? (" at_cycle=" + std::to_string(overwritten_at_cycle)) : "")
                << std::endl;
        }
        bool any_active = false;
        for (ThreadID tid = 0; tid < cpu->numThreads; ++tid) {
            gem5::ThreadContext *thread_context = cpu->getContext(tid);
            if (thread_context && thread_context->status() != ThreadContext::Halted) {
                any_active = true; break;
            }
        }
        if (any_active) {
            schedule(readTraceEvent, cpu->clockEdge(Cycles(100000)));
        } else {
            if (write_log) {
                *(log_stream->stream())
                    << "ReadTraceFinal: PhysReg[" << traced_phys_idx
                    << "] reads_before_overwrite=" << reads_before_overwrite
                    << " overwritten=" << (overwrite_recorded ? 1 : 0)
                    << (overwrite_recorded ? (" at_cycle=" + std::to_string(overwritten_at_cycle)) : "")
                    << " (workload halted)"
                    << std::endl;
            }
            cpu->physRegFile().clearReadTraceTarget();
            traced_phys_idx = -1;
        }
    }

    void
    CHAOSPhysReg::l0Final()
    {
        // [FR03] Terminal backstop: emit the permanent-cell chain_end and
        // clear the defect at end of run. Idempotent (installed=false after
        // the first call), so it is safe if CHAOSPropagation's own exit
        // flush already ran.
        if (vec_emit.installed)
            emitVecTerminal();
        // [FR01/FR02] Backstop terminal; the propagation exit-flush hook is
        // the primary path (it runs while the event stream is still open).
        if (vec_transient.installed)
            finalizeVecTransient(nullptr);
        // W2.5 L0 lifecycle final line (docs/gem5-fi/ooo/
        // 07-l0-lifecycle-interface.md), printed exactly once at end of
        // sim from the exit callback registered in the constructor.
        // Sync the FRESH container counters — PhysRegFile::getReg/setReg
        // keep counting past the last poll, and the counters survive
        // clearReadTraceTarget (only the key is cleared) — so reads/...
        // are exact up to sim end; only at= stays observation-granular
        // (poll stamp if a poll saw the flip, else this exit cycle).
        // No injection ever landed (honest skip / F3 trigger miss all
        // attempts) -> no line. Crash/abort paths run no exit callbacks,
        // so Crash runs legitimately have no CHAOS_L0 line.
        if (!l0.active || !write_log)
            return;
        chaosL0Sync(l0, cpu->physRegFile().getReadsBeforeOverwrite(),
                    cpu->physRegFile().isTraceOverwritten(), cpu->curCycle());
        *(log_stream->stream()) << chaosL0Line("CHAOSPhysReg", l0)
                                 << std::endl;
    }

} // namespace gem5
