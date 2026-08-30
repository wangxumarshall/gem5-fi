#ifndef __MEM_CHAOSMem_HH__
#define __MEM_CHAOSMem_HH__

#include <random>
#include <bitset>
#include <string>
#include <cstdint>
#include <functional>

#include "sim/sim_object.hh"
#include "mem/abstract_mem.hh"
#include "sim/eventq.hh"
#include "base/types.hh"
#include "params/CHAOSMem.hh"
#include "mem/packet.hh"
#include <stdexcept>
#include "base/output.hh"

namespace gem5 {

  class CHAOSMem : public SimObject {
    public:
      CHAOSMem(const CHAOSMemParams& p);
      ~CHAOSMem();

    private:
      enum class FaultType {
          BitFlip,
          StuckAtZero,
          StuckAtOne,
          Random
      };
      
      struct PermanentFault {
        FaultType fault_type;
        uint8_t mask;
        bool update;
      };

      memory::AbstractMemory* memory;
      float probability;
      int num_bits_to_change;
      int corruption_size;
      uint64_t first_clock, last_clock;
      FaultType fault_type_enum;
      unsigned char fault_mask;
      int tick_to_clock_ratio;
      float bit_flip_prob, stuck_at_zero_prob, stuck_at_one_prob;
      int cycles_permament_fault_check;
      bool write_log;
      uint64_t rng_seed;
      uint64_t max_faults;            // G5: 0 = unlimited; else cap
      uint64_t faults_injected_count; // G5: running count
      Addr target_start, target_end, target_size;

      // §1.2 protection-aware modeling layer (N1 TRM Table 9-1 PROXY).
      // DRAM = 'secded' (Huawei DDR ECC). applyProtection() runs BEFORE the
      // write-back so an undo (Corrected) restores the original byte. Default
      // "none" = raw upper bound = leave = escape, zero regression.
      std::string protection_model;
      enum class ProtectionOutcome { Raw, Corrected, Latent, SilentEscape };
      static ProtectionOutcome stringToProtectionModel(const std::string &s);
      const char* protectionOutcomeToString(CHAOSMem::ProtectionOutcome o);
      // Post-injection protection: acts on the mutated `data` byte (by ref)
      // before write-back. 1-bit secded -> undo (restore orig = Corrected);
      // 2-bit -> poison-log + leave (Latent, no poison bit E3); >=3 -> Silent;
      // none -> Raw (leave). Returns outcome; logs it.
      ProtectionOutcome applyProtection(uint8_t &data, uint8_t mask,
                                        uint8_t orig_byte, FaultType ft);

      EventFunctionWrapper attackEvent, periodicCheck;
      Tick first_tick, last_tick, ticks_permament_fault_check;
      
      unsigned char generateRandomMask(std::mt19937 &rng, int bits_to_change, int len);
      void attackMemory();
      void scheduleAttack(Tick time);
      void scheduleCheckPermanentFault(Tick time);
      void checkPermanent();
      const char* faultTypeToString(CHAOSMem::FaultType f);
      static FaultType stringToFaultType(const std::string &s);

      std::geometric_distribution<unsigned> inter_fault_tick_dist;
      std::discrete_distribution<int> random_fault_distribution;
      
      std::mt19937 rng;
      std::random_device rd;
      std::map<Addr, PermanentFault> permanent_faults;
      OutputStream *log_stream;

      struct CHAOSMemStats : public statistics::Group
      {
        statistics::Scalar numFaultsInjected;
        statistics::Scalar numBitFlips;
        statistics::Scalar numStuckAtZero;
        statistics::Scalar numStuckAtOne;
        statistics::Scalar numPermanentFaults;
        
        CHAOSMemStats(statistics::Group *parent);
      };

      std::unique_ptr<CHAOSMemStats> stats;
  };

} // namespace gem5

#endif // __MEM_CHAOSMem_HH__