/* w1_driver.c — W1 MiBench-TC23 十件套驱动器（DR-001 D+A 补建）
 *
 * 执行定义（Excel 6.负载清单 W1 + 清单 ITEM-040 契约）：
 *   blowfish(e+d)、patricia、fft(正+逆)、gsm(toast+untoast)、dijkstra、
 *   rijndael(e+d)、sha、bitcount、edge(susan -e)、smooth(susan -s)
 *   —— 全部最大输入集，一次运行覆盖十件套。
 *
 * Oracle 设计：
 *   - 子进程 stdout 直接继承（sha/patricia/fft/dijkstra/bitcount 的输出）
 *   - 驱动器对每个文件输出计算 FNV-1a 64 位校验和并打印（文件型 benchmark
 *     的结果进入 oracle：输出文件损坏 → SDC 可检出）
 *   - 每 benchmark 打印 exit/ok 行；驱动器 exit 0 iff 全部符合预期退出码
 *
 * 并行安全：mkdtemp 建立独立输出目录后 chdir（4 并发样本互不干扰，
 * 不污染 gem5 工作目录）；输入用编译期绝对路径（W1BASE）。
 *
 * 平台适配补丁记录（相对 MiBench 原始源，均非算法改动）：
 *   - sha: LONG→uint32（ILP32→LP64）+ -DLITTLE_ENDIAN（SHA-0 出厂口径，
 *     "abc"向量 0164b8a9... 精确匹配）
 *   - rijndael: fpos_t→long/ftell（fpos_t 结构体化）
 *   - bitcount: 去 Time 打印与 Best/Worst 计时选择（host 计时非确定）
 *   - patricia: 去残留 rpc/rpc.h include（无 XDR 调用）
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/wait.h>
#include <sys/types.h>
#include <fcntl.h>

#ifndef W1BASE
#define W1BASE "/home/sdc/gem5-fi-ding/workloads/mibench"
#endif

#define KEY32 "1234567890abcdeffedcba0987654321"
#define KEY64 "1234567890abcdeffedcba09876543211234567890abcdeffedcba0987654321"

typedef struct {
    const char *name;      /* benchmark 名 */
    char *const *argv;     /* execve argv（输入绝对路径，输出相对名） */
    int expected_exit;     /* 预期退出码（bf/patricia 固有 1） */
    const char *stdout_to; /* 子进程 stdout 重定向到该文件（NULL=继承） */
    const char *const *outs; /* 校验和文件列表（NULL 结尾） */
} spec_t;

/* FNV-1a 64-bit over a file */
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

static int run_one(const spec_t *s)
{
    pid_t pid = fork();
    if (pid < 0) { perror("fork"); return -1; }
    if (pid == 0) {
        if (s->stdout_to) {
            int fd = open(s->stdout_to, O_WRONLY|O_CREAT|O_TRUNC, 0644);
            if (fd < 0) { perror("open stdout_to"); _exit(126); }
            dup2(fd, 1);
            close(fd);
        }
        execv(s->argv[0], s->argv);
        perror("execv"); _exit(127);
    }
    int st; waitpid(pid, &st, 0);
    int code = WIFEXITED(st) ? WEXITSTATUS(st) : -1;
    int ok = (code == s->expected_exit);
    printf("[w1] %s exit=%d ok=%d\n", s->name, code, ok);
    for (const char *const *o = s->outs; *o; o++)
        printf("[w1] %s out %s fnv1a64=%016llx\n", s->name, *o, fnv1a64(*o));
    return ok ? 0 : 1;
}

