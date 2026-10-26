/*
 * chaos_cache_resp.hh — [0202-T02F2-MSHR] BaseCache::recvTimingResp 的响应分类契约。
 *
 * 为什么需要它（实测根因，2026-10-27）：
 *   一次 **UnCacheable 写**（UC write）走 write buffer 发出（BaseCache::
 *   sendWriteQueuePacket「forward as is」，**不分配 MSHR**，也不 push sender
 *   state）。若该写落到返回错误的目标（例：未映射地址命中 iobus 的 default
 *   `badaddr_responder`），回包是 `BadAddressError`。而
 *   `src/mem/packet.cc:216` 定义 `BadAddressError` 的 flags 为
 *   `{IsResponse, IsError}` —— **不含 IsWrite**。于是
 *   `recvTimingResp` 的 `pkt->isWrite()` 判据为假，该响应跳过
 *   `handleUncacheableWriteResp`，落到 `dynamic_cast<MSHR*>(popSenderState())`
 *   之后，而 UC 写从未分配 MSHR ⇒ `assert(mshr)` 失败 ⇒ SIGABRT。
 *   实测：T02-F2-W4 explicit seed 1，debug 日志完整链路见
 *   docs/superpowers/plans/2026-10-27-0202-t02f2-mshr-repair.md §根因。
 *
 * 本函数把「一个进入 recvTimingResp 的响应该走哪条路径」抽成**纯判定**，
 * 以便用真实的 command flags + senderState 事实做确定性单元测试
 * （tests/chaos_cache_resp_test.cc + tests/test_lsu_cache_resp_classify.py）。
 *
 * 注意：本版本是**当前生产行为的忠实提取**（base.cc:752-757 的判据），
 * 因此它对 BadAddressError 这类 error 响应会返回 MshrPath —— 这正是要修的缺陷，
 * 失败测试 tests/chaos_cache_resp_test.cc 会把它钉住（先红）。
 */
#ifndef __MEM_CACHE_CHAOS_CACHE_RESP_HH__
#define __MEM_CACHE_CHAOS_CACHE_RESP_HH__

namespace gem5
{

namespace chaos
{

/** 一个响应在 BaseCache::recvTimingResp 中应走的路径。 */
enum class CacheRespPath
{
    /** 写缓冲发出的请求（UC 写 / 写回/ clean evict）的响应：
     *  无 MSHR，走 handleUncacheableWriteResp()，直接经 cpuSidePort 回上游。 */
    WriteBuffer,
    /** 需要 MSHR senderState 的响应（miss / fill / prefetch / 读类 UC）。 */
    MshrPath,
};

/**
 * @param pkt_is_write           pkt->isWrite()   （error 响应可能丢失该位）
 * @param pkt_is_error           pkt->isError()
 * @param pkt_is_uncacheable     pkt->req->isUncacheable()
 * @param has_mshr_sender_state  popSenderState() 得到的是否为 MSHR
 */
inline CacheRespPath
classifyCacheTimingResp(bool pkt_is_write, bool pkt_is_error,
                        bool pkt_is_uncacheable, bool has_mshr_sender_state)
{
    (void)pkt_is_error;
    (void)pkt_is_uncacheable;
    (void)has_mshr_sender_state;

    // [当前生产判据] base.cc:752「if (pkt->isWrite() && cmd != LockedRMWWriteResp)」
    if (pkt_is_write) {
        return CacheRespPath::WriteBuffer;
    }
    return CacheRespPath::MshrPath;
}

} // namespace chaos
} // namespace gem5

#endif // __MEM_CACHE_CHAOS_CACHE_RESP_HH__
