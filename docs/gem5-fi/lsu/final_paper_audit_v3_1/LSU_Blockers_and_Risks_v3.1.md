# LSU 12模型最终方案：阻塞与风险 v3

## P0
| ID | 问题 | 影响 | 建议 |
|---|---|---|---|
| B01 | W2/W3/W5/W6/W7/W8六个专用负载缺失，禁止代理 | 9/12 BLOCKED | 新建六个专用负载 |
| B02 | 9/12模型无注入Hook；LP01/FW05仅PARTIAL | 无法执行 | 实现Hook |
| B03 | Trace v3关联键未实现 | 无法判定终态 | 实现commit_seq/execution_attempt/replay_generation/PropagationEdge等 |
| B04 | A01/A03 bit/op配置未实现 | 无法精确注入 | 研究者选bit/语义，开发加Load过滤 |
| B05 | LQ04提前pop+重用不可实现 | 原重用子模型BLOCKED | 只做提前失效或改模型 |
| B06 | SQ03 `_committed`不控制释放 | 不能作注入目标 | 选_canWB提前true |
| B07 | LP01现有uint64_t*越界 | 可能破坏内存 | 改逐字节byte0 bit3 |
| B08 | SP05无独立Ack | 语义不一致 | 重命名completion bookkeeping failure |
| B09 | FW05原部分重叠拼接不可实现 | 模型语义冲突 | 改wrong-source forwarding |
| B10 | DA04 byte_enable const | 无法改mask | 新增可写Hook |
| B11 | W1/W4基线未重跑 | BaselineValidated=0 | 重跑基线 |
| B12 | OUTPUT_ROOT/timeout未定 | 无法批量执行 | 研究者决定 |

## P1
- FW02 false miss可能只影响性能 → W4真实同地址对+Pilot。
- FW05 wrong-source需多个候选Store → W4/W8。
- MD04/RP01需W7真实alias/partial-forward → 新建W7。
- SE不调用TLB::lookup，DTLB不可观测 → SE标UNOBSERVABLE；FS方案另列成本。
- W7不能只因名字含Replay就认定能触发；W8不能只因宽度不同就认定覆盖byte-enable/partial overlap。
- 前5个eligible事件未必上下文不同 → 工作负载显式构造5组上下文。

## 建议顺序
1. 研究者确认12组Options、六个专用负载、OUTPUT_ROOT/timeout。
2. 实现Trace v3 + A01/A03/FW02 Pilot。
3. 实现其余Hook，新建六个负载，重跑W1/W4基线。
4. Pilot（R01可作Pilot）→ 正式60。


## v3.1 新增阻塞

- A01/A03：当前 POST hook 与 pushRequest PRE 方案冲突；需新增 PRE 模式。
- LQ04：clear() 释放在途 request 资源，安全性未证明。
- RP01：reschedule/replayMemInst 双路径，单点抑制未证明。
- 六个工作负载：已编译并跑通 gem5 SE 基线，但目标微架构事件触发未验证。
- W1/W4：当前 gem5 基线已重跑，exit 0，输出匹配 golden。

