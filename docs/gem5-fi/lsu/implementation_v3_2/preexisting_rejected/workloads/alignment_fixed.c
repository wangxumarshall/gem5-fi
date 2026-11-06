#include <stdio.h>
#include <stdint.h>
#include <string.h>
static uint64_t fnv1a(const void*p,size_t n){const uint8_t*b=p;uint64_t h=1469598103934665603ULL;for(size_t i=0;i<n;i++){h^=b[i];h*=1099511628211ULL;}return h;}
int main(void){static uint8_t a[4096]; memset(a,0xA5,sizeof a); uint64_t s=0;
 for(int i=0;i<1024;i++){uint32_t v=(uint32_t)(i*2654435761u); memcpy(a+i*4+1,&v,4); asm volatile("" ::: "memory");}
 for(int i=0;i<1022;i++){uint32_t v; memcpy(&v,a+i*4+1,4); s+=v;}
 for(int i=0;i<64;i++){a[i*8+2]=0x3c; a[i*8+5]=0xc3;}
 printf("checksum=0x%016llx\n",(unsigned long long)(s^fnv1a(a,sizeof a))); return 0;}
