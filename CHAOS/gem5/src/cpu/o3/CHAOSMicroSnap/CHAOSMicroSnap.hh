#ifndef __CPU_O3_CHAOS_MICRO_SNAP_HH__
#define __CPU_O3_CHAOS_MICRO_SNAP_HH__

// CHAOSMicroSnap — W2.4 read-only L1 µarchitecture shadow snapshot sampler
// (docs/superpowers/plans/2026-09-24-ooo-w2-observation.md Task 4;
//  docs/gem5-fi/ooo north-star W2 / 01-observation-points.md L1). NOT an
// injector: maybeSample() only READS commit-side µarch state and writes one
// CSV row every `snapEvery` committed instructions — it never schedules
// events and never writes architectural or µarch state. Proof: the workload
// FINAL checksum is byte-identical with the sampler attached (W2.4 hard
// gate, CHAOSProbe/CHAOSCommitTrace precedent). Like W2.1 it also prints
// NOTHING to stdout, so the full stdout stays byte-comparable.
//
// What one snapshot row captures (all read at the SAME commit-side anchor
// point as the W2.1 trace — Commit::commitHead after the commit-renameMap
// setEntry loop, before rob->retireHead):
//   - occupancies (CHAOSProbe.cc read pattern):
//       rob_occ  o3ROB().countInsts()               (all threads)
//       iq_occ   o3IEW().instQueue.getCount(0)      (thread 0)
//       fl_int/fl_fp/fl_vec  physFreeList().numFreeRegs(<class>)
//   - ROB head/tail seqNum (rob.hh readHeadInst/readTailInst; 0 when the
//     ROB end is empty — head is the inst being committed and is still in
//     the ROB at the hook point, so head is never 0 in practice)
//   - the RAT: thread `tid`'s FRONT rename map (cpu->frontRenameMap(), the
//     rename alias table proper — this is where the CHAOSRenameMap
//     map_bitflip/f5_substitute corruption lands: the injector self-attaches
//     to frontRenameMap()[0] and mutates entries at front-map setEntry calls
//     = squash rollbacks. The COMMIT rename map is a derived copy only ever
//     written from inst->renamedDestIdx, so it never carries the injected
//     entry directly; snapshotting the front map is what makes the directed
//     W2.4 acceptance "RAT divergence > 0 after a known injection" real).
//     Per class (Int/Float/VecReg), TWO quantities are dumped:
//       rat_<c>_hash   FNV-1a-64 over the (arch,phys) pair sequence:
//                     for each arch index i with mapped phys p:
//                       h = (h ^ i) * 1099511628211; h = (h ^ p) * 1099511628211
//                     (init 14695981039346656037 — order-sensitive, portable)
//       rat_<c>_table  the FULL arch->phys table, compact "0:5;1:6;..."
//                     (';' between entries — the row is comma-separated CSV
//                     with an exact 16-column contract, so entry lists inside
//                     a column must not use the CSV separator). A null
//                     PhysRegIdPtr entry prints as 65535, the same sentinel
//                     W2.1 uses for invalid phys ids. The full table is
//                     dumped rather than a diff-vs-previous because the L1
//                     reference is the NO-FAULT run, which gem5 side cannot
//                     see; tools/micro_diff.py aligns two runs by snap_seq
//                     and counts diverging entries per class.
//
// Pinned line format (W2.4 produces, tools/micro_diff.py consumes — DO NOT
// change one side without the other). One leading '#' comment line names
// the columns; every following line is:
//   snap_seq,commit_seq,tick,rob_occ,iq_occ,fl_int,fl_fp,fl_vec,
//   rob_head,rob_tail,rat_int_hash,rat_fp_hash,rat_vec_hash,
//   rat_int_table,rat_fp_table,rat_vec_table
//     snap_seq   snapshot counter, starts at 0 (one row per snapEvery commits)
//     commit_seq self-held global commit counter at sample time (counts EVERY
//                commitHead call incl. micro-ops, same semantics as the W2.1
//                trace seq — gem5 has no global counter, W2 spike fact 4)
//     tick       curTick()
//
// Crash durability: the snapshot file is a raw zlib gzFile opened at
// simout.resolve(trace_file) — NOT simout.create's gz streambuf. Reason
// (measured on this host, zlib gzwrite test): the streambuf path only ever
// calls gzwrite, and bare gzwrite holds data inside zlib's internal state —
// a run that dies by fatal/abort (the rename-inconsistency Crash class)
// loses the WHOLE file (0 bytes observed on the directed W2.4 verification
// before this fix), because SIGABRT bypasses the gzclose in the stream
// destructor. Here every row is followed by gzflush(Z_SYNC_FLUSH), so a
// crashed run still leaves every completed row readable on disk; the file
// then lacks only the gzip trailer, which tools/micro_diff.py treats as a
// truncated stream (salvaged prefix, honest "truncated" flag). zlib is a
// hard gem5 dependency (SConstruct).
//
// Attachment: same setter pattern as W2.1 — startup() dynamic_casts p.cpu to
// o3::CPU and calls cpu->o3Commit().setChaosMicroSnap(this); the commit.cc
// hook (second call at the W2.1 anchor point) calls maybeSample(). nullptr
// member = sampler disabled (hook never fires, zero regression).

#include <zlib.h>

#include <cstdint>
#include <string>

#include "params/CHAOSMicroSnap.hh"
#include "sim/sim_object.hh"
#include "base/output.hh"
#include "base/types.hh"
#include "cpu/base.hh"

namespace gem5 { namespace o3 { class CPU; } }
namespace gem5 { namespace o3 { class DynInst; } }

namespace gem5
{

class CHAOSMicroSnap : public SimObject
{
  public:
    CHAOSMicroSnap(const CHAOSMicroSnapParams &p);
    ~CHAOSMicroSnap();

    // Self-attach: dynamic_cast O3CPU (CHAOSCommitTrace pattern), then
    // cpu->o3Commit().setChaosMicroSnap(this). nullptr cpu member or non-O3
    // cpu = sampler disabled (hook never fires).
    void startup() override;

    // Called from Commit::commitHead at the W2.1 anchor point (after the
    // commit-renameMap setEntry loop, before rob->retireHead), once per
    // committed instruction. READ-ONLY (see file header); the internal
    // counter bumps once per call and one snapshot row is emitted every
    // snapEvery calls.
    void maybeSample(ThreadID tid, o3::DynInst *head_inst);

  private:
    BaseCPU *cpu;
    o3::CPU *o3cpu = nullptr;   // resolved at startup(); nullptr = disabled
    uint64_t snap_every;
    std::string trace_file;     // simout.resolve target (.gz, self-managed)
    bool write_log;             // gate the snapshot row writing
    gzFile gz_file = nullptr;   // raw zlib stream; see crash-durability note

    // Self-held counters (W2 spike fact 4): commit_count follows the commit
    // stream even with writing disabled; snap_seq numbers the emitted rows.
    uint64_t commit_count = 0;
    uint64_t snap_seq = 0;
};

} // namespace gem5

#endif // __CPU_O3_CHAOS_MICRO_SNAP_HH__
