#include <stdio.h>
#include <stdint.h>
#include <string.h>
static uint64_t fnv1a(const void *p,size_t n){const uint8_t*b=p;uint64_t h=1469598103934665603ULL;for(size_t i=0;i<n;i++){h^=b[i];h*=1099511628211ULL;}return h;}
int main(void){static uint8_t a[65536]; memset(a,0,sizeof a);
 for(int i=0;i<8192;i++){a[i*8]=(uint8_t)i; a[i*8+1]=(uint8_t)(i>>3); *(uint32_t*)(a+i*8+4)=0x11223344u^(uint32_t)i;}
 for(int i=0;i<8192;i+=2){a[i*8+3]=(uint8_t)(i*5); asm volatile("" ::: "memory");}
 uint64_t h=fnv1a(a,sizeof a); printf("checksum=0x%016llx\n",(unsigned long long)h); return 0;}
