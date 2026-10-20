/* LSU 定向负载 cache_mshr_refetch (R4-3, mshr_alloc 载体):
   "故障行被驱逐后再取回" 的可重复场景。
   L1D (B0, lsu_proxy): 32KiB / 2-way / 64B line → 256 组，组索引周期 16KiB。
   region = 48KiB = 每组恰好 3 行 → 顺序全扫时每行都 miss（2-way LRU：
   本行到达前组内已有 2 个更新行）→ 每一轮 (round) 内 region 的每一行都
   经历 驱逐 → demand miss → MSHR alloc（同行后续 7 个 8B load 合并
   merge）→ fill → free。CHAOSCache 注入落在任一 region 行上时，该行
   必然在 ≤1 轮内再次 miss（20M tick 注册有效窗口 >> 单轮时长）→
   mshr_alloc 可复现（跨 seed）。
   每轮先做一次栈帧读写（noinline + volatile）：故障落在栈行的 seed 也
   在 ≤1 轮内重取。region 之外的启动数据行在 round 0 全组驱逐后不再被
   访问 → 注入时刻不再是 valid、不会被抽中。
   golden = fnv-1a checksum of all read-back values。读出的值只进 checksum
   （绝不当地址/指针用）→ 数据损坏不会 crash，链可走到 chain_end。
   用途：C 系列（CHAOSCache on L1D）mshr_alloc/merge/fill/free 节点
   补证。SE。 */
#include <unistd.h>
#include <stdint.h>

static void put_hex(unsigned long v){
    char buf[16];
    for (int i=15;i>=0;--i){ unsigned d = v & 0xf; buf[i]=d<10?'0'+d:'a'+d-10; v>>=4; }
    write(1,buf,16); write(1,"\n",1);
}
static inline unsigned long fnv(unsigned long a, unsigned long v){
    a ^= v; a *= 0x100000001b3UL; return a;
}

#define L1D (32*1024)
#define REGION (L1D*3/2)        /* 48KiB = 3 lines/set → 全扫纯 miss */
#define WORDS (REGION/8)        /* 6144 个 8B 字 = 768 行 */
#define ROUNDS 16

static unsigned long region[WORDS];

/* 每轮一次的栈帧读写：栈行也被 region 扫驱逐 → 每轮重取（覆盖
   "故障落在栈行"的 seed）。volatile 防止 -O2 把访问优化掉。 */
static unsigned long __attribute__((noinline)) stack_round(unsigned long seed)
{
    volatile unsigned long s[16];       /* 128B = 2 行 */
    unsigned long a = seed;
    int i;
    for (i = 0; i < 16; ++i) s[i] = seed + i;
    for (i = 0; i < 16; ++i) a = fnv(a, s[i]);
    return a;
}

int main(void)
{
    unsigned long acc = 0x5eed1a05e57a2ed3UL;
    unsigned i, r;

    /* warm-up: 填满 region（全部行 valid；此后 round 0 把启动杂项行
       从所有组里驱逐出去） */
    for (i = 0; i < WORDS; ++i) region[i] = i * 2654435761UL + 1;

    /* rounds: 每轮每行 驱逐→重取（miss→alloc+merge→fill→free） */
    for (r = 0; r < ROUNDS; ++r) {
        acc = stack_round(acc + r);
        for (i = 0; i < WORDS; ++i) acc = fnv(acc, region[i]);
    }

    put_hex(acc);
    return 0;
}