int main(void)
{
    char tmp[] = "/tmp/w1_XXXXXX";
    if (!mkdtemp(tmp)) { perror("mkdtemp"); return 2; }
    if (chdir(tmp)) { perror("chdir"); return 2; }
    printf("[w1] start ten-benchmark suite (workdir isolated)\n");

    static char bfin[256], bfargv0[64], patin[256], fftargv0[64],
                gsmargv0[64], gsmstin[256], dijin[256], rndin[256],
                shain[256], susargv0[64], susin[256];
    snprintf(bfin, sizeof bfin, W1BASE "/data/blowfish/input_large.asc");
    snprintf(bfargv0, sizeof bfargv0, W1BASE "/bin/bf");
    snprintf(patin, sizeof patin, W1BASE "/data/large.udp");
    snprintf(fftargv0, sizeof fftargv0, W1BASE "/bin/fft");
    snprintf(gsmargv0, sizeof gsmargv0, W1BASE "/bin/toast");
    snprintf(gsmstin, sizeof gsmstin, W1BASE "/bin/untoast");
    snprintf(dijin, sizeof dijin, W1BASE "/data/input.dat");
    snprintf(rndin, sizeof rndin, W1BASE "/data/rijndael/input_large.asc");
    snprintf(shain, sizeof shain, W1BASE "/data/sha/input_large.asc");
    snprintf(susargv0, sizeof susargv0, W1BASE "/bin/susan");
    snprintf(susin, sizeof susin, W1BASE "/data/input_large.pgm");

    char bf_e[] = "e", bf_d[] = "d", fft8[] = "8", fftn[] = "32768",
         ffti[] = "-i", sus_e[] = "-e", sus_s[] = "-s",
         gsmt[] = "-fps", gsmc[] = "-c", rnde[] = "e", rndd[] = "d",
         iters[] = "1125000";

    char *bf_eav[] = {bfargv0, bf_e, bfin, "bf.enc", KEY32, NULL};
    char *bf_dav[] = {bfargv0, bf_d, "bf.enc", "bf.dec", KEY32, NULL};
    char *pat_av[] = {fftargv0 /*placeholder*/, NULL};
    char *fft_av[] = {fftargv0, fft8, fftn, NULL};
    char *fft_iav[] = {fftargv0, fft8, fftn, ffti, NULL};
    char *gsm_eav[] = {gsmargv0, gsmt, gsmc, "gsm.au", NULL};
    char *gsm_dav[] = {gsmstin, gsmt, gsmc, "gsm.enc.gsm", NULL};
    char *dij_av[] = {fftargv0 /*placeholder*/, NULL};
    char *rnd_eav[] = {fftargv0 /*placeholder*/, rndin, "rnd.enc", rnde, KEY64, NULL};
    char *rnd_dav[] = {fftargv0 /*placeholder*/, "rnd.enc", "rnd.dec", rndd, KEY64, NULL};
    char *sha_av[] = {fftargv0 /*placeholder*/, shain, NULL};
    char *bit_av[] = {fftargv0 /*placeholder*/, iters, NULL};
    char *sus_eav[] = {susargv0, susin, "susan_edge.pgm", sus_e, NULL};
    char *sus_sav[] = {susargv0, susin, "susan_smooth.pgm", sus_s, NULL};

    /* 修正占位符为真实二进制路径 */
    pat_av[0] = fft_av[0]; /* patricia bin 路径单独构造 */
    static char patargv0[64], dijargv0[64], rndargv0[64], shaargv0[64], bitargv0[64];
    snprintf(patargv0, sizeof patargv0, W1BASE "/bin/patricia");
    snprintf(dijargv0, sizeof dijargv0, W1BASE "/bin/dijkstra_large");
    snprintf(rndargv0, sizeof rndargv0, W1BASE "/bin/rijndael");
    snprintf(shaargv0, sizeof shaargv0, W1BASE "/bin/sha");
    snprintf(bitargv0, sizeof bitargv0, W1BASE "/bin/bitcnts");
    pat_av[0] = patargv0; pat_av[1] = patin; pat_av[2] = NULL;
    dij_av[0] = dijargv0; dij_av[1] = dijin; dij_av[2] = NULL;
    rnd_eav[0] = rndargv0; rnd_dav[0] = rndargv0;
    sha_av[0] = shaargv0; sha_av[1] = shain; sha_av[2] = NULL;
    bit_av[0] = bitargv0; bit_av[1] = iters; bit_av[2] = NULL;

    /* gsm 输入绝对路径 */
    static char gsmin[256];
    snprintf(gsmin, sizeof gsmin, W1BASE "/data/gsm/large.au");
    gsm_eav[3] = gsmin;

    const char *bf_enc[] = {"bf.enc", NULL};
    const char *bf_dec[] = {"bf.dec", NULL};
    const char *none[] = {NULL};
    const char *gsm_enc[] = {"gsm.enc.gsm", NULL};
    const char *gsm_dec[] = {"gsm.dec.au", NULL};
    const char *rnd_enc[] = {"rnd.enc", NULL};
    const char *rnd_dec[] = {"rnd.dec", NULL};
    const char *sus_e_outs[] = {"susan_edge.pgm", NULL};
    const char *sus_s_outs[] = {"susan_smooth.pgm", NULL};

    spec_t specs[] = {
        {"blowfish-e", bf_eav, 1, NULL, bf_enc},
        {"blowfish-d", bf_dav, 1, NULL, bf_dec},
        {"patricia",   pat_av,  1, NULL, none},
        {"fft",        fft_av,  0, NULL, none},
        {"fft-inv",    fft_iav, 0, NULL, none},
        {"gsm-toast",  gsm_eav, 0, "gsm.enc.gsm", gsm_enc},
        {"gsm-untoast",gsm_dav, 0, "gsm.dec.au", gsm_dec},
        {"dijkstra",   dij_av,  0, NULL, none},
        {"rijndael-e", rnd_eav, 0, NULL, rnd_enc},
        {"rijndael-d", rnd_dav, 0, NULL, rnd_dec},
        {"sha",        sha_av,  0, NULL, none},
        {"bitcount",   bit_av,  0, NULL, none},
        {"edge",       sus_eav, 0, NULL, sus_e_outs},
        {"smooth",     sus_sav, 0, NULL, sus_s_outs},
    };
    int nspec = sizeof specs / sizeof specs[0];

    int fails = 0;
    for (int i = 0; i < nspec; i++)
        fails += run_one(&specs[i]) ? 1 : 0;

    printf("[w1] suite done: %d/%d ok\n", nspec - fails, nspec);
    fprintf(stderr, "[w1] workdir %s (evidence retained)\n", tmp);
    return fails ? 1 : 0;
}
