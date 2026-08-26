/* P0 BM-L1I kernel: a tight loop over a fixed 32-bit A64 instruction
   sequence in a known PC range. The L1I data-array bit flip can mutate
   an instruction's opcode/Rn/Rm/Rd/immediate/condition field.
   Golden = a deterministic checksum of the loop iterations + a control
   marker. Print 16-hex. */
#include <unistd.h>
#include <stdint.h>

static void put_hex(unsigned long v){ char b[16]; for(int i=15;i>=0;--i){unsigned d=v&0xf;b[i]=d<10?'0'+d:'a'+d-10;v>>=4;} write(1,b,16); write(1,"\n",1);}

int main(void){
    unsigned long acc = 0xfeedfaceUL;
    /* a fixed-instruction-shape loop the compiler renders as a tight,
       L1I-resident basic block. ~5M iters. */
    for (volatile unsigned long i=0; i<5000000UL; ++i){
        acc += i;            /* ADD */
        acc ^= (acc << 7);   /* EOR/LSL */
        acc += 0x9e3779b9UL; /* ADD imm */
    }
    put_hex(acc);
    return 0;
}
