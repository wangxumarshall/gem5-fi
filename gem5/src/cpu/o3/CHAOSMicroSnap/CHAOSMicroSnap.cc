// CHAOSMicroSnap.cc — W2.4 read-only L1 µarchitecture shadow snapshot
// sampler. Four-piece SimObject family pattern (template: CHAOSProbe/;
// setter-attach pattern: CHAOSCommitTrace/). See CHAOSMicroSnap.hh for the
// contract and the pinned CSV line format. Nothing here mutates CPU state:
// the only writes are to the snapshot file itself.

#include "cpu/o3/CHAOSMicroSnap/CHAOSMicroSnap.hh"

#include <cstring>
#include <sstream>
#include <string>

#include "cpu/o3/cpu.hh"          // o3::CPU: o3Commit()/o3ROB()/o3IEW()/
                                  //  physFreeList()/frontRenameMap()
#include "cpu/o3/dyn_inst.hh"     // DynInst (head_inst null guard)
#include "cpu/o3/inst_queue.hh"   // InstructionQueue::getCount
#include "cpu/o3/rename_map.hh"   // UnifiedRenameMap::map() (W2.4 accessor)
#include "cpu/o3/rob.hh"          // ROB::countInsts/readHeadInst/readTailInst
#include "cpu/reg_class.hh"       // RegClassType: Int/Float/VecRegClass
#include "params/CHAOSMicroSnap.hh"
#include "sim/cur_tick.hh"        // curTick()
#include "sim/sim_exit.hh"        // registerExitCallback

namespace gem5
{

    CHAOSMicroSnap::CHAOSMicroSnap(const CHAOSMicroSnapParams &p)
        : SimObject(p),
          cpu(p.cpu),
          snap_every(p.snapEvery),
          trace_file(p.traceFile),
          write_log(p.writeLog)
    {
        if (snap_every == 0) {
            // A period of 0 would fire on every commit (x % 0 is UB) — clamp
            // to 1 and say so (CHAOSProbe sampleEvery=0 precedent).
            warn("CHAOSMicroSnap: snapEvery=0 clamped to 1.\n");
            snap_every = 1;
        }
        if (write_log) {
            // Raw zlib gzFile at simout.resolve(trace_file) — deliberately
            // NOT simout.create's gz streambuf: that path only gzwrite()s,
            // and zlib holds data internally until gzclose, so an aborted
            // run (the rename-inconsistency Crash class) loses the whole
            // file (measured 0 bytes in the directed W2.4 verification).
            // Every row below is followed by gzflush(Z_SYNC_FLUSH) — the
            // per-snapshot cost is one flush per snapEvery commits.
            const std::string path = simout.resolve(trace_file);
            gz_file = gzopen(path.c_str(), "wb");
            if (!gz_file)
                panic("CHAOSMicroSnap: Could not open snapshot file %s",
                      path);
            const char *header =
                "# micro_snap v1: snap_seq,commit_seq,tick,rob_occ,iq_occ,"
                "fl_int,fl_fp,fl_vec,rob_head,rob_tail,"
                "rat_int_hash,rat_fp_hash,rat_vec_hash,"
                "rat_int_table,rat_fp_table,rat_vec_table\n";
            const int hlen = (int)strlen(header);
            if (gzwrite(gz_file, header, hlen) != hlen)
                panic("CHAOSMicroSnap: header write failed on %s", path);
            gzflush(gz_file, Z_SYNC_FLUSH);

            // Normal-exit trailer: gzclose writes the gzip trailer. This
            // MUST happen in an exit callback, not the destructor — gem5's
            // exit path does not reliably run SimObject destructors
            // (measured: normal-run file came out trailer-less when only
            // the destructor closed it). CHAOSProbe.cc exit-callback
            // precedent ("always fires, unlike the destructor"). Aborted
            // runs never get here: they keep the Z_SYNC_FLUSH-ed truncated
            // stream, which micro_diff salvages.
            registerExitCallback([this]() {
                if (gz_file) {
                    gzclose(gz_file);
                    gz_file = nullptr;
                }
            });
        }
    }

    CHAOSMicroSnap::~CHAOSMicroSnap()
    {
        // Backstop only (exit callback above is the primary closer). On an
        // aborted run neither runs — that is fine, every row was already
        // flushed; the file is then a decodable truncated stream and
        // tools/micro_diff.py salvages its prefix.
        if (gz_file) {
            gzclose(gz_file);
            gz_file = nullptr;
        }
    }

    void
    CHAOSMicroSnap::startup()
    {
        SimObject::startup();
        auto *o3 = dynamic_cast<o3::CPU *>(cpu);
        if (!o3) {
            warn("CHAOSMicroSnap: cpu is not an O3CPU; sampler disabled.\n");
            return;
        }
        o3cpu = o3;
        // W2.1 setter pattern: the commit-stage pointer the commit.cc hook
        // tests. From here on every committed instruction calls maybeSample().
        o3cpu->o3Commit().setChaosMicroSnap(this);
    }

