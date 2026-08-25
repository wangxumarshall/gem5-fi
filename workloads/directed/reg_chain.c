/* Directed GPR micro-bench: long integer dependency chain on X0-X7.
   Designed so a transient bit-flip on a live arch register in the ROI
   has a measurable chance to propagate to the final checksum.
   Prints a 16-char hex checksum of the final value. */
#include <unistd.h>
#include <stdint.h>

static void put_hex(unsigned long v){
    char buf[16];
    for (int i=15;i>=0;--i){ unsigned d = v & 0xf; buf[i] = d<10? '0'+d : 'a'+d-10; v>>=4; }
    write(1,buf,16); write(1,"\n",1);
}

int main(void){
    unsigned long acc = 0x1234567890abcdefUL;
    /* ROI: a long, sequential dependency chain the compiler cannot fold. */
    for (volatile unsigned long i=0; i<2000000UL; ++i){
        acc ^= (acc << 13);
        acc ^= (acc >> 7);
        acc ^= (acc << 17);
        acc += 0x9e3779b97f4a7c15UL;
    }
    put_hex(acc);
    return 0;
}
