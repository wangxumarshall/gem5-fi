#include "arch/arm/CHAOSArmSysReg/CHAOSArmSysReg.hh"
#include "params/CHAOSArmSysReg.hh"
#include "arch/arm/isa.hh"
#include "arch/arm/regs/misc.hh"
#include "base/output.hh"
#include "sim/core.hh"  // getClockFrequency (global tick frequency)
#include <sstream>

namespace gem5
{

    CHAOSArmSysReg::CHAOSArmSysReg(const CHAOSArmSysRegParams &p)
        : SimObject(p),
          isa(p.isa),
          probability(p.probability),
          fault_type_enum(stringToFaultType(p.faultType)),
          fault_mask(p.faultMask),
          num_bits_to_change(p.bitsToChange),
          first_clock(Cycles(p.firstClock)),
          last_clock(Cycles(p.lastClock)),
          max_faults(p.maxFaults),
          faults_injected_count(0),
          rng_seed(p.rngSeed),
          write_log(p.writeLog),
          whitelist_str(p.targetRegs),
          stats(nullptr)
    {
        if (probability > 0.0f) {
            log_stream = simout.create("sysreg_injections.log", false, true);
            if (!log_stream || !log_stream->stream()) {
                panic("CHAOSArmSysReg: Could not open log file");
            }
            stats = std::make_unique<CHAOSArmSysRegStats>(this);
            rng.seed(rng_seed != 0 ? rng_seed : rd());
            random_fault_distribution = std::discrete_distribution<int>(
                {0.9, 0.05, 0.05});  // bit_flip / stuck0 / stuck1
            parseWhitelist(p.targetRegs);
            // SELF-ATTACH to the target ISA (same pattern as CHAOSLSQFwd and
            // CHAOSArmTLB: the ISA's `chaosSysReg` field is public; set it
            // here so readMiscRegNoEffect can reach this injector. `isa` was
            // passed as a Param and is constructed first. Safe because
            // readMiscRegNoEffect only reads chaosSysReg during MRS execute,
            // long after SimObject construction. Avoids a python binding for
            // setChaosSysReg (which has none).
            if (isa) {
                isa->chaosSysReg = this;
                inform("CHAOSArmSysReg: SELF-ATTACH to ISA %s (whitelist %d regs)\n",
                       isa->name(), (int)whitelist.size());
            } else {
                warn("CHAOSArmSysReg: isa param is NULL — SELF-ATTACH failed; "
                     "hook will be inactive.\n");
            }
        }
    }

    void
    CHAOSArmSysReg::startup()
    {
        // Convert the first/last Cycles window to Tick at sim-start (the
        // global tick frequency is fixed by then). first_clock/last_clock are
        // SIM cycles (global tick domain), not CPU cycles — this is an
        // approximate advisory window (same limitation as CHAOSArmTLB, since
        // the ISA is not a ClockedObject and can't reach the CPU clockEdge).
        // Ticks per cycle = (1e12 ticks/s) / (cycles/s); for the standard
        // 1 GHz sim clock that's 1000 ticks/cycle.
        Tick tps = getClockFrequency();  // global ticks per second
        // 1 cycle = tps / clock_hz ticks; but we don't know the CPU clock_hz
        // from the ISA. Use the sim convention: treat first_clock as cycles
        // of the global 1e12-tick domain -> ticks = first_clock * (tps/1e9)
        // for a 1GHz nominal. To stay domain-agnostic, store cycle count and
        // compare in ticks via curTick()/ (tps/1e9). Simplest: assume the
        // standard 1GHz CPU (1000 tick/cycle) — documented approximation.
        first_tick = first_clock * 1000;  // 1 GHz nominal: 1000 tick/cycle
        last_tick = (last_clock == Cycles(0)) ? 0 : (last_clock * 1000);
    }

    CHAOSArmSysReg::~CHAOSArmSysReg() {}

    CHAOSArmSysReg::FaultType
    CHAOSArmSysReg::stringToFaultType(const std::string &s) {
        if (s == "bit_flip") return FaultType::BitFlip;
        if (s == "stuck_at_zero") return FaultType::StuckAtZero;
        if (s == "stuck_at_one") return FaultType::StuckAtOne;
        if (s == "value_to_legal") return FaultType::ValueToLegal;
        return FaultType::Random;
    }

    const char*
    CHAOSArmSysReg::faultTypeToString(CHAOSArmSysReg::FaultType f) {
        switch (f) {
            case FaultType::BitFlip: return "bit_flip";
            case FaultType::StuckAtZero: return "stuck_at_zero";
            case FaultType::StuckAtOne: return "stuck_at_one";
            case FaultType::ValueToLegal: return "value_to_legal";
            case FaultType::Random: return "random";  // G7: clear -Wswitch
        }
        return "random";
    }

