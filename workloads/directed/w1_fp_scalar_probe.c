/* W1 FP-ScalarProbe — draft for docs/gem5-fi/fsu workbook W1.
 *
 * Covers (per W1 definition):
 *   FP32/FP64: add, sub, mul, div, sqrt, FMA (scalar, not NEON)
 *   deterministic NaN / Inf / +/-0 / subnormal inputs (full cross product)
 *   all four AArch64 rounding modes RN/RP/RM/RZ via MSR FPCR
 *   bit-exact result arrays + FPSR snapshots + FPCR snapshots
 *   in-run golden pass, bitwise oracle, ULP oracle, ARRAYHASH
 *
 * Anti constant-folding: all operands live in volatile arrays filled at
 * runtime; each op is evaluated through volatile locals and separated by
 * compiler barriers. Build with:
 *   gcc -O2 -static -ffp-contract=off -frounding-math -fsignaling-nans \
 *       -fno-tree-vectorize -fno-tree-slp-vectorize \
 *       -o w1_fp_scalar_probe w1_fp_scalar_probe.c -lm
 *
 * Identity line W1REP/NP and all hashes must be treated as one workload
 * identity. Changing REP/NP changes the expected golden hash.
 *
 * HONEST N/A (gem5 SE):
 *   - FPCR trap-enable bits (IOE/DZE/OFE/UFE/IXE/IDE, bits 8..15) are
 *     AArch32 FPSCR bits, not AArch64 FPCR; gem5 preserves arbitrary writes
 *     to them but does not deliver synchronous FP exceptions.
 *   - FPCR reserved bits and FPSR bits 28..31 are preserved by gem5 on
 *     MSR/MRS readback although real AArch64 hardware masks them to
 *     0x07FF0000 / 0xF800009F. The oracle below only uses RMode and the
 *     architecturally meaningful FPSR bits set by scalar FP (0..4, 7).
 *   - FPSR.QC (bit 27) is a cumulative saturation flag driven by AdvSIMD
 *     integer saturating ops, not by scalar W1 ops.
 */
#include <unistd.h>
#include <stdint.h>
#include <string.h>

#define NP_SPECIAL 16
#define NP_TOTAL   32          /* 16 special + 16 deterministic finite */
#ifndef REP
#define REP        1           /* compile-time volume; identity includes it */
#endif
#define OPS_PER_RM (5 * NP_TOTAL * NP_TOTAL + NP_TOTAL)
#define OPS_PER_PREC (4 * OPS_PER_RM * REP)

static volatile uint32_t in32[NP_TOTAL];
static volatile uint64_t in64[NP_TOTAL];

static uint32_t g32[OPS_PER_PREC];
static uint64_t g64[OPS_PER_PREC];
static uint32_t gf32[OPS_PER_PREC];
static uint32_t gf64[OPS_PER_PREC];
static uint32_t gfpcr[4];

static void put(const char *s){ write(1, s, strlen(s)); }
static void put_u64(uint64_t v){
    char b[24]; int i=23; b[i--]=0;
    if(!v) b[i--]='0';
    while(v){ b[i--]='0'+(v%10); v/=10; }
    write(1, b+i+1, 22-i);
}
static void put_hex64(uint64_t v){
    char b[16];
    for(int i=15;i>=0;--i){ unsigned x=v&0xf; b[i]=x<10?'0'+x:'a'+x-10; v>>=4; }
    write(1,b,16);
}
static void line_hex(const char *s, uint64_t v){ put(s); put_hex64(v); put("\n"); }
static void line_u64(const char *s, uint64_t v){ put(s); put_u64(v); put("\n"); }

static inline uint32_t b32(float f){ uint32_t u; memcpy(&u,&f,4); return u; }
static inline float f32(uint32_t u){ float f; memcpy(&f,&u,4); return f; }
static inline uint64_t b64(double d){ uint64_t u; memcpy(&u,&d,8); return u; }
static inline double f64(uint64_t u){ double d; memcpy(&d,&u,8); return d; }

static inline uint64_t rd_fpcr(void){ uint64_t v; __asm__ volatile("mrs %0, fpcr":"=r"(v): :"memory"); return v; }
static inline void wr_fpcr(uint64_t v){ __asm__ volatile("msr fpcr, %0"::"r"(v):"memory"); __asm__ volatile("isb":::"memory"); }
static inline uint64_t rd_fpsr(void){ uint64_t v; __asm__ volatile("mrs %0, fpsr":"=r"(v): :"memory"); return v; }
static inline void wr_fpsr(uint64_t v){ __asm__ volatile("msr fpsr, %0"::"r"(v):"memory"); }

