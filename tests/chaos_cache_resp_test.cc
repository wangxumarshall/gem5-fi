/*
 * chaos_cache_resp_test.cc — [0202-T02F2-MSHR] BaseCache::recvTimingResp 响应分类
 * 契约的**确定性**单元测试（standalone，不链接 gem5；编译方式见下方）。
 *
 *   g++ -std=c++17 -Wall -Wextra -Werror -I CHAOS/gem5/src \
 *       -DCMD_BADADDRESSERROR_ISWRITE=... -DCMD_BADADDRESSERROR_ISERROR=... ... \
 *       tests/chaos_cache_resp_test.cc -o /tmp/x && /tmp/x
 *
 * 各 command 的 flags **不是写死的**：由 tests/test_lsu_cache_resp_classify.py
 * 从权威源 `CHAOS/gem5/src/mem/packet.cc` 的 commandTable 解析后经 -D 传入，
 * 因此本测试真实消费生产数据（不是日志字符串）。
 *
 * 被钉死的规格（来自实测根因，见
 * docs/superpowers/plans/2026-10-27-0202-t02f2-mshr-repair.md §根因）：
 *   一次 UnCacheable 写走 write buffer 发出、**不分配 MSHR**；若目标回
 *   BadAddressError（flags 只有 IsResponse|IsError，**不含 IsWrite**），
 *   该响应必须仍按「UC 写响应」处理（handleUncacheableWriteResp），
 *   绝不能落到要求 MSHR 的路径（实测断言 base.cc:783）。
 */
#include "mem/cache/chaos_cache_resp.hh"

#include <cstdio>
#include <vector>

using gem5::chaos::CacheRespPath;
using gem5::chaos::classifyCacheTimingResp;

static std::vector<const char *> failed;

static void
check(const char *name, bool ok, const char *detail = "")
{
    if (ok) {
        printf("  PASS %s\n", name);
    } else {
        printf("  FAIL %s  :: %s\n", name, detail);
        failed.push_back(name);
    }
}

static const char *
pathName(CacheRespPath p)
{
    return p == CacheRespPath::WriteBuffer ? "WriteBuffer" : "MshrPath";
}

int
main()
{
    // ---- 生产数据事实（来自 packet.cc commandTable，经 -D 传入）----
    printf("[0] commandTable 事实（源自 CHAOS/gem5/src/mem/packet.cc）\n");
    check("WriteResp 含 IsWrite", CMD_WRITERESP_ISWRITE == 1);
    check("ReadResp 不含 IsWrite", CMD_READRESP_ISWRITE == 0);
    check("BadAddressError 不含 IsWrite（根因事实）", CMD_BADADDRESSERROR_ISWRITE == 0);
    check("BadAddressError 含 IsError", CMD_BADADDRESSERROR_ISERROR == 1);
    check("ReadError 不含 IsWrite", CMD_READERROR_ISWRITE == 0);
    check("ReadError 含 IsError", CMD_READERROR_ISERROR == 1);

    printf("[1] UC 写成功响应（WriteResp）⇒ WriteBuffer\n");
    check("WriteResp/UC/no-mshr ⇒ WriteBuffer",
          classifyCacheTimingResp(CMD_WRITERESP_ISWRITE, CMD_WRITERESP_ISERROR,
                                  true, false) == CacheRespPath::WriteBuffer);

    printf("[2] UC 写的错误响应（BadAddressError）⇒ WriteBuffer（修复目标）\n");
    {
        const auto got =
            classifyCacheTimingResp(CMD_BADADDRESSERROR_ISWRITE, CMD_BADADDRESSERROR_ISERROR,
                                    true, false);
        char d[128];
        snprintf(d, sizeof d, "got %s（UC 写无 MSHR，落到 MshrPath 即 base.cc:783 断言）",
                 pathName(got));
        check("BadAddressError/UC/no-mshr ⇒ WriteBuffer",
              got == CacheRespPath::WriteBuffer, d);
    }

    printf("[3] UC 读的错误响应（ReadError，**有** MSHR）⇒ MshrPath（不得误路由）\n");
    check("ReadError/UC/with-mshr ⇒ MshrPath",
          classifyCacheTimingResp(CMD_READERROR_ISWRITE, CMD_READERROR_ISERROR,
                                  true, true) == CacheRespPath::MshrPath);
    check("BadAddressError/UC/with-mshr ⇒ MshrPath（读侧 badaddr）",
          classifyCacheTimingResp(CMD_BADADDRESSERROR_ISWRITE, CMD_BADADDRESSERROR_ISERROR,
                                  true, true) == CacheRespPath::MshrPath);

    printf("[4] 普通读响应（非 error）⇒ MshrPath（无故障路径不变）\n");
    check("ReadResp/no-error/with-mshr ⇒ MshrPath",
          classifyCacheTimingResp(CMD_READRESP_ISWRITE, CMD_READRESP_ISERROR,
                                  false, true) == CacheRespPath::MshrPath);

    printf("[5] 非 UC 的非 MSHR 错误响应 ⇒ 仍 MshrPath（保持严格，不掩盖真异常）\n");
    check("BadAddressError/non-UC/no-mshr ⇒ MshrPath（异常仍响亮）",
          classifyCacheTimingResp(CMD_BADADDRESSERROR_ISWRITE, CMD_BADADDRESSERROR_ISERROR,
                                  false, false) == CacheRespPath::MshrPath);

    printf("\n");
    if (!failed.empty()) {
        printf("FAILED (%zu): [", failed.size());
        for (size_t i = 0; i < failed.size(); ++i) {
            printf("%s%s", i ? ", " : "", failed[i]);
        }
        printf("]\n");
        return 1;
    }
    printf("ALL PASS\n");
    return 0;
}
