/* LSU 负载 W7-SE 原子性探针（atomics_probe — O 系 SE 验证载体）:
   LDXR/STXR 重试环 + 数据数组消费。
   用途：W8 O 系注入器（exclusive monitor O01/O02、状态码 O03）的 SE
   定向验证负载（06-workloads r9 的 W7 Atomic-Litmus 是多核 FS 负载，
   O 系网格格全部 blocked；本探针只做注入器功能验证，不是网格格）。
   检测面设计（关键）：校验和只覆盖最终数据态，不含重试计数——
   monitor 地址（O01）/状态（O02）腐蚀 = 瞬时 reservation 失效，
   被重试环吸收 => Masked（不是伪 SDC）；只有数据面被污染才 SDC。 */
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

#define N 8
static unsigned long data[N];
static unsigned long lockvar;

int main(void)
{
    unsigned long acc = 0x9c3b7af1d52e4806UL;
    unsigned i, tries;

    /* 1. LDXR/STXR 原子加：重试环吸收瞬时 reservation 失效（O01/O02
       的预期结局 = Masked）。成功路径的数据更新才进 data[]。 */
    for (i = 0; i < 300; ++i) {
        unsigned int st;
        tries = 0;
        do {
            unsigned long tmp;
            __asm__ volatile("ldxr %0, [%1]" : "=r"(tmp) : "r"(&lockvar));
            tmp += 1;
            __asm__ volatile("stxr %w0, %1, [%2]"
                             : "=&r"(st) : "r"(tmp), "r"(&lockvar));
            ++tries;
        } while (st != 0 && tries < 1000);
        data[i % N] += lockvar;
    }

    /* 2. 临界区数据消费：读改写 data[]（模拟锁保护的数据面） */
    for (i = 0; i < N; ++i) {
        data[i] ^= (lockvar + i);
        acc = fnv(acc, data[i]);
    }
    acc = fnv(acc, lockvar);

    /* 最终数据态校验（重试计数不进 acc — 见文件头设计说明） */
    put_hex(acc);
    return 0;
}
