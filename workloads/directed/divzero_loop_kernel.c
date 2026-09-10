/* divzero_loop_kernel — v1.1 Phase 10 patch 2c.
 * One REAL integer division-by-zero. The operands are loaded from a
 * volatile so the compiler cannot fold the UB. Without exc_suppress the
 * workload traps (Crash/DUE); with the fault cleared at retire-head the
 * run completes and prints a checksum (the DUE->SDC conversion probe).
 * Static AArch64, no libc. */
#include <unistd.h>
#include <stdint.h>
#include <string.h>

static volatile uint64_t vnum = 0x243F6A8885A308D3ULL;
static volatile uint64_t vden = 0;

static void put(const char *s){ write(1, s, strlen(s)); }
static void put_hex64(uint64_t v){
    char buf[16];
    for(int i=15;i>=0;--i){ unsigned x=v&0xf; buf[i]=x<10?'0'+x:'a'+x-10; v>>=4; }
    write(1,buf,16);
}

int main(void){
    uint64_t num = vnum, den = vden;
    uint64_t q = num / den;        /* THE trap site (volatile loads — real) */
    put("FINAL=");
    put_hex64(q);
    put("\n");
    return 0;
}