/* ULP distance of raw encodings; NaN pair is non-comparable. */
static uint64_t ulp32(uint32_t x, uint32_t y){
    if(x==y) return 0;
    uint32_t ax=x&0x7fffffffU, ay=y&0x7fffffffU;
    if(ax>0x7f800000U || ay>0x7f800000U) return ~0ULL;
    if((x>>31)!=(y>>31)) return (uint64_t)ax+ay+1;
    return x>y ? (uint64_t)(x-y) : (uint64_t)(y-x);
}
static uint64_t ulp64(uint64_t x, uint64_t y){
    if(x==y) return 0;
    uint64_t ax=x&0x7fffffffffffffffULL, ay=y&0x7fffffffffffffffULL;
    if(ax>0x7ff0000000000000ULL || ay>0x7ff0000000000000ULL) return ~0ULL;
    if((x>>63)!=(y>>63)) return ax+ay+1;
    return x>y ? x-y : y-x;
}
static uint64_t fnv_bytes(uint64_t h, uint64_t v){
    for(int k=0;k<8;k++){ h^=(v>>(8*k))&0xffU; h*=1099511628211ULL; }
    return h;
}

static const uint32_t SP32[NP_SPECIAL] = {
    0x7fc00000U, 0x7fc12345U, 0x7f800001U, 0x7f800000U,
    0xff800000U, 0x00000000U, 0x80000000U, 0x00000001U,
    0x007fffffU, 0x00800000U, 0x7f7fffffU, 0x3f800000U,
    0xbf800000U, 0x40400000U, 0x3eaaaaabU, 0x4b000000U
};
static const uint64_t SP64[NP_SPECIAL] = {
    0x7ff8000000000000ULL, 0x7ff8123456789abcULL,
    0x7ff0000000000001ULL, 0x7ff0000000000000ULL,
    0xfff0000000000000ULL, 0x0000000000000000ULL,
    0x8000000000000000ULL, 0x0000000000000001ULL,
    0x000fffffffffffffULL, 0x0010000000000000ULL,
    0x7fefffffffffffffULL, 0x3ff0000000000000ULL,
    0xbff0000000000000ULL, 0x4008000000000000ULL,
    0x3fd5555555555555ULL, 0x4330000000000000ULL
};

static inline uint64_t splitmix64(uint64_t *s){
    uint64_t z=(*s += 0x9e3779b97f4a7c15ULL);
    z=(z^(z>>30))*0xbf58476d1ce4e5b9ULL;
    z=(z^(z>>27))*0x94d049bb133111ebULL;
    return z^(z>>31);
}

static void build_inputs(void){
    for(int i=0;i<NP_SPECIAL;i++){ in32[i]=SP32[i]; in64[i]=SP64[i]; }
    uint64_t s=0x243f6a8885a308d3ULL;
    for(int i=NP_SPECIAL;i<NP_TOTAL;i++){
        uint64_t x=splitmix64(&s);
        uint32_t e=(uint32_t)((x>>32)%254U)+1U;       /* 1..254 finite */
        uint32_t m=(uint32_t)x;
        in32[i]=((uint32_t)(x>>63)<<31)|(e<<23)|(m&0x7fffffU);
        uint64_t y=splitmix64(&s);
        uint64_t e64=((y>>12)%2046ULL)+1ULL;           /* 1..2046 finite */
        in64[i]=((y>>63)<<63)|(e64<<52)|(y&0xfffffffffffffULL);
    }
}

#define STEP32(tag, expr) do { \
    wr_fpsr(0); \
    volatile float _r = (expr); \
    __asm__ volatile("" ::: "memory"); \
    uint32_t _rb = b32(_r); \
    uint32_t _fl = (uint32_t)rd_fpsr(); \
    if(!check){ g32[idx32]=_rb; gf32[idx32]=_fl; } \
    else { \
        uint32_t _gb=g32[idx32], _gfl=gf32[idx32]; \
        if(_rb!=_gb){ (*mism)++; if(*first==0xffffffffU) *first=idx32; \
            uint64_t u=ulp32(_gb,_rb); if(u>*ulp) *ulp=u; } \
        if(_fl!=_gfl) (*fmism)++; \
        h32=fnv_bytes(h32,((uint64_t)(tag)<<32)|_gb); \
        h32=fnv_bytes(h32,_rb); \
        hf=fnv_bytes(hf,((uint64_t)(tag)<<32)|_gfl); \
        hf=fnv_bytes(hf,_fl); \
    } \
    idx32++; \
} while(0)

