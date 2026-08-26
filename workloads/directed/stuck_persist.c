/* G2 persistence kernel. The accumulator is pinned to x19 via register asm
   and a pure-asm write storm (no C optimizations can spill it). Stuck_at_one
   armed on x19's phys reg must force the stuck bit on every write; the final
   read reflects that. Print FINAL=<16-hex>. */
#include <unistd.h>
#include <stdint.h>

static void put_hex(unsigned long v){ char b[16]; for(int i=15;i>=0;--i){unsigned d=v&0xf;b[i]=d<10?'0'+d:'a'+d-10;v>>=4;} write(2,b,16); write(2,"\n",1);}

int main(void){
    register unsigned long x asm("x19") = 0;
    unsigned long i;
    for (i=0;i<5000000UL;++i){
        /* storm writes + xor, all on x19 */
        __asm__ volatile (
            "mov %0, %1\n"
            "eor %0, %0, %2\n"
            : "+r"(x) : "r"(i), "r"(0xdeadbeefUL) : );
    }
    put_hex(x);
    return 0;
}
