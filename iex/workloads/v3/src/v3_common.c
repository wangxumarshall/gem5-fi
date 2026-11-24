
#define N_EP 128
typedef unsigned long u64;
volatile u64 iex_output[2 * N_EP] __attribute__((aligned(16)));
extern const char iex_context[];

static long
sys_write(int fd, const void *buf, unsigned long n)
{
    register long x8 __asm__("x8") = 64;
    register long x0 __asm__("x0") = fd;
    register const void *x1 __asm__("x1") = buf;
    register unsigned long x2 __asm__("x2") = n;
    __asm__ volatile("svc #0" : "+r"(x0) : "r"(x1), "r"(x2), "r"(x8)
                     : "memory");
    return x0;
}

static void __attribute__((noreturn))
sys_exit(int code)
{
    register long x8 __asm__("x8") = 93;
    register long x0 __asm__("x0") = code;
    __asm__ volatile("svc #0" : : "r"(x0), "r"(x8) : "memory");
    __builtin_unreachable();
}

static char *
hex64(char *p, u64 v)
{
    static const char d[] = "0123456789ABCDEF";
    int i;
    *p++ = '0';
    *p++ = 'x';
    for (i = 60; i >= 0; i -= 4)
        *p++ = d[(v >> i) & 0xf];
    return p;
}

void
iex_print_mem(void)
{
    char buf[256];
    char *p = buf;
    const char *c;
    int i;
    for (c = iex_context; *c; ++c)
        *p++ = *c;
    for (i = 0; i < N_EP; ++i) {
        *p++ = ',';
        p = hex64(p, iex_output[2 * i]);
        *p++ = ',';
        p = hex64(p, iex_output[2 * i + 1]);
        if (p - buf > 200) {
            sys_write(1, buf, (unsigned long)(p - buf));
            p = buf;
        }
    }
    *p++ = '\n';
    sys_write(1, buf, (unsigned long)(p - buf));
    sys_exit(0);
}
