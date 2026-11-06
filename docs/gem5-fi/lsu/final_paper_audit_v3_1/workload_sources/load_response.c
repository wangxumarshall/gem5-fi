#include <stdio.h>
#include <stdint.h>
#include <string.h>
static uint64_t fnv1a(const void *p,size_t n){const uint8_t*b=p;uint64_t h=1469598103934665603ULL;for(size_t i=0;i<n;i++){h^=b[i];h*=1099511628211ULL;}return h;}
int main(void){static volatile uint64_t a[2048]; for(int i=0;i<2048;i++) a[i]=(uint64_t)i*0x9e3779b97f4a7c15ULL;
 uint64_t s=0; for(int r=0;r<128;r++){uint64_t x=a[(r*131)&2047]; uint64_t y=a[(r*197+7)&2047]; s+=x^y; asm volatile("" ::: "memory");}
 printf("checksum=0x%016llx\n",(unsigned long long)(s^fnv1a((const void*)a,sizeof a))); return 0;}
