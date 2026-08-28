#ifndef __CHAOSReg_HH__
#define __CHAOSReg_HH__

#include <random>
#include <bitset>

#include "params/CHAOSReg.hh"
#include "sim/sim_object.hh"
#include "sim/eventq.hh"
#include "cpu/base.hh"

#include <stdexcept>
#include "base/output.hh"

namespace gem5
{
  class CHAOSReg : public SimObject
  {
    public:
      CHAOSReg(const CHAOSRegParams &p);
      ~CHAOSReg();

    private:
      enum class FaultType {
          BitFlip,
          StuckAtZero,
          StuckAtOne,
          Random
      };

      enum class TargetClass {
          Both,
          Integer,
          FloatingPoint
      };
      
      struct PermanentFault {
        FaultType fault_type;
        uint64_t mask;
        bool update;
      };

      BaseCPU *cpu;
      float probability;
      int num_bits_to_change;
      Cycles first_clock, last_clock;
      uint64_t max_faults;             // 0 = unlimited
      uint64_t faults_injected_count; // running count of injected faults
      uint64_t rng_seed;               // 0 = seed from random_device (orig); else fixed
      uint64_t max_reg_idx;            // 0 = full numRegs()-1; else upper bound (exclusive)
      int target_reg_idx;              // G1/report #5: directed reg index; -1 = random
      uint64_t fault_mask;             // G1: dynamic-width (64-bit) bitmask; 0 = random
      int fault_mask_width;            // G1: width in bits (64 for X regs)
      FaultType fault_type_enum;
      float bit_flip_prob, stuck_at_zero_prob, stuck_at_one_prob;
      Cycles cycles_permament_fault_check;
      TargetClass reg_target_class_enum;
      Addr PC_target;
      bool write_log;

      EventFunctionWrapper attackEvent, periodicCheck;

      int generateRandomMask(std::mt19937 &gen, int bits_to_change, int len);
      // G1: width-aware mask. len in bits (e.g. 64 for AArch64 X regs).
      // Returns a uint64_t with `bits_to_change` distinct bits set in [0,len).
      // Uses unsigned (1ULL <<) to avoid the signed-shift UB of the old
      // `int mask; 1 << bit` (which was UB for bit >= 32).
      uint64_t generateRandomMask64(std::mt19937 &gen, int bits_to_change, int len);
      void processFault(ThreadID tid);
      void scheduleAttackEvent(Cycles delay);
      void unscheduleAttackEvent();
      void scheduleCheckPermanentFault(Cycles delay);
      void checkPermanent();
      void attackCheck();
      const char* faultTypeToString(CHAOSReg::FaultType f);
      static FaultType stringToFaultType(const std::string &s);
      static TargetClass stringToTargetClass(const std::string &s);

      std::geometric_distribution<unsigned> inter_fault_cycles_dist;
      std::discrete_distribution<int> random_fault_distribution;

      std::mt19937 rng;
      std::random_device rd;
      std::map<std::pair<ThreadID, gem5::RegId>, PermanentFault> permanent_faults;
      OutputStream *log_stream;

      struct CHAOSRegStats : public statistics::Group
      {
        statistics::Scalar numFaultsInjected;
        statistics::Scalar numBitFlips;
        statistics::Scalar numStuckAtZero;
        statistics::Scalar numStuckAtOne;
        statistics::Scalar numPermanentFaults;
        
        CHAOSRegStats(statistics::Group *parent);
      };
      
      std::unique_ptr<CHAOSRegStats> stats;
  };

} // namespace gem5
#endif // __CHAOSReg_HH__