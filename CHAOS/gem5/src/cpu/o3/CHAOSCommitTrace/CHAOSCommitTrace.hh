#ifndef __CPU_O3_CHAOS_COMMIT_TRACE_HH__
#define __CPU_O3_CHAOS_COMMIT_TRACE_HH__

// CHAOSCommitTrace — W2.1 read-only L2 commit-per-instruction trace
// (docs/superpowers/plans/2026-09-24-ooo-w2-observation.md Task 1;
//  docs/gem5-fi/ooo north-star W2 / 01-observation-points.md L2). NOT an
// injector: traceCommit() only READS commit-side state (pcState /
// staticInst->getName / destRegIdx / renamedDestIdx / physRegFile().getReg)
// and writes one CSV line per committed instruction — it never schedules
// events and never writes architectural or µarch state. Proof: the workload
// FINAL checksum is byte-identical with the tracer attached (W2.1 hard gate,
// CHAOSProbe precedent).
//
// Pinned line format (W2.1 produces, W2.2 tools/commit_diff.py consumes —
// DO NOT change one side without the other):
//   seq,tid,tick,pc,op,ndest[,class,arch,phys,val]*
//     seq   self-held global commit sequence number, starts at 0 (gem5 has
//           no global counter: commitStats[tid]->numInsts is per-thread and
//           skips micro-ops; seqNum has squash holes — W2 spike fact 4)
//     tid   thread id
//     tick  curTick()
//     pc    pcState().instAddr(), hex, no 0x prefix
//     op    staticInst->getName()
//     ndest numDestRegs(); then one 4-tuple per dest register:
//       class  renamedDestIdx(i)->classValue() (RegClassType value — also
//              the class that governs how val is read from the phys regfile)
//       arch   destRegIdx(i).index() (architectural register index)
//       phys   renamedDestIdx(i)->index() (physical index within its class)
//       val    scalar classes: physRegFile().getReg(phys) as 16 hex digits,
//              zero-padded; vector classes (VecReg/VecPred/Mat): the whole
//              phys-register blob folded to 16 hex digits via FNV-1a-64.
//              MiscReg has no phys-regfile value (fixed mapping) -> zeros.
//
// Attachment: unlike CHAOSProbe, self-attach is NOT enough — the hook lives
// in Commit::commitHead (commit.cc, right after the commit-renameMap setEntry
// loop, before rob->retireHead). startup() dynamic_casts p.cpu to o3::CPU and
// calls cpu->o3Commit().setChaosCommitTrace(this) (CHAOSRAS setter pattern,
// commit.hh). [W2.4 correction 2026-09-24: the commit-side setEntry loop does
// NOT contain the injection hook — CHAOSRenameMap only hooks the FRONT rename
// map, and the front map's SimpleRenameMap::rename() writes directly without
// setEntry. The trace still captures injected mappings, but via the INST's own
// renamedDestIdx (assigned at rename time from the front map), not via any
// commit-map post-injection state.]
//
// Crash durability (W2.1 follow-up 2026-09-24, CHAOSMicroSnap pattern): the
// trace file is a raw zlib gzFile at simout.resolve(trace_file) — NOT
// simout.create's gz streambuf (that path only gzwrite()s; zlib holds data
// internally until gzclose, so an aborted run's trace came out 0 bytes /
// truncated — measured in the W2.3 C3-arm Crash rep). Rows are gzwrite()n
// through a snprintf staging buffer and gzflush(Z_SYNC_FLUSH)ed every
// FLUSH_EVERY rows, so a Crash keeps everything up to <FLUSH_EVERY rows of
// the abort point as a decodable truncated stream (commit_diff salvages the
// prefix). The gzip trailer is written by gzclose in an exit callback.

#include <zlib.h>

#include <cstdint>
#include <string>

#include "params/CHAOSCommitTrace.hh"
#include "sim/sim_object.hh"
#include "base/output.hh"
#include "base/types.hh"
#include "cpu/base.hh"

namespace gem5 { namespace o3 { class CPU; } }
namespace gem5 { namespace o3 { class DynInst; } }

namespace gem5
{

class CHAOSCommitTrace : public SimObject
{
  public:
    CHAOSCommitTrace(const CHAOSCommitTraceParams &p);
    ~CHAOSCommitTrace();

    // Self-attach: dynamic_cast O3CPU (CHAOSRAS.cc:94-102 pattern), then
    // cpu->o3Commit().setChaosCommitTrace(this). nullptr cpu member or
    // non-O3 cpu = tracer disabled (hook never fires).
    void startup() override;

    // Called from Commit::commitHead AFTER the commit-renameMap setEntry
    // loop and BEFORE rob->retireHead. READ-ONLY (see file header).
    void traceCommit(ThreadID tid, o3::DynInst *head_inst);

  private:
    // FNV-1a-64 over a vector-register blob (16-hex-digit folding).
    uint64_t fnv1a64(const void *blob, size_t n) const;

    BaseCPU *cpu;
    o3::CPU *o3cpu = nullptr;   // resolved at startup(); nullptr = disabled
    std::string trace_file;     // gzopen target (crash-durability note above)
    bool write_log;             // gate the per-instruction line writing
    gzFile gz_file = nullptr;   // raw zlib stream; see crash-durability note

    // Periodic Z_SYNC_FLUSH bookkeeping: rows written since the last flush.
    // FLUSH_EVERY bounds Crash-trace loss to <FLUSH_EVERY rows (default
    // 4096 ≈ 0.05% of a smoke-sized trace; per-row flush on 8.6M-row runs
    // costs measurable wall time, per the MicroSnap per-snapshot precedent).
    static constexpr uint64_t FLUSH_EVERY = 4096;
    uint64_t rows_since_flush = 0;

    // Self-held global commit counter (W2 spike fact 4): bumped once per
    // committed instruction while attached, independent of write_log, so the
    // seq numbering matches the commit stream even with writing disabled.
    uint64_t seq = 0;
};

} // namespace gem5

#endif // __CPU_O3_CHAOS_COMMIT_TRACE_HH__
