// CHAOSCommitTrace.cc — W2.1 read-only L2 commit-per-instruction trace.
// Four-piece SimObject family pattern (template: CHAOSProbe/; setter-attach
// pattern: CHAOSRAS/). See CHAOSCommitTrace.hh for the contract and the
// pinned CSV line format. Nothing here mutates CPU state: the only writes
// are to the trace file itself.
//
// W2.1 follow-up (2026-09-24): the write path is a raw zlib gzFile with
// periodic gzflush(Z_SYNC_FLUSH) (CHAOSMicroSnap pattern, proven there on an
// aborted run) — the simout.create gz streambuf holds rows inside zlib until
// gzclose, so Crash/abort runs used to come out truncated (W2.3 C3-arm rep1
// measured: 2.3 MB salvageable only by luck of the streambuf's own flushing).

#include "cpu/o3/CHAOSCommitTrace/CHAOSCommitTrace.hh"

#include <cstdio>
#include <string>
#include <vector>

#include "cpu/o3/cpu.hh"          // o3::CPU: o3Commit(), physRegFile()
#include "cpu/o3/dyn_inst.hh"     // DynInst: pcState/destRegIdx/renamedDestIdx
#include "cpu/reg_class.hh"       // RegClassType values
#include "params/CHAOSCommitTrace.hh"
#include "sim/cur_tick.hh"        // curTick()
#include "sim/sim_exit.hh"        // registerExitCallback

namespace gem5
{

    CHAOSCommitTrace::CHAOSCommitTrace(const CHAOSCommitTraceParams &p)
        : SimObject(p),
          cpu(p.cpu),
          trace_file(p.traceFile),
          write_log(p.writeLog)
    {
        if (write_log) {
            // Raw zlib gzFile at the simout-resolved path (NOT simout.create's
            // gz streambuf — see the file header). zlib is a hard gem5
            // dependency (SConstruct); the file lands in the run's --outdir.
            const std::string path = simout.resolve(trace_file);
            gz_file = gzopen(path.c_str(), "wb");
            if (!gz_file)
                panic("CHAOSCommitTrace: Could not open trace file %s",
                      path.c_str());
            // Normal-exit trailer: gzclose writes it. MUST run in an exit
            // callback, not the destructor — gem5's exit path does not
            // reliably run SimObject destructors (MicroSnap measurement).
            // Aborted runs never get here: they keep the Z_SYNC_FLUSH-ed
            // truncated stream, which tools/commit_diff.py salvages.
            registerExitCallback([this]() {
                if (gz_file) {
                    gzclose(gz_file);
                    gz_file = nullptr;
                }
            });
        }
    }

    CHAOSCommitTrace::~CHAOSCommitTrace()
    {
        // Backstop only (the exit callback above is the primary closer). On
        // an aborted run neither runs — fine: every FLUSH_EVERY-boundary row
        // was already flushed and the file is a decodable truncated stream.
        if (gz_file) {
            gzclose(gz_file);
            gz_file = nullptr;
        }
    }

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
        if (!write_log || !gz_file)
            return;

        // ---- one READ-ONLY sample of the committing instruction ----
        // [W2.4 correction: renamedDestIdx below is the mapping the INST was
        // assigned at rename time (from the front map, where the injector
        // lives); the commit-side setEntry loop that just ran does NOT
        // contain the injection hook.]
        //
        // Row assembly: snprintf into a staging buffer, then a bounded number
        // of gzwrite()s (prefix / op name / dests), then the periodic
        // gzflush. Buffer math: prefix <= 64, one dest quad <= 4+1+3+1+5+1
        // +16+1 = 32, ndest is small (<= ~6 on AArch64); 1024 is generous.
        char buf[1024];
        int n = std::snprintf(buf, sizeof buf, "%llu,%d,%llu,%llx,",
                              (unsigned long long)my_seq, (int)tid,
                              (unsigned long long)curTick(),
                              (unsigned long long)
                                  head_inst->pcState().instAddr());
        gzwrite(gz_file, buf, n);

        const std::string op_name = head_inst->staticInst->getName();
        gzwrite(gz_file, op_name.c_str(), op_name.size());

        const int ndest = (int)head_inst->numDestRegs();
        char *p = buf;
        char *const end = buf + sizeof buf;
        p += std::snprintf(p, end - p, ",%d", ndest);

        for (int i = 0; i < ndest; ++i) {
            const PhysRegIdPtr phys = head_inst->renamedDestIdx(i);
            const RegClassType rc =
                phys ? phys->classValue() : InvalidRegClass;
            p += std::snprintf(p, end - p, ",%d,%u",
                               (int)rc,
                               (unsigned)head_inst->destRegIdx(i).index());
            if (!phys) {
                // No phys id recorded (should not happen at commit): keep
                // the column count contract, mark unknown.
                p += std::snprintf(p, end - p, ",-1,0000000000000000");
                continue;
            }
            p += std::snprintf(p, end - p, ",%u", (unsigned)phys->index());
            switch (rc) {
              // Scalar path (CHAOSPhysReg.cc:387 read pattern): RegVal.
              case IntRegClass:
              case FloatRegClass:
              case VecElemClass:
              case CCRegClass:
                p += std::snprintf(p, end - p, ",%016llx",
                    (unsigned long long)
                        (uint64_t)o3cpu->physRegFile().getReg(phys));
                break;
              // Vector blob path (CHAOSPhysReg.cc:336 read pattern): read
              // the WHOLE phys register, FNV-1a-64 fold to 16 hex digits.
              // VecReg width from vecRegBytes() (regfile.hh:183);
              // VecPred/Mat from the phys reg's own RegClass::regBytes().
              case VecRegClass:
              case VecPredRegClass:
              case MatRegClass: {
                size_t vbytes = (rc == VecRegClass)
                    ? o3cpu->physRegFile().vecRegBytes()
                    : phys->regClass().regBytes();
                if (vbytes < sizeof(uint64_t))
                    vbytes = sizeof(uint64_t);  // paranoia (CHAOSPhysReg)
                std::vector<uint8_t> vbuf(vbytes, 0);
                o3cpu->physRegFile().getReg(phys, vbuf.data());
                p += std::snprintf(p, end - p, ",%016llx",
                    (unsigned long long)fnv1a64(vbuf.data(), vbuf.size()));
                break;
              }
              // MiscRegClass (and anything unrecognized): misc regs are
              // fixed-mapping, NOT stored in the phys regfile —
              // PhysRegFile::getReg would panic. No value column content.
              default:
                p += std::snprintf(p, end - p, ",0000000000000000");
                break;
            }
            // Defensive: if a pathological ndest ever overflowed the staging
            // buffer, flush what we have and continue in a fresh one rather
            // than corrupting the pinned format.
            if (end - p < 64) {
                gzwrite(gz_file, buf, p - buf);
                p = buf;
            }
        }
        p += std::snprintf(p, end - p, "\n");
        gzwrite(gz_file, buf, p - buf);

        // Periodic crash-durability flush (hh: bounds loss to <FLUSH_EVERY
        // rows; per-row flush on 8.6M-row runs costs measurable wall time).
        if (++rows_since_flush >= FLUSH_EVERY) {
            gzflush(gz_file, Z_SYNC_FLUSH);
            rows_since_flush = 0;
        }
    }

} // namespace gem5
