#include "mem/CHAOSMem/CHAOSMem.hh"
#include "params/CHAOSMem.hh"

#include <fstream>
#include <random>
#include <bitset>
#include <functional>
#include <string>     

#include "sim/sim_object.hh"
#include "sim/eventq.hh"
#include "mem/packet.hh"
#include "mem/packet_access.hh"

namespace gem5 {

    CHAOSMem::CHAOSMem(const CHAOSMemParams& p)
    : SimObject(p), 
    probability(p.probability), 
    num_bits_to_change(p.bitsToChange),
    first_clock(p.firstClock), 
    last_clock(p.lastClock),
    fault_type_enum(stringToFaultType(p.faultType)),
    fault_mask(static_cast<unsigned char>(std::stoi(p.faultMask, nullptr, 2))), 
    tick_to_clock_ratio(p.tickToClockRatio), 
    bit_flip_prob(p.bitFlipProb),
    stuck_at_zero_prob(p.stuckAtZeroProb),
    stuck_at_one_prob(p.stuckAtOneProb),
    cycles_permament_fault_check(p.cyclesPermamentFaultCheck),
    write_log(p.writeLog),
    rng_seed(p.rngSeed),
    max_faults(p.maxFaults),
    faults_injected_count(0),
    target_start(p.addr_start),
    target_end(p.addr_end),
    attackEvent([this]{ this->attackMemory(); }, name()),
    periodicCheck([this] { this->checkPermanent(); }, name() + ".periodicCheck"),
    stats(nullptr)
    {
        if (probability > 0.0) {
            if (p.mem) {
                memory = p.mem;
            }

            if (!memory) {
                warn("CHAOSMem: Memory not available. Disabling fault injection.\n");
                return;
            }
            
            log_stream = simout.create("main_mem_injections.log", false, true);
            if (!log_stream || !log_stream->stream()) {
                panic("CHAOSMem: Could not open log file");
            }
            
            if (num_bits_to_change == -1){
                std::uniform_int_distribution<int> dist(1, 8);
                num_bits_to_change = dist(rng);
            }

            Addr mem_start = memory->getAddrRange().start();
            Addr mem_size = memory->getAddrRange().size();
            
            // G4: validate the [start, end] window. Both endpoints are
            // INCLUSIVE. Clamp start to mem_start; if end is 0 or invalid,
            // set it to the last valid byte (mem_start + mem_size - 1).
            // A valid single-byte interval [n,n] must work (the old
            // dist used target_end-1, dropping the last byte).
            if (target_start < mem_start) {
                target_start = mem_start;
                warn("CHAOSMem: target_start adjusted to memory start\n");
            }
            Addr last_byte = mem_start + mem_size - 1;  // inclusive last
            if (target_end == 0 || target_end < target_start) {
                target_end = last_byte;
                warn("CHAOSMem: target_end set to memory end (inclusive)\n");
            }
            if (target_end > last_byte) target_end = last_byte; // clamp

            stats = std::make_unique<CHAOSMemStats>(this);

            target_size = target_end - target_start + 1;

            first_tick = first_clock * tick_to_clock_ratio;
            last_tick = last_clock * tick_to_clock_ratio;

            ticks_permament_fault_check = cycles_permament_fault_check * tick_to_clock_ratio;

            rng.seed(rng_seed != 0 ? rng_seed : rd());
            inter_fault_tick_dist = std::geometric_distribution<unsigned>(probability);
            
            scheduleAttack(first_tick + inter_fault_tick_dist(rng) * tick_to_clock_ratio);

            // G4: normalize the THREE real weights instead of silently
            // overwriting to 0.9/0.05/0.05 when they don't sum to 1.0.
            // (The old code clobbered user-specified distributions.)
            double wsum = bit_flip_prob + stuck_at_zero_prob + stuck_at_one_prob;
            if (wsum <= 0.0) {
                warn("CHAOSMem: fault-type weights sum to <=0; defaulting "
                     "to bit_flip=0.9/stuck_at_zero=0.05/stuck_at_one=0.05\n");
                bit_flip_prob = 0.9; stuck_at_zero_prob = 0.05;
                stuck_at_one_prob = 0.05;
                wsum = 1.0;
            }
            if (wsum != 1.0) {
                bit_flip_prob    /= wsum;
                stuck_at_zero_prob /= wsum;
                stuck_at_one_prob  /= wsum;
            }

            // G4 BUG FIX: the old weights vector was
            //   {bit_flip_prob, bit_flip_prob, stuck_at_one_prob}
            // — a DUPLICATE bit_flip and a MISSING stuck_at_zero, so the
            // discrete_distribution index 1 (which FaultType maps to
            // StuckAtZero) actually selected bit_flip. This silently broke
            // the fault-type distribution vs config. Correct order:
            //   index 0 -> bit_flip, 1 -> stuck_at_zero, 2 -> stuck_at_one
            std::vector<double> weights = {bit_flip_prob,
                                            stuck_at_zero_prob,
                                            stuck_at_one_prob};
            random_fault_distribution = std::discrete_distribution<int>(weights.begin(), weights.end());

            scheduleCheckPermanentFault(first_tick + ticks_permament_fault_check);
        }
    }

