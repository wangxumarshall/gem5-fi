/* LSU 定向负载 ssit_dual_set（R4-6-S10 平台修复后的 S10 carrier）:
   定向构造 **多个互异 store-set 并发活跃** 的访存形态，用于给 S10
   （StoreSet SSIT-ID 换值）提供合法的替换候选。

   为什么需要它（机理，引用源码条件）:
     S10 的注入点唯有 StoreSet::violation 的"全新 store-set 赋值臂"
     （CHAOS/gem5/src/cpu/o3/store_set.cc：`if (!valid_load_SSID &&
     !valid_store_SSID)`，chaosS10SsidSubst 调用点在其中）。该臂的候选集 =
     SSIT 现存**其他**活跃 SSID（排除真值 calcSSID(load_PC)，
     calcSSID(PC) = (PC ^ (PC>>10)) % LFSTSize，LFSTSize=1024）。而 SSIT
     只被 violation() 写，所以：
       - 任何 run 的**第一条** training event 必然进该臂且表为空 →
         不可能 eligible（这是结构性的，不是负载缺陷）；
       - 该臂对同一 (store_PC, load_PC) 对是一次性的（训练过之后该对走
         合并臂，钩子不再被调用）；
       - 因此 eligible>0 的充要条件是：**存在第二条「首次训练」的别名对**，
         且其 calcSSID(load_PC) 与表里已有的活跃 SSID 不同。
     本负载把 sq_forward §5 的"数据晚到 store + 紧随同址 load"模式复制到
     NSITES 个**互不相同的 PC 对**上，并且在同一个主循环里**交替执行**
     （同 idx 轮内 site_0..site_7 依次发出，8 个 store-set 同时在 LSQ 窗口
     内活跃），使 arm-1 事件 >= 2 成为结构性结果、并让候选集在第二条及
     以后的 arm-1 事件上非空。

   与 alias_sites（R4-5.7b 载体）的区别:
     alias_sites 是"每站各自跑完 48 轮"的**串行**站点集合；本载体改为
     "每个 idx 轮内 8 站交替"的**交织**形态，使 ≥2 个 store-set 在**同一
     时间窗口内**并发活跃（SSIT 中同时存在多条有效条目），并显式保留
     loop-carried 数据依赖（store 的数据来自上一次调用返回的 load 值）来
     维持"store 数据晚到 / load 地址早到"的违例检出面。

   期望（主 agent 用 census 实测判定，不在此处声称）:
     CHAOS_LSU_S10_FORK: arm1_events >= 2, max_live_ssids >= 2,
     arm1_cand_ok >= 1, eligible >= 1, injected >= 1（F5 cell）。
     —— 前置条件：StoreSet 平台修复已落地（否则本实例 SSIT 恒空，
        arm1_cand_empty == arm1_events 依旧）。

   检测面：S10-SDIT 预测器状态（PC 键）；其他数据面模型不读此负载的语义，
   只读其访存流。SE。 */
#include <stdint.h>
#include <unistd.h>

static void put_hex(unsigned long v)
{
    char buf[16];
    for (int i = 15; i >= 0; --i) {
        unsigned d = (unsigned)(v & 0xf);
        buf[i] = (char)(d < 10 ? '0' + d : 'a' + d - 10);
        v >>= 4;
    }
    write(1, buf, 16);
    write(1, "\n", 1);
}

static inline unsigned long fnv(unsigned long acc, unsigned long v)
{
    acc ^= v;
    acc *= 0x100000001b3UL;
    return acc;
}

/* 8 个独立站点：每站独占一行 volatile 数组（地址不同、代码不同）。
   volatile 禁止编译器把 store→load 折成寄存器传递，保证每个 idx 都真的
   发出一条 store 与紧随其后、同地址的一条 load —— 这正是 gem5 O3 LSQ
   checkViolations 检出 memory-order violation 的形态。数据依赖由调用者
   携带（carry 来自上一次调用的返回值）→ store 数据晚到；load 地址
   (arena[ID] + idx) 早已就绪 → load 先执行读到旧值、store 写回时检出违例。 */
#define NSITES 8
#define ROWLEN 64
static volatile unsigned long arena[NSITES][ROWLEN];

#define SITE(ID)                                                             \
__attribute__((noinline)) static unsigned long site_##ID(unsigned long prev,  \
                                                          unsigned idx)       \
{                                                                            \
    arena[ID][idx] = prev + 0x9E3779B97F4A7C15UL + 0x1000193UL * (ID);        \
    return arena[ID][idx];                                                    \
}

SITE(0) SITE(1) SITE(2) SITE(3)
SITE(4) SITE(5) SITE(6) SITE(7)

int main(void)
{
    unsigned long acc = 0x243f6a8885a308d3UL;
    unsigned long carry[NSITES];

    for (unsigned s = 0; s < NSITES; ++s)
        carry[s] = 0x9E3779B97F4A7C15UL + 0x1000193UL * s;

    /* 两轮：第一轮让 8 个站点各自完成首次训练（每站最多产出一次 arm-1
       training event —— 第一条必然候选为空、第二条起表里已有互异活跃
       SSID），第二轮把访存流拉长（已训练的对不再产生 violation，属预期）。
       同一 idx 轮内 8 站交替 → ≥2 个 store-set 同时活跃。 */
    for (unsigned round = 0; round < 2; ++round) {
        for (unsigned idx = 0; idx < ROWLEN; ++idx) {
            carry[0] = site_0(carry[0], idx); acc = fnv(acc, carry[0]);
            carry[1] = site_1(carry[1], idx); acc = fnv(acc, carry[1]);
            carry[2] = site_2(carry[2], idx); acc = fnv(acc, carry[2]);
            carry[3] = site_3(carry[3], idx); acc = fnv(acc, carry[3]);
            carry[4] = site_4(carry[4], idx); acc = fnv(acc, carry[4]);
            carry[5] = site_5(carry[5], idx); acc = fnv(acc, carry[5]);
            carry[6] = site_6(carry[6], idx); acc = fnv(acc, carry[6]);
            carry[7] = site_7(carry[7], idx); acc = fnv(acc, carry[7]);
        }
    }

    put_hex(acc);
    return 0;
}
