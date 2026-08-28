/* x86-64 freestanding reg_chain: same algorithm as the AArch64 version
   (xorshift accumulator + checksum), but no libc — raw Linux x86-64
   sys_write/sys_exit. Built with clang --target=x86_64 + lld -nostdlib.
   Prints a 16-hex checksum to stdout (the §10.4 cross-ISA oracle). */
typedef unsigned long u64;
static long sys_write(int fd, const void *buf, long n) {
    long ret;
    __asm__ volatile("syscall" : "=a"(ret)
        : "0"(1), "D"(fd), "S"(buf), "d"(n) : "rcx","r11","memory");
    return ret;
}
static void sys_exit(int code) {
    __asm__ volatile("syscall" : : "a"(60), "D"(code));
    __builtin_unreachable();
}
static void put_hex(u64 v) {
    char b[17]; b[16]='\n';
    for (int i=15;i>=0;--i){unsigned d=v&0xf;b[i]=d<10?'0'+d:'a'+d-10;v>>=4;}
    sys_write(1, b, 17);
}
void _start(void) {
    u64 acc = 0x1234567890abcdefUL;
    for (volatile u64 i=0; i<2000000UL; ++i) {
        acc ^= (acc << 13);
        acc ^= (acc >> 7);
        acc ^= (acc << 17);
        acc += 0x9e3779b97f4a7c15UL;
    }
    put_hex(acc);
    sys_exit(0);
}
