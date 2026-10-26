#ifndef __ARCH_ARM_CHAOS_TLB_STUCK_HH__
#define __ARCH_ARM_CHAOS_TLB_STUCK_HH__

// [MDSPEC][R6-F5-NOEFFECT] 永久卡死掩码语义（armtlb LOOKUP 路径，单元格
// T03-F5-W4）。
//
// 规范原文（docs/gem5-fi/lsu/gem5-fi-LSU单元故障注入方案-07-展开执行矩阵.md:60）：
//   "…在 warm-up 后固定一个物理 bit、lane 或控制位置 … 之后每次读出/写入都
//    施加同一掩码直到运行结束。若某次事件的正确值本来就等于卡死值，该次不增加
//    activated。"
// 频率档规范（…方案.md:149）：
//   "warm-up 后第一个 eligible event 起持续到运行结束；每次运行仅选一个 bit/字段"
//
// 本头文件把两条规则编码为无依赖的纯函数，供 CHAOSArmTLB.cc（gem5 构建内）与
// 独立单测（tests/chaos_tlb_stuck_test.cc）共享 —— 与 chaos_tlb_pfn.hh 同一模式，
// 保证"被测的规则就是跑的规则"。

#include <cstdint>

namespace gem5
{
namespace chaos_tlb
{

enum class StuckKind : uint8_t { StuckAtZero, StuckAtOne, BitFlip };

struct StuckOutcome
{
    uint64_t new_pfn = 0;    // 施加掩码后的帧号
    bool effective = false;  // new_pfn != old_pfn ⇒ 真实有效注入
};

inline StuckOutcome
applyStuckMask(uint64_t mask, uint64_t old_pfn, StuckKind kind)
{
    uint64_t np = old_pfn;
    switch (kind) {
      case StuckKind::StuckAtZero: np = old_pfn & ~mask; break;
      case StuckKind::StuckAtOne:  np = old_pfn |  mask; break;
      case StuckKind::BitFlip:     np = old_pfn ^  mask; break;
    }
    return {np, np != old_pfn};
}

// F5 永久卡死：每次运行仅一个掩码（07:60）。latched 是本次运行的固定掩码
// （0 表示尚未抽取）。显式 --tlb_fault_mask 优先于抽取，且同样被 latch ——
// 两条路径下运行内掩码都是固定的。
inline uint64_t
latchStuckMask(uint64_t user_mask, uint64_t &latched, uint64_t draw)
{
    if (latched != 0) return latched;
    latched = user_mask ? user_mask : draw;
    return latched;
}

// F5 永久卡死：把抽取限制在该帧**实际存在**的物理位内。
// 规范 07:60 要求"固定一个**物理** bit"；uniform 取 0..63 会以约 72% 的概率
// 落在物理地址宽度之外（实测 pfn≈19 位、PA≈2^30），使整个运行恒为 no_effect
// —— 这是真机实测 610MB 日志里 0 条 effective 行的直接原因。
inline uint64_t
latchStuckMaskForFrame(uint64_t user_mask, uint64_t &latched, uint64_t draw,
                       uint64_t old_pfn)
{
    if (latched != 0) return latched;
    if (user_mask) { latched = user_mask; return latched; }
    const unsigned width = old_pfn
        ? (64u - static_cast<unsigned>(__builtin_clzll(old_pfn))) : 1u;
    latched = 1ULL << (draw % width);
    return latched;
}

} // namespace chaos_tlb
} // namespace gem5

#endif // __ARCH_ARM_CHAOS_TLB_STUCK_HH__