    CHAOSMem::CHAOSMemStats::CHAOSMemStats(statistics::Group *parent)
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
    {
    }

    CHAOSMem::~CHAOSMem() {}

    CHAOSMem::FaultType 
    CHAOSMem::stringToFaultType(const std::string &s) {
        if (s == "bit_flip") return FaultType::BitFlip;
        else if (s == "stuck_at_zero") return FaultType::StuckAtZero;
        else if (s == "stuck_at_one") return FaultType::StuckAtOne;
        return FaultType::Random;
    }

    const char* 
    CHAOSMem::faultTypeToString(CHAOSMem::FaultType f) {
        switch (f) {
            case FaultType::BitFlip: return "bit_flip";
            case FaultType::StuckAtZero: return "stuck_at_zero";
            case FaultType::StuckAtOne: return "stuck_at_one";
        }
        return "random";
    }

    void 
    CHAOSMem::scheduleAttack(Tick time) {
        if (!attackEvent.scheduled()) {
            schedule(attackEvent, time);
        }
    }

    void 
    CHAOSMem::scheduleCheckPermanentFault(Tick time)
    {
        if (!periodicCheck.scheduled()) {
            schedule(periodicCheck, time);
        }
    }

    unsigned char 
    CHAOSMem::generateRandomMask(std::mt19937 &rng, int bits_to_change, int len)
    {
        unsigned char mask = 0;
        std::uniform_int_distribution<int> bitDist(0, len-1);

        for (int i = 0; i < bits_to_change; i++) {
            // G1/G4: unsigned shift (1U <<), no signed-shift UB for bit>=31.
            mask |= (1U << bitDist(rng));
        }
        return mask;
    }