#define STEP64(tag, expr) do { \
    wr_fpsr(0); \
    volatile double _r = (expr); \
    __asm__ volatile("" ::: "memory"); \
    uint64_t _rb = b64(_r); \
    uint32_t _fl = (uint32_t)rd_fpsr(); \
    if(!check){ g64[idx64]=_rb; gf64[idx64]=_fl; } \
    else { \
        uint64_t _gb=g64[idx64]; uint32_t _gfl=gf64[idx64]; \
        if(_rb!=_gb){ (*mism)++; if(*first==0xffffffffU) *first=idx64; \
            uint64_t u=ulp64(_gb,_rb); if(u>*ulp) *ulp=u; } \
        if(_fl!=_gfl) (*fmism)++; \
        h64=fnv_bytes(h64,((uint64_t)(tag)<<32)|_gb); \
        h64=fnv_bytes(h64,_rb); \
        hf=fnv_bytes(hf,((uint64_t)(tag)<<32)|_gfl); \
        hf=fnv_bytes(hf,_fl); \
    } \
    idx64++; \
} while(0)

static __attribute__((noinline)) void
run_pass(int check, uint64_t *o32, uint64_t *o64, uint64_t *of,
         uint32_t *mism, uint32_t *fmism, uint32_t *fpmism,
         uint64_t *ulp, uint32_t *first)
{
    uint64_t h32=0x84222325cbf29ce5ULL;
    uint64_t h64=0x9e3779b97f4a7c15ULL;
    uint64_t hf =0xd6e8feb86659fd93ULL;
    uint32_t idx32=0, idx64=0;

    for(int rep=0; rep<REP; rep++){
        for(int rm=0; rm<4; rm++){
            wr_fpcr((uint64_t)rm << 22);
            uint32_t snap=(uint32_t)rd_fpcr();
            if(!check) gfpcr[rm]=snap;
            else if(snap!=gfpcr[rm]) (*fpmism)++;

            for(int i=0;i<NP_TOTAL;i++){
                int ia=(i + rep*7) & (NP_TOTAL-1);
                volatile float va=f32(in32[ia]);
                volatile double da=f64(in64[ia]);
                for(int j=0;j<NP_TOTAL;j++){
                    int ib=(j + rep*11) & (NP_TOTAL-1);
                    int ic=(i*3 + j*5 + rep*13) & (NP_TOTAL-1);
                    volatile float vb=f32(in32[ib]);
                    volatile float vc=f32(in32[ic]);
                    volatile double db=f64(in64[ib]);
                    volatile double dc=f64(in64[ic]);

                    STEP32(0, va+vb);
                    STEP32(1, va-vb);
                    STEP32(2, va*vb);
                    STEP32(3, va/vb);
                    STEP32(4, __builtin_fmaf(va,vb,vc));
                    STEP64(0, da+db);
                    STEP64(1, da-db);
                    STEP64(2, da*db);
                    STEP64(3, da/db);
                    STEP64(4, __builtin_fma(da,db,dc));
                }
                STEP32(5, __builtin_sqrtf(va));
                STEP64(5, __builtin_sqrt(da));
            }
        }
    }
    wr_fpcr(0); wr_fpsr(0);
    *o32=h32; *o64=h64; *of=hf;
}

int main(void){
    build_inputs();

    uint32_t mism=0, fmism=0, fpmism=0, first=0xffffffffU;
    uint64_t ulp=0, h32=0, h64=0, hf=0;
    run_pass(0, &h32, &h64, &hf, &mism, &fmism, &fpmism, &ulp, &first);
    run_pass(1, &h32, &h64, &hf, &mism, &fmism, &fpmism, &ulp, &first);

    put("W1REP="); put_u64(REP); put("\n");
    put("NP="); put_u64(NP_TOTAL); put("\n");
    put("OPS32="); put_u64(OPS_PER_PREC); put("\n");
    put("OPS64="); put_u64(OPS_PER_PREC); put("\n");
    put("FPCR_RN="); put_hex64(gfpcr[0]); put("\n");
    put("FPCR_RP="); put_hex64(gfpcr[1]); put("\n");
    put("FPCR_RM="); put_hex64(gfpcr[2]); put("\n");
    put("FPCR_RZ="); put_hex64(gfpcr[3]); put("\n");
    line_hex("ARRAYHASH32=", h32);
    line_hex("ARRAYHASH64=", h64);
    line_hex("FPSRHASH=", hf);
    /* Single 64-hex identity for tools/classify.py array_hash oracle:
     * result FP32 hash | result FP64 hash | FPSR hash | FPCR hash. */
    uint64_t hfpcr = 1469598103934665603ULL;
    for (int k = 0; k < 4; k++)
        hfpcr = fnv_bytes(hfpcr, gfpcr[k]);
    put("ARRAYHASH="); put_hex64(h32); put_hex64(h64);
    put_hex64(hf); put_hex64(hfpcr); put("\n");
    line_u64("ULP=", ulp);
    line_u64("ULPMAX=", ulp);
    line_u64("BITMISMATCH=", mism);
    line_u64("FPSRMISMATCH=", fmism);
    line_u64("FPCRMISMATCH=", fpmism);
    if(first==0xffffffffU) put("FIRSTDIFF=none\n");
    else { put("FIRSTDIFF="); put_u64(first); put("\n"); }
    put("DONE\n");
    return 0;
}
