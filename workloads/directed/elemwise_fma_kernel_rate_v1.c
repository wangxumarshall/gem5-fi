/* elemwise_fma_kernel_rate_v1 — FSU D2 W4-rate-v1 (2026-11-02).
 *
 * W4/FMA-DotProduct 的确定性 ROI 扩展版，**不覆盖**现有短 W4
 * (workloads/directed/elemwise_fma_kernel)。
 *
 * 与原短 W4 的关系:
 *   - 同一 FP 操作: c[i] = a[i]*b[i] + d[i] (FP64), golden/check 双遍；
 *   - 同一输入 LCG 与同一 ARRAYHASH/ULP oracle 形式；
 *   - 新增编译期 REPEAT: 把 ROI 划分为 REPEAT 个 N_BASE 元素块，
 *     总元素 N = N_BASE * REPEAT；每块跑完整 golden+check 两遍，
 *     输出覆盖全部 N 个元素（不存在后续块覆盖前块结果的问题）。
 *   - 目标: countOnly 实测 eligible_total >= 1,500,000，使 F1
 *     (±50% jitter, 最大首间隔 1,500,000) 至少能到达第一次注入。
 *
 * 确定性:
 *   - 输入由固定 LCG 从 0x243F6A8885A308D3 连续生成，只依赖 N；
 *   - 数组规模、循环次数、FP 操作全部由 -DN_BASE/-DREPEAT 固定；
 *   - 无时间/环境/随机设备输入。
 *
 * 构建 (host aarch64, 与短 W4 相同):
 *   gcc -O2 -static -DN_BASE=8192 -DREPEAT=32 \
 *       -o workloads/directed/elemwise_fma_kernel_rate_v1 \
 *       workloads/directed/elemwise_fma_kernel_rate_v1.c
 *
 * 输出:
 *   W4RATEV1 N=<N> REPEAT=<REPEAT>
 *   ARRAYHASH=<64hex>
 *   ULP=<max_ulp_error>
 */
#include <unistd.h>
#include <stdint.h>
#include <string.h>

#ifndef N_BASE
#define N_BASE 8192
#endif
#ifndef REPEAT
#define REPEAT 32
#endif
#define N (N_BASE * REPEAT)

#if N_BASE <= 0 || REPEAT <= 0
#error "N_BASE and REPEAT must be positive"
#endif

static double a[N], b[N], d[N], c_golden[N], c_check[N];

static void put(const char *s){ write(1, s, strlen(s)); }
static void put_u64(uint64_t v){
    char buf[20]; int i=19; buf[i--]=0;
    if(!v) buf[i--]='0';
    while(v){ buf[i--]='0'+(v%10); v/=10; }
    write(1, buf+i+1, 18-i);
}
static void put_hex64(uint64_t v){
    char buf[16];
    for(int i=15;i>=0;--i){ unsigned x=v&0xf; buf[i]=x<10?'0'+x:'a'+x-10; v>>=4; }
    write(1,buf,16);
}

static uint64_t ulp_dist(double x, double y){
    if(x==y) return 0;
    uint64_t ux, uy;
    memcpy(&ux,&x,8); memcpy(&uy,&y,8);
    if((ux>>63)!=(uy>>63)){
        uint64_t ax=ux&0x7fffffffffffffffULL, ay=uy&0x7fffffffffffffffULL;
        return ax+ay+1;
    }
    return ux>uy ? ux-uy : uy-ux;
}

int main(void){
    put("W4RATEV1 N="); put_u64((uint64_t)N);
    put(" REPEAT="); put_u64((uint64_t)REPEAT); put("\n");

    /* deterministic inputs (same LCG/order as short W4) */
    uint64_t s=0x243F6A8885A308D3ULL;
    for(int i=0;i<N;i++){
        s=s*6364136223846793005ULL+1442695040888963407ULL;
        a[i]=(double)(s%1000)*0.001+0.5;
        b[i]=(double)((s>>17)%1000)*0.001+0.25;
        d[i]=(double)((s>>33)%1000)*0.001-0.5;
    }

    /* REPEAT deterministic ROI blocks; each block is the short-W4 geometry. */
    for(int r=0;r<REPEAT;r++){
        const int lo = r*N_BASE, hi = lo + N_BASE;
        for(int i=lo;i<hi;i++) c_golden[i]=a[i]*b[i]+d[i];
        for(int i=lo;i<hi;i++) c_check[i]=a[i]*b[i]+d[i];
    }

    /* ARRAYHASH over all N check results (same 4-lane FNV-1a form). */
    put("ARRAYHASH=");
    const unsigned char *p=(const unsigned char*)c_check;
    unsigned total=sizeof(c_check), q=(total+3)/4;
    for(int lane=0; lane<4; lane++){
        uint64_t h=1469598103934665603ULL ^ (0x9e3779b9ULL*lane);
        for(unsigned i=lane*q; i<(lane+1)*q && i<total; i++){
            h^=p[i]; h*=1099511628211ULL;
        }
        put_hex64(h);
    }
    put("\n");

    uint64_t maxulp=0;
    for(int i=0;i<N;i++){
        uint64_t u=ulp_dist(c_check[i],c_golden[i]);
        if(u>maxulp) maxulp=u;
    }
    put("ULP="); put_u64(maxulp); put("\n");
    return 0;
}
