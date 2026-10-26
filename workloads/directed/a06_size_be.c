/* LSU 负载 A06-定向 carrier（MDSPEC R4-6-A06 / 03 sheet A06 行）:
   规格 A06 的触发面 = "子字节或向量访存"；负载面 = AGU-AddrModes(W3) +
   SQ-Forward 转发探针(W5)。

   本 carrier 用**显式宽度的访存**（内联汇编，宽度不受 -O2 优化影响）覆盖：
     a) 子字节 store + 相邻字节 canary（A06-a/A06-b 的 store 侧污染面）
     b) 子字节 load（对齐/非对齐）——A06-a load 侧 widen 的候选面
     c) 同地址 store→load 转发对（SQ-Forward 探针；widen 会改变
        LSQUnit::tryToForward 的覆盖判定 -> 转发降级/replay）
     d) 向量（16B）load/store —— 规格点名的"向量访存"
     e) 字/双字 load —— 宽的固定完成宽度对照面

   软件 oracle：每步结果参与 FNV-1a 累积；canary 字节逐字节回读校验；
   行尾打印 16 进制校验和与 canary 判定（1=未污染），确定性可复现。
   检测面：注入改变 size/byte-enable 后，校验和与 canary 判定是否仍与原
   版本一致（L5 输出比对）；转发降级/replay 属 L2/L3 结构面观测。 */
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

/* ---- 显式宽度访存（宽度由构造固定，不受优化影响） ---- */
static inline void st_b(unsigned char *p, unsigned v){
    __asm__ volatile("strb %w0, [%1]" :: "r"(v), "r"(p) : "memory"); }
static inline unsigned ld_b(const unsigned char *p){
    unsigned v; __asm__ volatile("ldrb %w0, [%1]" : "=r"(v) : "r"(p) : "memory"); return v; }
static inline void st_h(unsigned char *p, unsigned v){
    __asm__ volatile("strh %w0, [%1]" :: "r"(v), "r"(p) : "memory"); }
static inline unsigned ld_h(const unsigned char *p){
    unsigned v; __asm__ volatile("ldrh %w0, [%1]" : "=r"(v) : "r"(p) : "memory"); return v; }
static inline void st_w(unsigned char *p, unsigned v){
    __asm__ volatile("str %w0, [%1]" :: "r"(v), "r"(p) : "memory"); }
static inline unsigned ld_w(const unsigned char *p){
    unsigned v; __asm__ volatile("ldr %w0, [%1]" : "=r"(v) : "r"(p) : "memory"); return v; }
static inline void st_x(unsigned char *p, unsigned long v){
    __asm__ volatile("str %0, [%1]" :: "r"(v), "r"(p) : "memory"); }
static inline unsigned long ld_x(const unsigned char *p){
    unsigned long v; __asm__ volatile("ldr %0, [%1]" : "=r"(v) : "r"(p) : "memory"); return v; }
static inline void st_q(unsigned char *p, unsigned long lo, unsigned long hi){
    __asm__ volatile("fmov d0, %0\n\tfmov d1, %1\n\tstr q0, [%2]"
                     :: "r"(lo), "r"(hi), "r"(p) : "memory", "v0", "v1"); }
static inline void ld_q(const unsigned char *p, unsigned long *lo, unsigned long *hi){
    __asm__ volatile("ldr q0, [%2]\n\tfmov %0, d0\n\tfmov %1, d1"
                     : "=&r"(*lo), "=&r"(*hi) : "r"(p) : "memory", "v0"); }

#define NB 64
#define CANARY 0xA5u
static unsigned char buf[NB]  __attribute__((aligned(64)));  /* byte canary */
static unsigned char hw[NB]   __attribute__((aligned(64)));  /* 2B canary */
static unsigned char fwd[NB]  __attribute__((aligned(64)));  /* byte forwarding */
static unsigned char pair[NB] __attribute__((aligned(64)));  /* 8B forwarding */
static unsigned char wide[NB] __attribute__((aligned(64)));  /* vector region */

