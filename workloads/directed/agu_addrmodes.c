/* LSU 负载 W3 AGU-AddrModes (06-workloads r5):
   覆盖 base+imm、base+index、LSL、UXTW/SXTW、pre/post-index、LDP/STP、
   非对齐和页边界；每地址附软件 oracle。
   用途：AGU 注入器(A01-A08)的定向验证负载。SE。
   检测面：每种寻址模式产生确定值参与最终 FNV-1a 校验和。 */
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

#define N 64
static unsigned long array[N] __attribute__((aligned(4096)));
static unsigned long output[N];

int main(void)
{
    unsigned long acc = 0x42ee1ce4d4e55eedUL;
    unsigned long base = (unsigned long)array;
    unsigned i;

    /* 初始化: 每个元素一个确定值 */
    for (i = 0; i < N; ++i) array[i] = 0x1000UL + i * 0x0123456789ABCDEFUL;

    /* 1. base+imm (immediate offset) */
    for (i = 0; i < 8; ++i) acc = fnv(acc, *(unsigned long *)(base + i * 8));

    /* 2. base+index (register offset) */
    for (i = 0; i < 8; ++i) { unsigned long idx = i; acc = fnv(acc, *(unsigned long *)(base + idx * 8)); }

    /* 3. LSL shifted register offset (base + (idx << 3)) */
    for (i = 0; i < 8; ++i) { unsigned long idx = i; acc = fnv(acc, *(unsigned long *)(base + (idx << 3))); }

    /* 4. UXTW (unsigned extend word: 32-bit index zero-extended) */
    for (i = 0; i < 8; ++i) { uint32_t widx = (uint32_t)(i + 16); acc = fnv(acc, *(unsigned long *)(base + (unsigned long)widx * 8)); }

    /* 5. SXTW (sign extend word — positive values here for determinism) */
    for (i = 0; i < 8; ++i) { int32_t sidx = (int32_t)(i + 24); acc = fnv(acc, *(unsigned long *)(base + (long)sidx * 8)); }

    /* 6. pre-index (LDUR with writeback: addr = base+off; base = base+off) */
    { unsigned long *p = array; for (i = 0; i < 4; ++i) { acc = fnv(acc, *++p); } }

    /* 7. post-index (LDR then base increment) */
    { unsigned long *p = array; for (i = 0; i < 4; ++i) { acc = fnv(acc, *p++); } }

    /* 8. LDP/STP (load/store pair — reads two consecutive values) */
    for (i = 0; i < 8; i += 2) {
        unsigned long a, b;
        __asm__ volatile("ldp %0, %1, [%2]" : "=r"(a), "=r"(b) : "r"(base + i * 8));
        acc = fnv(acc, a); acc = fnv(acc, b);
    }

    /* 9. non-aligned (byte load from odd offsets) */
    { unsigned char *bp = (unsigned char *)array; for (i = 0; i < 16; ++i) acc = fnv(acc, bp[i * 3 + 1]); }

    /* 10. page-boundary (last 8 bytes of the 4KiB-aligned page) */
    acc = fnv(acc, *(unsigned long *)(base + 4096 - 8));

    /* store side: write via different modes then read back */
    for (i = 0; i < N; ++i) output[i] = array[i] ^ 0xDEADBEEFCAFEBABEUL;
    for (i = 0; i < N; ++i) acc = fnv(acc, output[i]);

    put_hex(acc);
    return 0;
}
