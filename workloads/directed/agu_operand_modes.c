/* LSU 负载 R6-A3 A05-a/b/c 定向微载体 (06-workloads):
   用**真实 AArch64 标量 register-offset** 载具覆盖 A05 操作数子模型：

     ld_shift0(base, byte_off) : ldr x, [Xn, Xm]          (option=LSL, S=0)
     ld_lsl3 (base, idx)       : ldr x, [Xn, Xm, lsl #3]  (option=LSL, S=1)
     ld_sxtw (base, w_idx)     : ldr x, [Xn, Wm, sxtw]    (option=SXTW)

   三个探针都是 noinline + volatile asm，-O2 不会强度削减成指针步进；
   每次调用读取 array 中一个确定元素并累加进 FNV-1a 校验和，因此
   A05-c（shift 替换）在对象内读到不同元素时校验和必变（SDC 通道），
   A05-a（base/index 互换）产生 (base<<3) 级野地址；A05-b 用**负 W 索引**
   （SXTW 正确 EA = array+8，在对象内；换成 UXTW 后 = array+4GiB 级野地址）
   ——二者都是翻译失败 / guest SEGV 通道，与 DIAG-B §3.2/3.3 的诚实
   预期一致（不是 in-object SDC）。

   选择规则（canary 固定 warmup=0/span=1，首个合格事件即注入）：
     a05_shift      : 首个合格事件 = ld_shift0(k=1)  -> EA 变到 array+64
     a05_base_index : 首个合格事件 = ld_lsl3(k=0)   -> EA 变到 (base<<3)
     a05_extend     : 唯一合格事件 = 末尾 bit31=1 的 ld_sxtw
   SE。 */
#include <stdint.h>
#include <unistd.h>

static unsigned long array[64] __attribute__((aligned(64)));
static volatile unsigned long sink;

static inline unsigned long fnv(unsigned long acc, unsigned long v)
{
    acc ^= v;
    acc *= 0x100000001b3UL;
    return acc;
}

__attribute__((noinline))
static unsigned long ld_shift0(const unsigned long *base, unsigned long byte_off)
{
    unsigned long v;
    __asm__ __volatile__("ldr %0, [%1, %2]"
                         : "=&r"(v) : "r"(base), "r"(byte_off) : "memory");
    return v;
}

__attribute__((noinline))
static unsigned long ld_lsl3(const unsigned long *base, unsigned long idx)
{
    unsigned long v;
    __asm__ __volatile__("ldr %0, [%1, %2, lsl #3]"
                         : "=&r"(v) : "r"(base), "r"(idx) : "memory");
    return v;
}

__attribute__((noinline))
static unsigned long ld_sxtw(const unsigned long *base, int32_t w_idx)
{
    unsigned long v;
    __asm__ __volatile__("ldr %0, [%1, %w2, sxtw]"
                         : "=&r"(v) : "r"(base), "r"(w_idx) : "memory");
    return v;
}

static void put_hex(unsigned long v)
{
    char buf[17];
    for (int i = 15; i >= 0; --i) {
        unsigned d = v & 0xf;
        buf[i] = d < 10 ? '0' + d : 'a' + d - 10;
        v >>= 4;
    }
    buf[16] = '\n';
    write(1, buf, 17);
}

int main(void)
{
    unsigned long acc = 0xcbf29ce484222325UL;

    for (unsigned long i = 0; i < 64; ++i)
        array[i] = 0x1000UL + i * 0x0123456789abcdefUL;

    /* 每种形态先各走一遍（同一循环，顺序固定）：
       shift0 -> lsl3 -> sxtw。三种形态的合格事件互不重叠。 */
    for (unsigned long k = 0; k < 8; ++k) {
        acc = fnv(acc, ld_shift0(array, k * 8));
        acc = fnv(acc, ld_lsl3(array, k));
        acc = fnv(acc, ld_sxtw(array, (int32_t)(k + 16)));
    }

    /* A05-b 载具：W-index bit31 = 1（w = -8）。
       SXTW: EA = (array+16) - 8 = array+8（对象内，正确执行可达）；
       UXTW: EA = (array+16) + 0xfffffff8（约 +4GiB，对象外 ->
             真实 arch_translation_fault / guest SEGV）。 */
    acc = fnv(acc, ld_sxtw(array + 2, -8));

    sink = acc;
    put_hex(acc);
    return 0;
}
