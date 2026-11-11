#include <cassert>
#include <cstdint>
#include <cstdio>
#include <fstream>
#include <initializer_list>
#include <sstream>
#include <string>
#include <vector>

#include "cpu/o3/CHAOSL1DForward/lp01_bytewise.hh"

using namespace gem5::chaos_lp01;

namespace
{

std::string
readFile(const std::string &path)
{
    std::ifstream f(path);
    assert(f.good() && "cannot open source file");
    std::ostringstream ss;
    ss << f.rdbuf();
    return ss.str();
}

bool
contains(const std::string &hay, const std::string &needle)
{
    return hay.find(needle) != std::string::npos;
}

// Slice from `begin` (inclusive) to `end` (exclusive). Keeps the format
// assertions scoped to the function that must emit the field rather than
// accepting the token anywhere in the file.
std::string
slice(const std::string &text, const std::string &begin,
      const std::string &end)
{
    const auto b = text.find(begin);
    if (b == std::string::npos)
        return {};
    const auto e = text.find(end, b);
    if (e == std::string::npos)
        return {};
    return text.substr(b, e - b);
}

// Path relative to the repository root, derived from this file's own path
// (works for both `g++ tests/test_lp01_bytewise.cc` and an absolute path).
std::string
repoFile(const char *rel)
{
    const std::string self = __FILE__;
    const auto slash = self.rfind('/');
    const std::string here = slash == std::string::npos
        ? std::string(".") : self.substr(0, slash);
    return here + "/../" + rel;
}

} // namespace

static void
checkSize(unsigned n)
{
    std::vector<uint8_t> buf(n, 0xA5);
    const std::vector<uint8_t> before = buf;
    assert(corruptByte0(buf.data(), n, 0x8));
    assert(buf[0] == (uint8_t)(before[0] ^ 0x08));
    for (unsigned i = 1; i < n; ++i)
        assert(buf[i] == before[i]);
}

int
main()
{
    // Model matrix: exactly byte 0 changes, for every size.
    for (unsigned n : {1u, 4u, 7u, 8u, 9u, 12u, 16u})
        checkSize(n);

    // Size 0 is a no-op and must not touch memory.
    uint8_t zero[1] = {0xAA};
    assert(!corruptByte0(zero, 0, 0x08));
    assert(zero[0] == 0xAA);

    // mask 0 is a no-op.
    uint8_t m0[8] = {0};
    assert(!corruptByte0(m0, 8, 0));
    for (uint8_t b : m0)
        assert(b == 0);

    // A mask with no byte-0 bit is outside the LP01 lane (review fix: do not
    // silently discard random bits 8..63).
    uint8_t hi[8] = {0};
    assert(!corruptByte0(hi, 8, 0x100));
    for (uint8_t b : hi)
        assert(b == 0);

    // Only the low byte of the mask is in the modeled lane.
    uint8_t wide[4] = {0, 0, 0, 0};
    assert(corruptByte0(wide, 4, 0x1122334455667708ULL));
    assert(wide[0] == 0x08 && wide[1] == 0 && wide[2] == 0 && wide[3] == 0);

    // Ordinal helper: skip 0 -> ordinal 1; skip 4 -> ordinal 5.
    assert(eligibleOrdinal(0, 0) == 1);
    assert(eligibleOrdinal(4, 0) == 5);

    std::printf("LP01 byte-0 payload matrix (0/1/4/7/8/9/12/16): PASS\n");

    // v3.3.2 LP01 identity: the injection must be bound to the target
    // instruction, not only to a physical address. Assert on the emission
    // code itself (scoped to the emitting function) so deleting a field
    // fails here; a re-implemented format string would not prove anything.
    const std::string fwd = readFile(
        repoFile("CHAOS/gem5/src/cpu/o3/CHAOSL1DForward/CHAOSL1DForward.cc"));
    const std::string prop = readFile(
        repoFile("CHAOS/gem5/src/cpu/o3/CHAOSPropagation/CHAOSPropagation.cc"));
    const std::string lsq = readFile(
        repoFile("CHAOS/gem5/src/cpu/o3/lsq_unit.cc"));

    // Injector log line: instruction identity + both address spaces.
    const std::string inj = slice(fwd, "CHAOSL1DForward::maybeCorrupt(",
                                  "CHAOSL1DForward::startup(");
    assert(!inj.empty());
    for (const char *f : {"pc=0x", "va=0x", "pa=0x", "dyn_inst_seq=",
                          "lq_entry_id=", "entry_generation=",
                          "request_id=", "addr_unchanged=1",
                          "size_unchanged=1"})
        assert(contains(inj, f));

    // inj_l1dfwd detail: new identity fields AND every pre-existing field.
    const std::string note = slice(
        prop, "CHAOSPropagation::noteL1DForwardInjection(",
        "CHAOSPropagation::noteL1DForwardWriteback(");
    assert(!note.empty());
    for (const char *f : {";pc=0x", ";vaddr=0x", ";dyn_inst_seq=",
                          ";lq_entry_id=", ";entry_generation=",
                          ";request_id=", ";response_id=", ";fragment_id=",
                          ";orig_data_fnv=", ";inj_data_fnv=", ";addr=0x",
                          ";execution_attempt_id=", ";replay_generation=",
                          ";wb_to_reg=", ";phys_regs=", ";mask=0x",
                          ";eligible_ordinal="})
        assert(contains(note, f));

    // Call site: the target DynInst is actually passed to the injector.
    const std::string call = slice(lsq, "chaosL1DFwd->maybeCorrupt(", ");");
    assert(!call.empty());
    assert(contains(call, "inst.get()"));

    std::printf("LP01 identity record (l1d_fwd_injections.log + inj_l1dfwd): "
                "PASS\n");
    return 0;
}
