/* [LSU][MDSPEC][R6-A2] 同源 repeat 载体公共头。
 *
 * 背景：F1/F2/F4 的首发射位置在 eligible 计数空间（F1 max=1290806,
 * F2/F4 max=140806），而 W3/W0/W5 的短探针每次只产生 ~2.6-3.2k eligible。
 * 用户 2026-10-28 工作令授权“重复执行同一工作负载”扩展 eligible 流：
 * workload ID 不变、每次迭代执行相同程序与 oracle、manifest 记录
 * repeat_factor、频率间隔/seed/trigger 算法不变。
 *
 * 约定：
 *   - argv[1] = repeat 次数；缺省 1（输出与旧二进制逐字节一致，无 ITER 行）。
 *   - 1..CHAOS_REPEAT_MAX；非法值按 1 处理（campaign 侧还会做上限拒绝）。
 *   - reps>1 时每迭代打印 `ITER:<n>:<16hex>`，末行仍是裸 <16hex>，
 *     使既有 L5 classifier（取最后一个 checksum 行）继续工作；
 *     campaign 另行逐 ITER 行独立校验 golden。
 */
#ifndef CHAOS_REPEAT_H
#define CHAOS_REPEAT_H

#include <stdint.h>
#include <stdlib.h>
#include <unistd.h>

/* [R6-A2 census 2026-10-28] 实测每迭代 eligible 增量远小于整次运行
 * （W3/W5 首趟含启动流）：F1-W3 需 ~4023 趟、W5-F2 需 ~934 趟。
 * 4096 是“有界且可完成”的实测上限，不是拍的。 */
#define CHAOS_REPEAT_MAX 4096

static inline int
chaos_repeat_count(int argc, char **argv)
{
    if (argc < 2 || argv == NULL || argv[1] == NULL)
        return 1;
    char *end = NULL;
    long n = strtol(argv[1], &end, 10);
    if (end == argv[1] || n < 1)
        return 1;
    if (n > CHAOS_REPEAT_MAX)
        n = CHAOS_REPEAT_MAX;
    return (int)n;
}

static inline void
chaos_write_hex16(unsigned long v)
{
    char buf[16];
    for (int i = 15; i >= 0; --i) {
        unsigned d = v & 0xf;
        buf[i] = d < 10 ? (char)('0' + d) : (char)('a' + d - 10);
        v >>= 4;
    }
    write(1, buf, 16);
}

static inline void
chaos_emit_iter(int idx, unsigned long v)
{
    char pre[16];
    int n = 0;
    pre[n++] = 'I'; pre[n++] = 'T'; pre[n++] = 'E'; pre[n++] = 'R';
    pre[n++] = ':';
    if (idx >= 100)
        pre[n++] = (char)('0' + (idx / 100) % 10);
    if (idx >= 10)
        pre[n++] = (char)('0' + (idx / 10) % 10);
    pre[n++] = (char)('0' + idx % 10);
    pre[n++] = ':';
    write(1, pre, n);
    chaos_write_hex16(v);
    write(1, "\n", 1);
}

#endif /* CHAOS_REPEAT_H */
