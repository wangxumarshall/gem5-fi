// CHAOSCommitTrace.cc — W2.1 read-only L2 commit-per-instruction trace.
// Four-piece SimObject family pattern (template: CHAOSProbe/; setter-attach
// pattern: CHAOSRAS/). See CHAOSCommitTrace.hh for the contract and the
// pinned CSV line format. Nothing here mutates CPU state: the only writes
// are to the trace file itself.

#include "cpu/o3/CHAOSCommitTrace/CHAOSCommitTrace.hh"

#include <iomanip>
#include <ostream>
#include <vector>

#include "cpu/o3/cpu.hh"          // o3::CPU: o3Commit(), physRegFile()
#include "cpu/o3/dyn_inst.hh"     // DynInst: pcState/destRegIdx/renamedDestIdx
#include "cpu/reg_class.hh"       // RegClassType values
#include "params/CHAOSCommitTrace.hh"
#include "sim/cur_tick.hh"        // curTick()

namespace gem5
{

    // File-local: print a 64-bit value as a CSV field — leading comma,
    // then exactly 16 hex digits zero-padded (the pinned `val` column
    // format) — then restore dec/fill.
    static void
    hex16(std::ostream &os, uint64_t v)
    {
        os << ',' << std::hex << std::setfill('0') << std::setw(16) << v
           << std::dec << std::setfill(' ');
    }

    CHAOSCommitTrace::CHAOSCommitTrace(const CHAOSCommitTraceParams &p)
        : SimObject(p),
          cpu(p.cpu),
          trace_file(p.traceFile),
          write_log(p.writeLog)
    {
        if (write_log) {
            // simout.create (CHAOSProbe.cc:40 pattern): a name ending in .gz
            // is opened as a gzip stream unless no_gz=true (output.hh); zlib
            // is a hard gem5 dependency (SConstruct). The file lands in the
            // run's --outdir directory.
            trace_stream = simout.create(trace_file, false, false);
            if (!trace_stream || !trace_stream->stream())
                panic("CHAOSCommitTrace: Could not open trace file %s",
                      trace_file);
        }
    }

    CHAOSCommitTrace::~CHAOSCommitTrace() {}

    void
    CHAOSCommitTrace::startup()
    {
        SimObject::startup();
        auto *o3 = dynamic_cast<o3::CPU *>(cpu);
        if (!o3) {
            warn("CHAOSCommitTrace: cpu is not an O3CPU; tracer disabled.\n");
            return;
        }
        o3cpu = o3;
        // CHAOSRAS.cc:101 setter pattern: the commit-stage pointer the
        // commit.cc hook tests. From here on every committed instruction
        // passes through traceCommit().
        o3cpu->o3Commit().setChaosCommitTrace(this);
    }

    uint64_t
    CHAOSCommitTrace::fnv1a64(const void *blob, size_t n) const
    {
        const uint8_t *p = static_cast<const uint8_t *>(blob);
        uint64_t h = 14695981039346656037ULL;  // FNV-1a 64-bit offset basis
        for (size_t i = 0; i < n; ++i) {
            h ^= p[i];
            h *= 1099511628211ULL;             // FNV-1a 64-bit prime
        }
        return h;
    }

    void
    CHAOSCommitTrace::traceCommit(ThreadID tid, o3::DynInst *head_inst)
    {
        if (!o3cpu || !head_inst)
            return;

        // seq always advances with the commit stream (write_log only gates
        // the line writing), so the numbering is stable either way.
        const uint64_t my_seq = seq++;
        if (!write_log || !trace_stream || !trace_stream->stream())
            return;

        // ---- one READ-ONLY sample of the committing instruction ----
        // (the post-injection RAT was just written by the setEntry loop in
        // the caller; renamedDestIdx below is the freshly committed mapping)
        std::ostream &os = *trace_stream->stream();
        os << my_seq << ',' << (int)tid << ',' << curTick() << ','
           << std::hex << head_inst->pcState().instAddr() << std::dec << ','
           << head_inst->staticInst->getName() << ','
           << (int)head_inst->numDestRegs();

        const int ndest = (int)head_inst->numDestRegs();
        for (int i = 0; i < ndest; ++i) {
            const PhysRegIdPtr phys = head_inst->renamedDestIdx(i);
            const RegClassType rc =
                phys ? phys->classValue() : InvalidRegClass;
            os << ',' << (int)rc
               << ',' << (unsigned)head_inst->destRegIdx(i).index();
            if (!phys) {
                // No phys id recorded (should not happen at commit): keep
                // the column count contract, mark unknown.
                os << ",-1,0000000000000000";
                continue;
            }
            os << ',' << (unsigned)phys->index();
            switch (rc) {
              // Scalar path (CHAOSPhysReg.cc:387 read pattern): RegVal.
              case IntRegClass:
              case FloatRegClass:
              case VecElemClass:
              case CCRegClass:
                hex16(os, (uint64_t)o3cpu->physRegFile().getReg(phys));
                break;
              // Vector blob path (CHAOSPhysReg.cc:336 read pattern): read
              // the WHOLE phys register, FNV-1a-64 fold to 16 hex digits.
              // VecReg width comes from vecRegBytes() (the pinned accessor,
              // regfile.hh:183); VecPred/Mat have no such accessor, so their
              // width comes from the phys reg's own RegClass::regBytes().
              case VecRegClass:
              case VecPredRegClass:
              case MatRegClass: {
                size_t vbytes = (rc == VecRegClass)
                    ? o3cpu->physRegFile().vecRegBytes()
                    : phys->regClass().regBytes();
                if (vbytes < sizeof(uint64_t))
                    vbytes = sizeof(uint64_t);  // paranoia (CHAOSPhysReg)
                std::vector<uint8_t> buf(vbytes, 0);
                o3cpu->physRegFile().getReg(phys, buf.data());
                hex16(os, fnv1a64(buf.data(), buf.size()));
                break;
              }
              // MiscRegClass (and anything unrecognized): misc regs are
              // fixed-mapping, NOT stored in the phys regfile —
              // PhysRegFile::getReg would panic. No value column content.
              default:
                os << ",0000000000000000";
                break;
            }
        }
        os << '\n';
    }

} // namespace gem5
