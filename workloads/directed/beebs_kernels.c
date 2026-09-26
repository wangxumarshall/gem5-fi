/* LSU 负载 W2 BEEBS-DelayAVF (06-workloads r4):
   md5、libbubblesort、libstrstr、matmult、libfibcall
   用途：LSQ 与预取器的时延故障规律对照。SE。
   实现：五种 kernel 的简化确定性版本，每个产生确定值参与最终校验和。 */
#include <unistd.h>
#include <stdint.h>
#include <string.h>

static void put_hex(unsigned long v){
    char buf[16];
    for (int i=15;i>=0;--i){ unsigned d = v & 0xf; buf[i]=d<10?'0'+d:'a'+d-10; v>>=4; }
    write(1,buf,16); write(1,"\n",1);
}
static inline unsigned long fnv(unsigned long a, unsigned long v){
    a ^= v; a *= 0x100000001b3UL; return a;
}

#define N 256
static unsigned long data[N];
static char strbuf[1024];

/* md5-style hash (simplified FNV-based, deterministic) */
static unsigned long simple_hash(const unsigned char *p, int len){
    unsigned long h = 0xcbf29ce484222325UL;
    for (int i = 0; i < len; ++i) { h ^= p[i]; h *= 0x100000001b3UL; }
    return h;
}

/* bubble sort */
static void bubble_sort(unsigned long *a, int n){
    for (int i = 0; i < n - 1; ++i)
        for (int j = 0; j < n - 1 - i; ++j)
            if (a[j] > a[j+1]) { unsigned long t = a[j]; a[j] = a[j+1]; a[j+1] = t; }
}

/* strstr-like search */
static int find_pattern(const char *hay, int haylen, const char *needle, int nlen){
    for (int i = 0; i <= haylen - nlen; ++i)
        if (memcmp(hay + i, needle, nlen) == 0) return i;
    return -1;
}

/* matrix multiply (N×N, but keep small for determinism) */
#define M 16
static unsigned long matA[M*M], matB[M*M], matC[M*M];

/* fibonacci */
static unsigned long fib(int n){
    if (n < 2) return n;
    unsigned long a = 0, b = 1;
    for (int i = 2; i <= n; ++i) { unsigned long c = a + b; a = b; b = c; }
    return b;
}

int main(void)
{
    unsigned long acc = 0xbee5552d1ce4a7f0UL;
    int i, j, k;

    /* 1. md5-style hash of a pattern buffer */
    for (i = 0; i < 256; ++i) strbuf[i] = (char)(i * 7 + 3);
    acc = fnv(acc, simple_hash((unsigned char *)strbuf, 256));

    /* 2. bubble sort (store + load intensive) */
    for (i = 0; i < N; ++i) data[i] = (unsigned long)((i * 73 + 41) % N);
    bubble_sort(data, N);
    for (i = 0; i < N; i += 16) acc = fnv(acc, data[i]);

    /* 3. strstr pattern search */
    for (i = 0; i < 256; ++i) strbuf[i] = (char)('a' + (i % 26));
    memcpy(strbuf + 100, "xyze", 4);
    acc = fnv(acc, find_pattern(strbuf, 256, "xyze", 4));

    /* 4. matrix multiply (load-heavy: row-major access) */
    for (i = 0; i < M; ++i)
        for (j = 0; j < M; ++j) { matA[i*M+j] = i + j; matB[i*M+j] = i - j; }
    for (i = 0; i < M; ++i)
        for (j = 0; j < M; ++j) {
            unsigned long s = 0;
            for (k = 0; k < M; ++k) s += matA[i*M+k] * matB[k*M+j];
            matC[i*M+j] = s;
        }
    for (i = 0; i < M; i += 4) acc = fnv(acc, matC[i*M + i]);

    /* 5. fibonacci (pure compute, tests LQ address generation) */
    acc = fnv(acc, fib(90));

    put_hex(acc);
    return 0;
}
