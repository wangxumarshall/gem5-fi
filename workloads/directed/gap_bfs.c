/* LSU 负载 W9 GAP/Graph500 子集 (06-workloads r11):
   BFS/SSSP/PR, 使用固定图与结果哈希; 强调不规则地址和大 working set。
   用途：DTLB、Cache、AGU、Prefetch 注入器定向验证。SE。
   实现：确定性 CSR 图上的 BFS + SSSP + PageRank 一轮迭代。 */
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

/* 确定性图: 1024 节点, 每节点 4 条边 (CSR 格式, 不规则偏移) */
#define NV 1024
#define NE (NV*4)
static unsigned long rowptr[NV+1];
static unsigned long colidx[NE];
static unsigned long dist[NV];     /* BFS/SSSP */
static unsigned long rank[NV];     /* PageRank */
static unsigned long outdeg[NV];

int main(void)
{
    unsigned long acc = 0x9a9170eed0d15eedUL;
    unsigned i, v, u;

    /* 确定性图生成: 每节点 4 条边, 目标由 hash 决定 (不规则) */
    for (v = 0; v < NV; ++v) {
        rowptr[v] = v * 4;
        for (i = 0; i < 4; ++i) {
            unsigned long h = (v * 2654435761UL + i * 40503UL) % NV;
            colidx[v*4+i] = h;
        }
    }
    rowptr[NV] = NE;
    for (v = 0; v < NV; ++v) outdeg[v] = 4;

    /* 1. BFS from node 0 */
    for (v = 0; v < NV; ++v) dist[v] = ~0UL;
    dist[0] = 0;
    for (unsigned d = 0; d < 16; ++d) {
        for (v = 0; v < NV; ++v) {
            if (dist[v] != d) continue;
            for (i = rowptr[v]; i < rowptr[v+1]; ++i) {
                u = (unsigned)colidx[i];
                if (dist[u] > d + 1) dist[u] = d + 1;
            }
        }
    }
    for (v = 0; v < NV; v += 8) acc = fnv(acc, dist[v]);

    /* 2. SSSP (uniform weight 1 — same as BFS but with path check) */
    for (v = 0; v < NV; ++v) dist[v] = ~0UL;
    dist[0] = 0;
    for (unsigned iter = 0; iter < 16; ++iter) {
        for (v = 0; v < NV; ++v) {
            if (dist[v] == ~0UL) continue;
            for (i = rowptr[v]; i < rowptr[v+1]; ++i) {
                u = (unsigned)colidx[i];
                if (dist[v] + 1 < dist[u]) dist[u] = dist[v] + 1;
            }
        }
    }
    for (v = 0; v < NV; v += 8) acc = fnv(acc, dist[v]);

    /* 3. PageRank one iteration (damping 0.85) */
    for (v = 0; v < NV; ++v) rank[v] = 1000000UL / NV;
    for (v = 0; v < NV; ++v) {
        unsigned long contrib = rank[v] * 85 / 100 / 4;
        for (i = rowptr[v]; i < rowptr[v+1]; ++i) {
            u = (unsigned)colidx[i];
            rank[u] += contrib;
        }
    }
    for (v = 0; v < NV; v += 8) acc = fnv(acc, rank[v]);

    put_hex(acc);
    return 0;
}