    void
    CHAOSArmSysReg::parseWhitelist(const std::string &s) {
        // Parse "NAME1,NAME2,..." into MiscReg indices by matching against
        // the ArmISA::miscRegName[] array. Unknown names are skipped with
        // a warning (no crash — a typo shouldn't abort the whole sim).
        if (s.empty()) return;
        std::stringstream ss(s);
        std::string tok;
        while (std::getline(ss, tok, ',')) {
            // trim whitespace
            tok.erase(0, tok.find_first_not_of(" \t"));
            tok.erase(tok.find_last_not_of(" \t") + 1);
            if (tok.empty()) continue;
            bool found = false;
            for (uint32_t i = 0; i < ArmISA::NUM_MISCREGS; ++i) {
                if (ArmISA::miscRegName[i] && tok == ArmISA::miscRegName[i]) {
                    whitelist.insert(i);
                    found = true;
                    break;
                }
            }
            if (!found && write_log) {
                *(log_stream->stream())
                    << "CHAOSArmSysReg: whitelist name '" << tok
                    << "' not a known MiscReg — skipped." << std::endl;
            }
        }
        if (write_log) {
            *(log_stream->stream())
                << "CHAOSArmSysReg: whitelist has " << whitelist.size()
                << " register(s): " << whitelist_str << std::endl;
        }
    }

    uint64_t
    CHAOSArmSysReg::generateRandomMask(int bits_to_change) {
        uint64_t mask = 0;
        std::uniform_int_distribution<int> bitDist(0, 63);
        while (bits_to_change-- > 0) mask |= (1ULL << bitDist(rng));
        return mask;
    }

    bool
    CHAOSArmSysReg::maybeCorrupt(uint32_t idx, const char *reg_name,
                                 RegVal &val)
    {
        if (probability <= 0.0f || whitelist.empty()) return false;
        if (whitelist.find(idx) == whitelist.end()) return false;  // not whitelisted
        if (max_faults != 0 && faults_injected_count >= max_faults) return false;

        // Clock window (advisory, same approach as CHAOSArmTLB): the ISA is a
        // SimObject (not ClockedObject), so we can't reach curCycle()/clockEdge
        // directly here. Use the global curTick() vs first_clock/last_clock
        // interpreted as tick values (approximate — 1 cycle = clock period
        // ticks; for the standard 1 GHz sim clock, 1 cycle == 1000 ticks).
        // last_clock==0 means unrestricted. This gates injection to a window
        // after warmup; exact cycle precision is a G6-extension concern.
        Tick now = curTick();
        if (now < first_tick) return false;
        if (last_tick != 0 && now > last_tick) return false;

        // Probability gate: per-read Bernoulli.
        std::uniform_real_distribution<float> probDist(0.0f, 1.0f);
        if (probDist(rng) > probability) return false;

        FaultType chosen = fault_type_enum;
        if (fault_type_enum == FaultType::Random) {
            int i = random_fault_distribution(rng);
            chosen = static_cast<FaultType>(i);
        }

        // §2.10 F5 value_to_legal (Phase 4.5): substitute with the CURRENT
        // value of ANOTHER whitelisted sysreg (legal in-use configuration ->
        // silent misconfiguration instead of an illegal-value fault). Needs
        // >= 2 whitelist entries; single-entry whitelist declines honestly.
        if (chosen == FaultType::ValueToLegal) {
            if (whitelist.size() < 2) return false;
            uint32_t other = idx;
            for (int t = 0; t < 16 && other == idx; ++t) {
                auto it = whitelist.begin();
                std::advance(it, rng() % whitelist.size());
                other = *it;
            }
            if (other == idx) return false;
            RegVal old_val = val;
            val = isa->readMiscRegNoEffect(other);
            stats->numFaultsInjected++;
            ++faults_injected_count;
            if (write_log) {
                *(log_stream->stream())
                    << "Tick: " << curTick()
                    << ", Site: arm_sysreg_read"
                    << ", Reg: " << (reg_name ? reg_name : "(?)")
                    << ", idx: " << idx
                    << ", old: 0x" << std::hex << old_val
                    << ", new: 0x" << val
                    << ", FaultType: value_to_legal"
                    << ", source_reg_idx: " << std::dec << other
                    << std::endl;
            }
            return true;
        }

        uint64_t mask = fault_mask ? fault_mask : generateRandomMask(
            num_bits_to_change);
        if (mask == 0) return false;

        RegVal old_val = val;
        switch (chosen) {
            case FaultType::StuckAtZero:
                val &= ~mask;
                stats->numStuckAtZero++;
                break;
            case FaultType::StuckAtOne:
                val |= mask;
                stats->numStuckAtOne++;
                break;
            case FaultType::BitFlip:
                val ^= mask;
                stats->numBitFlips++;
                break;
            default: break;
        }
        stats->numFaultsInjected++;
        ++faults_injected_count;

        if (write_log) {
            *(log_stream->stream())
                << "Tick: " << curTick()
                << ", Site: arm_sysreg_read"
                << ", Reg: " << (reg_name ? reg_name : "(?)")
                << ", idx: " << idx
                << ", old: 0x" << std::hex << old_val
                << ", new: 0x" << val
                << ", FaultType: " << faultTypeToString(chosen)
                << ", Mask: 0x" << mask << std::dec
                << std::endl;
        }
        return true;
    }

    CHAOSArmSysReg::CHAOSArmSysRegStats::CHAOSArmSysRegStats(
            statistics::Group *parent)
        : statistics::Group(parent),
          ADD_STAT(numFaultsInjected, statistics::units::Count::get(),
                   "Total sys-reg faults injected"),
          ADD_STAT(numBitFlips, statistics::units::Count::get(),
                   "Sys-reg bit-flip faults"),
          ADD_STAT(numStuckAtZero, statistics::units::Count::get(),
                   "Sys-reg stuck-at-zero faults"),
          ADD_STAT(numStuckAtOne, statistics::units::Count::get(),
                   "Sys-reg stuck-at-one faults")
    {}

} // namespace gem5
