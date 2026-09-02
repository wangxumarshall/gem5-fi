/* ras_checksum_kernel — §2.18 CHAOSRAS 验证 kernel.
 * 做正常计算 + 16-hex checksum。CHAOSRAS exc_suppress 不影响这个 kernel
 * （无 fault → 无 fault 可 clear）。但可以作为"无注入→golden"验证。
 * 真正的 RAS 验证需一个产生 fault 的 kernel——但 fault kernel 没 checksum。
 * 诚实：RAS pilot 只能验证"无注入→golden"回归，不能验证 exc_suppress 效果
 * （exc_suppress 需要 fault → crash → 无 checksum → 无法分类）。
 */
#include <stdio.h>
#include <stdint.h>
static uint64_t cs = 0xcbf29ce484222325ULL;
int main(void) {
    for (int i = 0; i < 1000; i++) { cs ^= i * 7; cs *= 0x100000001b3ULL; }
    printf("%016llx\n", cs);
    return 0;
}