    void
    CHAOSMicroSnap::maybeSample(ThreadID tid, o3::DynInst *head_inst)
    {
        if (!o3cpu || !head_inst)
            return;

        // Self-held commit counter always follows the commit stream (write_log
        // only gates the row writing), same discipline as the W2.1 seq.
        ++commit_count;
        if (commit_count % snap_every != 0)
            return;
        if (!write_log || !gz_file)
            return;

        // ---- one READ-ONLY snapshot (no CPU state is written) ----

        // Occupancies: the exact CHAOSProbe.cc:92-125 read pattern. The head
        // instruction is still IN the ROB here (retireHead runs after the
        // hook), so rob_occ includes it — deterministic, comparable across
        // runs at the same commit_seq.
        const uint64_t rob_occ = (uint64_t)o3cpu->o3ROB().countInsts();
        const uint64_t iq_occ =
            (uint64_t)o3cpu->o3IEW().instQueue.getCount(0);
        const uint64_t fl_int =
            (uint64_t)o3cpu->physFreeList().numFreeRegs(IntRegClass);
        const uint64_t fl_fp =
            (uint64_t)o3cpu->physFreeList().numFreeRegs(FloatRegClass);
        const uint64_t fl_vec =
            (uint64_t)o3cpu->physFreeList().numFreeRegs(VecRegClass);

        // ROB head/tail seqNums (rob.hh:136/153). Null guard: readTailInst
        // may in principle hand back an empty slot; print 0 then.
        // DynInstPtr is an o3-namespace typedef.
        const o3::DynInstPtr head = o3cpu->o3ROB().readHeadInst(tid);
        const o3::DynInstPtr tail = o3cpu->o3ROB().readTailInst(tid);
        const uint64_t rob_head = head ? (uint64_t)head->seqNum : 0;
        const uint64_t rob_tail = tail ? (uint64_t)tail->seqNum : 0;

        // RAT: the FRONT rename map of this thread, per class (see .hh for
        // why front, not commit). UnifiedRenameMap::map() is the W2.4
        // minimal accessor; SimpleRenameMap's public iterators walk the
        // arch->phys table in arch-index order.
        auto snapRat = [&](RegClassType rc, uint64_t &hash,
                           std::ostringstream &table) {
            static const uint64_t FNV_OFFSET = 14695981039346656037ULL;
            static const uint64_t FNV_PRIME = 1099511628211ULL;
            hash = FNV_OFFSET;
            const o3::SimpleRenameMap &m =
                o3cpu->frontRenameMap()[tid].map(rc);
            uint64_t i = 0;
            for (auto it = m.begin(); it != m.end(); ++it, ++i) {
                // Null entry sentinel = 65535 (the W2.1 invalid-phys
                // convention). Entries are initialized to valid phys ids at
                // CPU init, so this is pure paranoia.
                const uint64_t phys =
                    (*it) ? (uint64_t)(*it)->index() : 65535ULL;
                hash = (hash ^ i) * FNV_PRIME;
                hash = (hash ^ phys) * FNV_PRIME;
                // ';' (not ',') between entries: the row is comma-separated
                // CSV and the consumer enforces an exact 16-column contract,
                // so entry lists inside a column must not use the CSV
                // separator.
                if (i)
                    table << ';';
                table << i << ':' << phys;
            }
        };

        uint64_t h_int = 0, h_fp = 0, h_vec = 0;
        std::ostringstream t_int, t_fp, t_vec;
        snapRat(IntRegClass, h_int, t_int);
        snapRat(FloatRegClass, h_fp, t_fp);
        snapRat(VecRegClass, h_vec, t_vec);

        std::ostringstream row;
        row << snap_seq << ',' << commit_count << ',' << curTick() << ','
            << rob_occ << ',' << iq_occ << ','
            << fl_int << ',' << fl_fp << ',' << fl_vec << ','
            << rob_head << ',' << rob_tail << ','
            << h_int << ',' << h_fp << ',' << h_vec << ','
            << t_int.str() << ',' << t_fp.str() << ',' << t_vec.str() << '\n';
        const std::string s = row.str();
        if (gzwrite(gz_file, s.data(), (unsigned)s.size())
                != (int)s.size())
            panic("CHAOSMicroSnap: snapshot row write failed (seq %llu)",
                  (unsigned long long)snap_seq);
        // Crash-durability flush (see .hh): one gzflush per snapshot.
        gzflush(gz_file, Z_SYNC_FLUSH);
        ++snap_seq;
    }

} // namespace gem5
