#include <stdio.h>
#include <stdint.h>
#include <string.h>
static uint64_t fnv1a(const void *p, size_t n){const uint8_t*b=p;uint64_t h=1469598103934665603ULL;for(size_t i=0;i<n;i++){h^=b[i];h*=1099511628211ULL;}return h;}
int main(void){static volatile uint8_t a[4096]; static uint8_t guard[64]; uint64_t s=0;
 for(int i=0;i<4096;i++) a[i]=(uint8_t)(i*7+3);
 memset(guard,0xA5,sizeof guard);
 for(int r=0;r<64;r++){int idx=(r*97+13)&4095; uint8_t v=a[idx]; uint8_t w=a[(idx+64)&4095]; s+=v*3u+w; if((r&7)==0) s^=0x9e3779b97f4a7c15ULL; asm volatile("" ::: "memory");}
 for(int i=0;i<64;i++) if(guard[i]!=0xA5){printf("guard_fail=%d\n",i);return 2;}
 printf("checksum=0x%016llx\n",(unsigned long long)(s^fnv1a(a,sizeof a))); return 0;}