int main(void)
{
    unsigned long acc = 0x41406f6b6b6fUL;   /* deterministic seed */
    unsigned i;
    unsigned canary_ok = 1;

    /* 0) 初始化：canary 填充（每字节可辨） */
    for (i = 0; i < NB; ++i) {
        buf[i] = CANARY; hw[i] = CANARY;
        fwd[i] = 0; pair[i] = 0; wide[i] = 0;
    }

    /* 1) 子字节 store + 相邻 canary：只应改目标字节 */
    for (i = 0; i < 16; ++i) st_b(buf + i * 4 + 1, (unsigned)(0x11u + i));
    for (i = 0; i < 16; ++i) {
        if (ld_b(buf + i * 4) != CANARY)     canary_ok = 0;   /* store 污染面 */
        if (ld_b(buf + i * 4 + 2) != CANARY) canary_ok = 0;
        acc = fnv(acc, ld_b(buf + i * 4 + 1));
    }
    /* 1b) 半字 store（2B，步长 8 —— 每个 store 前后各留 6 个 canary 字节，
           store 越宽/byte-enable 越界都会踩到它们） */
    for (i = 0; i < 8; ++i) {
        st_h(hw + i * 8, (unsigned)(0x2000u + i));
        acc = fnv(acc, ld_h(hw + i * 8));
    }
    for (i = 0; i < 8; ++i) {
        unsigned j;
        for (j = 2; j < 8; ++j)
            if (ld_b(hw + i * 8 + j) != CANARY) canary_ok = 0;
    }

    /* 2) 同地址 store→load 转发对（SQ-Forward 探针；size 被改宽时
          tryToForward 的 store_has_upper_limit 失效 -> full-coverage 分支
          不可达 -> 该 load 降级/被 replay 直到 store drain） */
    for (i = 0; i < 16; ++i) {
        unsigned v = (unsigned)(0x40u + i);
        st_b(fwd + i * 4, v);                 /* 1B store ... */
        acc = fnv(acc, ld_b(fwd + i * 4));    /* ... 同地址 1B load（可转发） */
    }
    for (i = 0; i < 8; ++i) {
        unsigned long v = 0x1000UL + i;
        st_x(pair + i * 8, v);                 /* 8B store ... */
        acc = fnv(acc, ld_x(pair + i * 8));    /* ... 同地址 8B load */
    }

    /* 3) 非对齐子字节 load（跨行偏移面） */
    for (i = 0; i < 12; ++i) acc = fnv(acc, ld_b(buf + i * 3 + 1));
    for (i = 0; i < 6; ++i)  acc = fnv(acc, ld_w(buf + i * 8 + 4));

    /* 4) 字/双字（固定完成宽度对照面） */
    for (i = 0; i < 16; ++i) acc = fnv(acc, ld_w(buf + i * 4));
    for (i = 0; i < 8; ++i)  acc = fnv(acc, ld_x(wide + i * 8));

    /* 5) 向量（16B）load/store —— 规格点名的"向量访存" */
    {
        unsigned long lo = 0x0123456789abcdefUL, hi = 0xfedcba9876543210UL;
        unsigned long rlo = 0, rhi = 0;
        st_q(wide + 0, lo, hi);
        ld_q(wide + 0, &rlo, &rhi);
        acc = fnv(acc, rlo); acc = fnv(acc, rhi);
        st_q(wide + 16, ~lo, ~hi);
        ld_q(wide + 16, &rlo, &rhi);
        acc = fnv(acc, rlo); acc = fnv(acc, rhi);
    }

    /* 6) 汇总：校验和 + canary 判定（确定性；两条独立输出） */
    put_hex(acc);
    write(1, "canary=", 7);
    put_hex((unsigned long)canary_ok);
    return 0;
}
