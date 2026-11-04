# FR03-F5-W3 seed3 protocol deviation

'
> 复核时间：2026-11-04。原始日志未修改。

'
- 原预注册：Vec phys 0, lane0, bits 15..22, mask 0x007f8000, SA0（提交 b365cee5）。
'
- attempt-1：真实执行完成、证据有效、activated（gen3/6）、但最终 L5 路径 gen8 未被故障改变；chain_certified=false，terminal=exposed_unconsumed，oracle=Masked。保留为原 seed3 真实结局。
'
- attempt-2：目标改为 sign 0x80000000 SA1 lane0，发生在 attempt-1 结果之后；属于 protocol deviation / supplemental evidence，不计入原 seed3。
'
- 计数：FSU-FR03-F5-W3 3/3 → 2/3。AUTHORITATIVE 指针保留为 AUTHORITATIVE.attempt-2-protocol-deviation。
'
- 归档 chain_report.json 的 terminal=full 是旧工具产物；当前重算见 attempt-1/chain_report_recomputed.json（exposed_unconsumed）。
'
- 关键哈希见 ../protocol_review.json 的 evidence_hashes。
'
