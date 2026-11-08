#ifndef __CPU_O3_FW05_RULES_HH__
#define __CPU_O3_FW05_RULES_HH__

#include <cstdint>
#include <cstring>

namespace gem5
{
namespace chaos_fw05
{

// FW05-ELIG-v1: single wrong-source forwarding. The load is younger than
// both stores; the true source is the youngest matching store selected by
// gem5's full-coverage forwarding; the alternative is an older, DIFFERENT
// store that fully covers the load range and holds different bytes. A
// partial alternative is rejected (no multi-store splice). `alt_offset` is
// the byte offset inside the alternative store at which the load starts.
struct Candidate
{
    uint64_t seq = 0;
    uint64_t addr = 0;
    unsigned size = 0;
    const uint8_t *data = nullptr;
};

inline bool
isEligible(uint64_t load_seq, uint64_t load_addr, unsigned load_size,
           const Candidate &true_src, const Candidate &alt_src,
           unsigned &alt_offset)
{
    alt_offset = 0;
    if (!true_src.data || !alt_src.data)
        return false;
    if (load_size == 0 || true_src.size < load_size)
        return false;
    if (true_src.seq == alt_src.seq)
        return false;                       // two different dynamic stores
    if (alt_src.seq >= true_src.seq)
        return false;                       // alternative must be older
    if (load_seq <= true_src.seq || load_seq <= alt_src.seq)
        return false;                       // load must be younger
    if (true_src.addr > load_addr
            || true_src.addr + true_src.size < load_addr + load_size)
        return false;                       // true source must cover the load
    if (alt_src.addr > load_addr)
        return false;                       // must cover the load's first byte
    const uint64_t off = load_addr - alt_src.addr;
    if (off + load_size > alt_src.size)
        return false;                       // no multi-store splice
    alt_offset = (unsigned)off;
    const uint8_t *t = true_src.data + (load_addr - true_src.addr);
    const uint8_t *a = alt_src.data + off;
    return std::memcmp(t, a, load_size) != 0;
}

} // namespace chaos_fw05
} // namespace gem5

#endif // __CPU_O3_FW05_RULES_HH__
