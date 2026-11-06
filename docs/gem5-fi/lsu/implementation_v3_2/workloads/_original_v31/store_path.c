#include <stdio.h>
#include <stdint.h>
#include <string.h>
static uint64_t fnv1a(const void *p,size_t n){const uint8_t*b=p;uint64_t h=1469598103934665603ULL;for(size_t i=0;i<n;i++){h^=b[i];h*=1099511628211ULL;}return h;}
int main(void){static uint8_t a[32768]; memset(a,0,sizeof a);
 for(int i=0;i<4096;i++){a[i]=(uint8_t)i; *(uint16_t*)(a+4096+i*2)=(uint16_t)(i*3); *(uint32_t*)(a+8192+i*4)=(uint32_t)i*7u; *(uint64_t*)(a+16384+i*4)=0x0123456789abcdefULL^(uint64_t)i;}
 for(int i=0;i<4096;i+=4){a[i+1]^=0x5a; asm volatile("" ::: "memory");}
 printf("checksum=0x%016llx\n",(unsigned long long)fnv1a(a,sizeof a)); return 0;}
