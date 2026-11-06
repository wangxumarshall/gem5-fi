#include <stdio.h>
#include <stdint.h>
static uint64_t fnv1a(const void*p,size_t n){const uint8_t*b=p;uint64_t h=1469598103934665603ULL;for(size_t i=0;i<n;i++){h^=b[i];h*=1099511628211ULL;}return h;}
int main(void){static volatile uint64_t a[1024]; for(int i=0;i<1024;i++) a[i]=i;
 uint64_t s=0; volatile uint64_t *p=a; uint64_t *q=(uint64_t*)(void*)p;
 for(int r=0;r<256;r++){int idx=(r*37)&1023; q[idx]=r; asm volatile("" ::: "memory"); s+=p[idx];}
 printf("checksum=0x%016llx\n",(unsigned long long)(s^fnv1a((const void*)a,sizeof a))); return 0;}
