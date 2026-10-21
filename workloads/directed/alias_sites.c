/* LSU 负载 W11 alias_sites（R4-5.7b S10 carrier）:
   定向构造 **大量互不相同的 store→load 别名对**，用于给 S10（StoreSet
   SSIT-ID 换值）提供合法的替换候选。

   为什么需要它（机理，引用源码条件）：
     S10 的注入点唯有 StoreSet::violation 的"全新 store-set 赋值臂"
     （CHAOS/gem5/src/cpu/o3/store_set.cc 的
      `if (!valid_load_SSID && !valid_store_SSID)`，chaosS10SsidSubst 调
      用点在其中）。该臂的候选集 = SSIT 现存**其他**活跃 SSID（排除真值
      calcSSID(load_PC)）。而 SSIT 只被 violation() 写，所以：
       - 任何 run 的第一条 training event 必然进该臂且表为空 → 不可能
         eligible（census 实测 attempted=4/5、eligible=0 的直接谓词）；
       - 该臂对同一 (store_PC, load_PC) 对是一次性的（训练过之后该对走
         合并臂，钩子不再被调用）；
       - 因此 eligible>0 的充要条件是：**存在第二条「首次训练」的别名对**，
         且其 calcSSID(load_PC) 与表里已有的活跃 SSID 不同。
     既有 W5/W9 负载（sq_forward 4 次 / gap_bfs 5 次 memory-order
     violation，见 iew.memOrderViolationEvents）远远不够；本负载把
     sq_forward §5 的"数据晚到 store + 紧随同址 load"模式复制到 12 个
     **互不相同的 PC 对**（12 个 noinline 函数），使 arm-1 事件 ≥ 2 次
     成为结构性结果。

   期望（主 agent 用 census 实测判定，不在此处声称）：
     CHAOS_LSU_S10_FORK: arm1_events >= 2, max_live_ssids >= 2,
     arm1_cand_ok >= 1, eligible >= 1, injected >= 1（F5 cell）。

   检测面：S10-SDIT 预测器状态（PC 键）；S09/S01 等数据面模型不读此负载的
   语义，只读其访存流。SE。 */
#include <unistd.h>
#include <stdint.h>

static void put_hex(unsigned long v){
    char buf[16];
    for (int i=15;i>=0;--i){ unsigned d = v & 0xf; buf[i]=d<10?'0'+d:'a'+d-10; v>>=4; }
    write(1,buf,16); write(1,"\n",1);
}

static inline unsigned long fnv(unsigned long acc, unsigned long v){
    acc ^= v; acc *= 0x100000001b3UL; return acc;
}

/* 12 个独立别名站点，每站独占一行 volatile 数组（地址不同、代码不同）。
   volatile：禁止编译器把 store→load 折成寄存器传递，保证每次迭代都真的
   发出一条 store 与紧随其后、同地址的一条 load —— 这正是 gem5 O3 LSQ
   checkViolations 检出 memory-order violation 的形态（store 的数据依赖上
   一次迭代的 load 结果 → 数据晚到；load 地址已就绪 → 先执行读到旧值 →
   store 写回时检出违例）。 */
#define NSITES 12
#define NROWS  48
static volatile unsigned long arena[NSITES][NROWS];

#define SITE(ID)                                                              \
__attribute__((noinline)) static void site_##ID(unsigned long *acc) {         \
    unsigned long prev = 0x9E3779B97F4A7C15UL + 0x1000193UL * (ID);           \
    for (unsigned i = 0; i < NROWS; ++i) {                                    \
        arena[ID][i] = prev + i;   /* 数据晚到的 store（依赖 prev 链） */     \
        prev = arena[ID][i];       /* 紧随其后、同地址的 load（别名） */      \
        *acc = fnv(*acc, prev);                                               \
    }                                                                         \
}

SITE(0)  SITE(1)  SITE(2)  SITE(3)
SITE(4)  SITE(5)  SITE(6)  SITE(7)
SITE(8)  SITE(9)  SITE(10) SITE(11)

int main(void)
{
    unsigned long acc = 0x243f6a8885a308d3UL;

    /* 两轮：第一轮让 12 个站点各自完成首次训练（每个站点最多产出一次
       arm-1 training event），第二轮把访存流拉长（各站点已被预测依赖时
       不再产生 violation，属预期）。 */
    for (int round = 0; round < 2; ++round) {
        site_0(&acc);  site_1(&acc);  site_2(&acc);  site_3(&acc);
        site_4(&acc);  site_5(&acc);  site_6(&acc);  site_7(&acc);
        site_8(&acc);  site_9(&acc);  site_10(&acc); site_11(&acc);
    }

    put_hex(acc);
    return 0;
}
