/* LSU 负载 W12 SQLite-Speedtest1 (06-workloads r13):
   SQLite speedtest1 代理 — B-tree 页遍历、读改写事务、integrity_check。
   用途：AGU、LQ、SQ、L1D-Cache 注入器定向验证。SE。
   实现：B-tree 页式存储模拟（不是真实 SQLite, 但覆盖同一访问模式）。

   [LSU][MDSPEC][R6-L-UNIT] 同源有界重复载体（chaos_repeat.h）：
   argv[1]=reps（缺省 1）。reps==1 时输出与旧二进制逐字节一致（只有末行
   裸 16hex checksum）；reps>1 时每趟打印 `ITER:<n>:<16hex>`，末行仍是裸
   checksum。每趟都重置页池，保证每趟执行完全相同的第 1–8 步操作序列，
   因此每个 ITER 行都等于冻结 golden（33f836327a416d35）。 */
#include <unistd.h>
#include <stdint.h>
#include <string.h>
#include "chaos_repeat.h"

static void put_hex(unsigned long v){
    char buf[16];
    for (int i=15;i>=0;--i){ unsigned d = v & 0xf; buf[i]=d<10?'0'+d:'a'+d-10; v>>=4; }
    write(1,buf,16); write(1,"\n",1);
}
static inline unsigned long fnv(unsigned long a, unsigned long v){
    a ^= v; a *= 0x100000001b3UL; return a;
}

#define PAGE_SZ 4096
#define NPAGES 256          /* 1MiB page pool = 32× L1D */
#define ORDER 32            /* B-tree order (keys per page) */
#define NKEYS (NPAGES * ORDER)

/* Simulated B-tree page pool (exercises page-level read/write patterns) */
static unsigned long pages[NPAGES][ORDER];
static unsigned long meta[NPAGES];  /* page metadata (like SQLite header) */

static unsigned long probe_once(void)
{
    unsigned long acc = 0x5a1711523d1ce5eeUL;
    unsigned i, j;

    /* Every iteration is a fresh database: reset the page pool so repeats
       execute the identical operation sequence and yield the same checksum. */
    memset(pages, 0, sizeof pages);
    memset(meta, 0, sizeof meta);

    /* 1. Initialize: "CREATE TABLE" — bulk sequential insert */
    for (i = 0; i < NPAGES; ++i) {
        meta[i] = i;
        for (j = 0; j < ORDER; ++j)
            pages[i][j] = i * ORDER + j;
    }

    /* 2. "SELECT" — point queries (random page access, like B-tree traversal) */
    for (i = 0; i < 512; ++i) {
        unsigned pg = (i * 73 + 17) % NPAGES;
        unsigned slot = (i * 31) % ORDER;
        acc = fnv(acc, pages[pg][slot]);
    }

    /* 3. "INSERT" — scattered writes (page read-modify-write) */
    for (i = 0; i < 256; ++i) {
        unsigned pg = (i * 137) % NPAGES;
        pages[pg][ORDER-1] = 0xD00D0000 + i;
        acc = fnv(acc, pages[pg][ORDER-1]);
    }

    /* 4. "UPDATE" — range scan + modify (sequential page walk) */
    for (i = 0; i < NPAGES / 2; ++i) {
        for (j = 0; j < ORDER; ++j)
            pages[i][j] += 1;
        acc = fnv(acc, pages[i][0]);
    }

    /* 5. "integrity_check" — full scan (sequential read all pages) */
    { unsigned long checksum = 0;
      for (i = 0; i < NPAGES; ++i) {
          for (j = 0; j < ORDER; j += 4)
              checksum ^= pages[i][j];
          checksum = checksum * 31 + meta[i];
      }
      acc = fnv(acc, checksum); }

    /* 6. "DELETE" — punch holes (scattered page invalidation) */
    for (i = 0; i < 64; ++i) {
        unsigned pg = (i * 199) % NPAGES;
        memset(pages[pg], 0, ORDER * sizeof(unsigned long));
    }

    /* 7. "VACUUM" — compact (move all non-empty pages to front) */
    { unsigned write_pg = 0;
      for (i = 0; i < NPAGES; ++i) {
          if (meta[i] != 0 || pages[i][0] != 0) {
              if (i != write_pg) {
                  memcpy(pages[write_pg], pages[i], ORDER * sizeof(unsigned long));
                  meta[write_pg] = meta[i];
              }
              ++write_pg;
          }
      }
      acc = fnv(acc, write_pg); }

    /* 8. Final scan of compacted data */
    for (i = 0; i < NPAGES; i += 4)
        acc = fnv(acc, pages[i][0]);

    return acc;
}

int main(int argc, char **argv)
{
    int reps = chaos_repeat_count(argc, argv);
    unsigned long acc = 0;
    for (int r = 0; r < reps; ++r) {
        acc = probe_once();
        if (reps > 1)
            chaos_emit_iter(r, acc);
    }
    put_hex(acc);
    return 0;
}
