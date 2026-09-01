/* exc_trigger — §2.18 CHAOSRAS 验证 kernel.
 *
 * 触发一个 ARM 异常（除零 SIGFPE 或 unaligned access SIGBUS），让 commit
 * 看到 fault。CHAOSExMon exc_suppress 在 commit.cc:1161 清 fault 后，
 * 本该 trap 的指令静默提交——SDC。输出 16-hex checksum（无注入时
 * 应崩溃/trap exit，有注入时可能正常完成或 SDC）。
 *
 * 这里用 unaligned access（A64 SCTLR_EL1.A=1 时 unaligned load 触发
 * SError/SIGBUS）。在 SE 模式下 gem5 对 unaligned 默认不 fault（A=0），
 * 但 division-by-zero 在 SE 下 gem5 会 trap (SIGFPE)。
 *
 * Build: gcc -static -O0 -o exc_trigger exc_trigger.c
 */
#include <stdio.h>
#include <stdint.h>
#include <signal.h>

static uint64_t cs = 0xcbf29ce484222325ULL;
static void fold(uint64_t v) { cs ^= v; cs *= 0x100000001b3ULL; }

int main(void) {
    /* Try to generate a fault that commit will see: write to NULL.
     * In gem5 SE, this should produce a SIGSEGV (commit sees a fault).
     * CHAOSRAS exc_suppress would clear it -> no crash, program continues
     * -> SDC (the program reaches the checksum print).
     */
    volatile int *p = (volatile int *)0;
    int val = 0;
    /* This dereference will fault (SIGSEGV in SE). Without CHAOSRAS:
     * gem5 aborts. With CHAOSRAS exc_suppress: the fault is cleared at
     * commit -> the instruction 'completes' (val = whatever) -> SDC. */
    val = *p;  /* NULL deref -> fault */
    fold((uint64_t)val);

    printf("%016llx\n", cs);
    return 0;
}
