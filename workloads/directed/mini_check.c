/* LSU 负载 W0 MiniCheck (docs/gem5-fi/lsu/06-workloads.md r2):
     短数组校验和、guard page、指针链、load/store round-trip；
     每次运行产生确定 golden output（16-char hex checksum, FNV-1a 折叠）。
   用途：全部 LSU 单元的注入器冒烟与传播调试（09 W9 滚动首项）。
   结构（对注入传播的检测面）:
     1. 短数组校验和 —— 数据面腐蚀 -> SDC（checksum 变化）。
     2. 指针链（数组内置换链）—— 地址/索引腐蚀 -> 错节点或越界 -> SDC/Crash。
     3. load/store round-trip —— store 数据面 + load 读回（volatile 强制真读）。
     4. guard page —— 链表合法 next 指针全留在 page1；被腐蚀的指针落在
        PROT_NONE page2 上解引用 -> SIGSEGV（native）/ SE fault（gem5）。
        无故障运行永不触碰 page2（golden 安全）。 */
#include <unistd.h>
#include <stdint.h>
#include <sys/mman.h>

static void put_hex(unsigned long v){
    char buf[16];
    for (int i=15;i>=0;--i){ unsigned d = v & 0xf; buf[i]=d<10?'0'+d:'a'+d-10; v>>=4; }
    write(1,buf,16); write(1,"\n",1);
}

#define N 64
static unsigned long data[N];

/* FNV-1a 折叠：任何单元素/指针偏差都会改变 checksum。 */
static inline unsigned long fnv(unsigned long acc, unsigned long v){
    acc ^= v; acc *= 0x100000001b3UL; return acc;
}

struct node { unsigned long val; unsigned long next_off; };

int main(void){
    unsigned long acc = 0xcbf29ce484222325UL;
    unsigned i;

    /* 1. 短数组校验和 */
    for (i = 0; i < N; ++i) data[i] = 0x1000UL + (unsigned long)i * 0x0101010101010101UL;
    for (i = 0; i < N; ++i) acc = fnv(acc, data[i]);

    /* 2. 指针链（置换链：节点 i 的下一跳 = (i*7+3)%N，无自环前遍历 N 步） */
    for (i = 0; i < N; ++i) data[i] = (data[i] & ~0xffUL) | (unsigned long)((i * 7 + 3) % N);
    { unsigned cur = 0;
      for (i = 0; i < N; ++i){ acc = fnv(acc, data[cur]); cur = (unsigned)(data[cur] & 0xffUL); } }

    /* 3. load/store round-trip（volatile 读强制真实 load） */
    for (i = 0; i < N; ++i) data[i] ^= 0xa5a5a5a5a5a5a5a5UL;
    { volatile unsigned long *vd = data;
      for (i = 0; i < N; ++i) acc = fnv(acc, vd[i]); }

    /* 4. guard page：page1 放链表，page2 PROT_NONE；合法 next 全在 page1 内 */
    { char *pages = mmap(0, 8192, PROT_READ|PROT_WRITE,
                         MAP_PRIVATE|MAP_ANONYMOUS, -1, 0);
      if (pages == MAP_FAILED){ put_hex(acc ^ 0xdeadUL); return 1; }
      if (mprotect(pages + 4096, 4096, PROT_NONE) != 0){ put_hex(acc ^ 0xbeefUL); return 1; }
      struct node *nl = (struct node *)pages;            /* page1: 4096/16 = 256 槽 */
      const unsigned NN = 64;
      for (i = 0; i < NN; ++i){
          nl[i].val      = 0x2000UL + (unsigned long)i * 0x0707070707070707UL;
          nl[i].next_off = (unsigned long)(((i * 11 + 5) % NN) * sizeof(struct node));
      }
      unsigned long off = 0;
      for (i = 0; i < NN; ++i){
          struct node *p = (struct node *)(pages + off);   /* 腐蚀的 next_off 会落到 page2 -> fault */
          acc = fnv(acc, p->val);
          off = p->next_off;
      } }

    put_hex(acc);
    return 0;
}