    void 
    CHAOSMem::attackMemory() {
        if (!memory) {
            warn("CHAOSMem: Memory not available.\n");
            scheduleAttack(curTick() + inter_fault_tick_dist(rng) * tick_to_clock_ratio);
            return;
        }

        // G4: [target_start, target_end] BOTH inclusive — the old code used
        // (target_end - 1), silently dropping the last byte of the range.
        // With the constructor setting target_end = mem_start + mem_size - 1,
        // the old dist spanned [start, end-1] = excluded the final byte.
        std::uniform_int_distribution<Addr> dist(target_start, target_end);
        Addr target_addr = dist(rng);

        try {
            // Attack a single byte
            uint8_t data;
            RequestPtr req = std::make_shared<Request>(target_addr, sizeof(data), 0, 0);
            PacketPtr read_pkt = new Packet(req, MemCmd::ReadReq);
            read_pkt->dataStatic(&data);

            memory->access(read_pkt);

            // G5: capture the OLD value (before injection) for the evidence log.
            uint8_t old_value = data;

            unsigned char mask = (fault_mask != 0) ? fault_mask : generateRandomMask(rng, num_bits_to_change, sizeof(data) << 3);

            FaultType chosen_fault_type_enum = fault_type_enum;
            if (fault_type_enum == FaultType::Random) {
                int faultIdx = random_fault_distribution(rng);
                chosen_fault_type_enum = static_cast<FaultType>(faultIdx);
            }

            switch (chosen_fault_type_enum) {
                case FaultType::StuckAtZero:
                    data &= ~mask;
                    stats->numStuckAtZero++;
                    stats->numPermanentFaults++;
                    permanent_faults[target_addr] = {chosen_fault_type_enum, mask, true};
                    break;
                case FaultType::StuckAtOne:
                    data |= mask;
                    stats->numStuckAtOne++;
                    stats->numPermanentFaults++;
                    permanent_faults[target_addr] = {chosen_fault_type_enum, mask, true};
                    break;
                case FaultType::BitFlip:
                    data ^= mask;
                    stats->numBitFlips++;
                    break;
                default:
                    break;
            }

            PacketPtr write_pkt = new Packet(req, MemCmd::WriteReq);
            write_pkt->dataStatic(&data);

            memory->access(write_pkt);
            stats->numFaultsInjected++;
            ++faults_injected_count;   // G5: count this valid injection

            delete read_pkt;
            delete write_pkt;

            if (write_log){
                // G5: evidence log — old/new value + width + mask + type +
                // target identity + trigger (tick) + seed (recorded at ctor,
                // echoed here for traceability) + faults_injected count.
                *(log_stream->stream()) << "Tick: " << curTick()
                    << ", target addr: " << target_addr
                    << ", old: 0x" << std::hex << (unsigned)old_value
                    << ", new: 0x" << (unsigned)data
                    << ", Mask: 0x" << (unsigned)mask
                    << ", width_bits: 8"
                    << ", Fault Type: " << faultTypeToString(chosen_fault_type_enum)
                    << ", seed: " << std::dec << rng_seed
                    << ", faults_injected: " << faults_injected_count
                    << std::dec << std::endl;
            }

        } catch (const std::exception &e) {
            *(log_stream->stream())  << "Error: Exception during fault injection. "
                    << "Target Addr: " << target_addr
                    << ", Error: " << e.what() << std::endl;
        } catch (...) {
            *(log_stream->stream())  << "Error: Unknown exception during fault injection. "
                    << "Target Addr: " << target_addr << std::endl;
        }

        // G5: single-fault enforcement. If we've injected max_faults, STOP
        // rescheduling — the original CHAOSMem had no cap and re-injected
        // forever (observed: maxFaults=1 param ignored, 5 injections logged
        // in one tick). max_faults==0 = unlimited (original behavior).
        if (max_faults != 0 && faults_injected_count >= max_faults) {
            return;  // do not reschedule
        }

        Tick next_injection = curTick() + inter_fault_tick_dist(rng) * tick_to_clock_ratio;

        if (next_injection <= last_tick || last_tick == 0) {
            scheduleAttack(next_injection);
        }
    }

    void CHAOSMem::checkPermanent()
    {
        for (auto &entry : permanent_faults) {
            if (!entry.second.update)
                continue;

            Addr target_addr = entry.first;
            const PermanentFault &fault = entry.second;

            try {
                uint8_t data;
                RequestPtr req = std::make_shared<Request>(target_addr, sizeof(uint8_t), 0, 0);
                PacketPtr read_pkt = new Packet(req, MemCmd::ReadReq);
                read_pkt->dataStatic(&data);

                memory->access(read_pkt);

                switch (fault.fault_type) {
                    case FaultType::StuckAtZero:
                        data &= ~fault.mask;
                        break;
                    case FaultType::StuckAtOne:
                        data |= fault.mask;
                        break;
                    default:
                        break;
                }

                PacketPtr write_pkt = new Packet(req, MemCmd::WriteReq);
                write_pkt->dataStatic(&data);

                memory->access(write_pkt);
                entry.second.update = false;

                delete read_pkt;
                delete write_pkt;
            } catch (const std::exception &e) {
                *(log_stream->stream())  << "Error: Exception during fault injection. "
                        << "Target Addr: " << target_addr
                        << ", Error: " << e.what() << std::endl;
            } catch (...) {
                *(log_stream->stream())  << "Error: Unknown exception during fault injection. "
                        << "Target Addr: " << target_addr << std::endl;
            }
        }
        scheduleCheckPermanentFault(curTick() + ticks_permament_fault_check);
    }

} // namespace gem5