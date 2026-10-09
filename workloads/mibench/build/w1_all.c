/* w1_all.c — W1 MiBench-TC23 十件套单进程驱动器（v2，fork-free）
 *
 * 设计变更（v1 fork 方案废弃的原因，gem5 SE 冒烟实证 2026-10-09）：
 *   gem5 SE 的 clone 系统调用需要系统中有空闲 ThreadContext
 *   （syscall_emul.hh:1774 threads.findFree()），单 CPU 板卡恒返回
 *   EAGAIN → fork 全部失败；增加 CPU 会破坏 B0 平台定义且子进程将
 *   跑在无注入器的 CPU 上（FI 语义失效）。
 *   v2 = 全部十件套静态链接为一个进程（-Dmain=bm_X_main 重命名），
 *   驱动器顺序调用各 benchmark 的 main——执行全程留在 CPU0，
 *   注入器可见全部内存操作，FI 语义与现有单进程负载完全一致。
 *
 * exit() 覆盖：各 benchmark 以 exit() 终止（patricia/bf 固有 exit(1)），
 * 驱动器用 setjmp/longjmp 捕获 exit 返回到调用点继续下一 benchmark。
 * 驱动器自身以 _exit() 终止（不经覆盖的 exit，避免 crt 调用 exit 时
 * longjmp 到失效的 jmp_buf）。
 *
 * 其余口径同 v1：mkdtemp 输出隔离（4 并发安全）、FNV-1a64 输出文件
 * 校验和（文件型 benchmark 的 SDC 可检出）、[w1] 标记行 + line-buffered。
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <setjmp.h>
#include <unistd.h>
#include <fcntl.h>
#include <sys/types.h>

#ifndef W1BASE
#define W1BASE "/home/sdc/gem5-fi-ding/workloads/mibench"
#endif

#define KEY32 "1234567890abcdeffedcba0987654321"
#define KEY64 "1234567890abcdeffedcba09876543211234567890abcdeffedcba0987654321"

/* 各 benchmark 重命名后的 main（构建时 -Dmain=bm_X_main） */
extern int bm_bf_main(int, char **);
extern int bm_patricia_main(int, char **);
extern int bm_fft_main(int, char **);
extern int bm_gsm_main(int, char **);
extern int bm_dijkstra_main(int, char **);
extern int bm_rijndael_main(int, char **);
extern int bm_sha_main(int, char **);
extern int bm_bitcount_main(int, char **);
extern int bm_susan_main(int, char **);

static jmp_buf g_jmp;
static volatile int g_status;

/* 拦截 benchmark 的 exit()（-Wl,--wrap=exit 重定向到本函数）→ longjmp
 * 回驱动器循环；libc.a 的 exit 强符号不冲突。驱动器自身以 _exit 终止，
 * crt 的 exit(ret) 路径不会执行。 */
void __wrap_exit(int status)
{
    g_status = status;
    longjmp(g_jmp, 1);
}

static unsigned long long fnv1a64(const char *path)
{
    unsigned long long h = 0xcbf29ce484222325ULL;
    unsigned char buf[65536];
    int fd = open(path, O_RDONLY);
    if (fd < 0) { printf("fnv: cannot open %s\n", path); return 0; }
    ssize_t n;
    while ((n = read(fd, buf, sizeof buf)) > 0)
        for (ssize_t i = 0; i < n; i++) { h ^= buf[i]; h *= 0x100000001b3ULL; }
    close(fd);
    return h;
}

static int copy_file(const char *src, const char *dst)
{
    int in = open(src, O_RDONLY), out = open(dst, O_WRONLY|O_CREAT|O_TRUNC, 0644);
    if (in < 0 || out < 0) return -1;
    char buf[65536]; ssize_t n;
    while ((n = read(in, buf, sizeof buf)) > 0)
        if (write(out, buf, n) != n) return -1;
    close(in); close(out); return 0;
}

typedef struct {
    const char *name;
    int (*fn)(int, char **);
    char **argv;               /* 以 NULL 结尾，argv[0] 为程序名 */
    int expected_exit;
    const char *const *outs;   /* 校验和文件（相对 workdir） */
} spec_t;

#define NARGV 6

