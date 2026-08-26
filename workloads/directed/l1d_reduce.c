/* P0 BM-L1D kernel: array reduction with memory-resident data.
   A checksum over a large array forces L1D traffic. An L1D byte-flip
   on a live array byte has a chance to corrupt the reduction and
   propagate to the final checksum. Print 16-hex checksum. */
#include <unistd.h>
#include <stdint.h>
#include <string.h>

static void put_hex(unsigned long v){ char b[16]; for(int i=15;i>=0;--i){unsigned d=v&0xf;b[i]=d<10?'0'+d:'a'+d-10;v>>=4;} write(1,b,16); write(1,"\n",1);}

#define N 65536
static unsigned long data[N];  /* in BSS -> 512KiB, exceeds L1D -> L1D thrashing */

int main(void){
    /* fill with a pseudo-random but deterministic pattern */
    unsigned long s = 0x1234567890abcdefUL;
    for (int i=0;i<N;i++){ s ^= s<<13; s ^= s>>7; s ^= s<<17; data[i]=s; }
    /* reduction: xor + add, memory-traffic heavy */
    unsigned long acc=0;
    for (int i=0;i<N;i++){ acc += data[i]; acc ^= data[i] >> (i & 31); }
    put_hex(acc);
    return 0;
}