int main(void)
{
    setvbuf(stdout, NULL, _IOLBF, 0);
    char tmp[] = "/tmp/w1_XXXXXX";
    if (!mkdtemp(tmp)) { perror("mkdtemp"); _exit(2); }
    if (chdir(tmp)) { perror("chdir"); _exit(2); }
    fprintf(stderr, "[w1] workdir %s\n", tmp);
    printf("[w1] start ten-benchmark suite (single process, workdir isolated)\n");

    /* 路径与参数（静态存储，编译期 W1BASE） */
    static char p_bf[256], p_pat[256], p_dij[256], p_rnd[256], p_sha[256],
                p_gsm[256], p_sus[256];
    snprintf(p_bf,  sizeof p_bf,  W1BASE "/data/blowfish/input_large.asc");
    snprintf(p_pat, sizeof p_pat, W1BASE "/data/large.udp");
    snprintf(p_dij, sizeof p_dij, W1BASE "/data/input.dat");
    snprintf(p_rnd, sizeof p_rnd, W1BASE "/data/rijndael/input_large.asc");
    snprintf(p_sha, sizeof p_sha, W1BASE "/data/sha/input_large.asc");
    snprintf(p_gsm, sizeof p_gsm, W1BASE "/data/gsm/large.au");
    snprintf(p_sus, sizeof p_sus, W1BASE "/data/input_large.pgm");

    char n_bf[] = "bf", n_pat[] = "patricia", n_fft[] = "fft",
         n_toast[] = "toast", n_untoast[] = "untoast",
         n_dij[] = "dijkstra_large", n_rnd[] = "rijndael", n_sha[] = "sha",
         n_bc[] = "bitcnts", n_sus[] = "susan";
    char f8[] = "8", fn[] = "32768", fi[] = "-i", it[] = "1125000",
         se[] = "-e", ss[] = "-s", gf[] = "-fps", gc[] = "-c",
         e_e[] = "e", e_d[] = "d";

    char *a_bf_e[]  = {n_bf, e_e, p_bf, "bf.enc", KEY32, NULL};
    char *a_bf_d[]  = {n_bf, e_d, "bf.enc", "bf.dec", KEY32, NULL};
    char *a_pat[]   = {n_pat, p_pat, NULL};
    char *a_fft[]   = {n_fft, f8, fn, NULL};
    char *a_fft_i[] = {n_fft, f8, fn, fi, NULL};
    char *a_gsm_e[] = {n_toast, gf, "large.au", NULL};
    char *a_gsm_d[] = {n_untoast, gf, "large.au.gsm", NULL};
    char *a_dij[]   = {n_dij, p_dij, NULL};
    char *a_rnd_e[] = {n_rnd, p_rnd, "rnd.enc", e_e, KEY64, NULL};
    char *a_rnd_d[] = {n_rnd, "rnd.enc", "rnd.dec", e_d, KEY64, NULL};
    char *a_sha[]   = {n_sha, p_sha, NULL};
    char *a_bc[]    = {n_bc, it, NULL};
    char *a_sus_e[] = {n_sus, p_sus, "susan_edge.pgm", se, NULL};
    char *a_sus_s[] = {n_sus, p_sus, "susan_smooth.pgm", ss, NULL};

    const char *o_bf_e[]  = {"bf.enc", NULL};
    const char *o_bf_d[]  = {"bf.dec", NULL};
    const char *o_none[]  = {NULL};
    const char *o_gsm_e[] = {"large.au.gsm", NULL};
    const char *o_rnd_e[] = {"rnd.enc", NULL};
    const char *o_rnd_d[] = {"rnd.dec", NULL};
    const char *o_sus_e[] = {"susan_edge.pgm", NULL};
    const char *o_sus_s[] = {"susan_smooth.pgm", NULL};

    spec_t specs[] = {
        {"blowfish-e",  bm_bf_main,       a_bf_e,  1, o_bf_e},
        {"blowfish-d",  bm_bf_main,       a_bf_d,  1, o_bf_d},
        {"patricia",    bm_patricia_main, a_pat,   1, o_none},
        {"fft",         bm_fft_main,      a_fft,   0, o_none},
        {"fft-inv",     bm_fft_main,      a_fft_i, 0, o_none},
        {"gsm-toast",   bm_gsm_main,      a_gsm_e, 0, o_gsm_e},
        {"gsm-untoast", bm_gsm_main,      a_gsm_d, 0, o_none},
        {"dijkstra",    bm_dijkstra_main, a_dij,   0, o_none},
        {"rijndael-e",  bm_rijndael_main, a_rnd_e, 0, o_rnd_e},
        {"rijndael-d",  bm_rijndael_main, a_rnd_d, 0, o_rnd_d},
        {"sha",         bm_sha_main,      a_sha,   0, o_none},
        {"bitcount",    bm_bitcount_main, a_bc,    0, o_none},
        {"edge",        bm_susan_main,    a_sus_e, 0, o_sus_e},
        {"smooth",      bm_susan_main,    a_sus_s, 0, o_sus_s},
    };
    int nspec = sizeof specs / sizeof specs[0];

    /* gsm 文件模式：输入复制进 workdir（toast 写 large.au.gsm，untoast
     * 解码回 large.au——避免 -c 的 stdout 二进制污染 oracle） */
    if (copy_file(p_gsm, "large.au")) { printf("fnv: gsm input copy failed\n"); }
    const char *o_gsm_d[] = {"large.au", NULL};
    specs[6].outs = o_gsm_d;   /* gsm-untoast 的输出 = 解码结果 */

    int fails = 0;
    for (int i = 0; i < nspec; i++) {
        spec_t *s = &specs[i];
        int rc;
        int argc = 0;
        while (s->argv[argc]) argc++;
        if (setjmp(g_jmp) == 0)
            rc = s->fn(argc, s->argv);      /* 正常 return 路径 */
        else
            rc = g_status;                   /* benchmark 调了 exit() */
        int ok = (rc == s->expected_exit);
        printf("[w1] %s exit=%d ok=%d\n", s->name, rc, ok);
        for (const char *const *o = s->outs; *o; o++)
            printf("[w1] %s out %s fnv1a64=%016llx\n", s->name, *o, fnv1a64(*o));
        if (!ok) fails++;
    }
    printf("[w1] suite done: %d/%d ok\n", nspec - fails, nspec);
    fflush(stdout);
    _exit(fails ? 1 : 0);
}
