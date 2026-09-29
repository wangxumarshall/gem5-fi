# 06 · 负载清单（W0–W13）

> 来源：《gem5-fi-LSU单元故障注入方案V2.0.xlsx》（Microsoft Excel 生成，9 表），逐格忠实提取：单元格文字原文照录，仅版式/标题排版；〔提取注〕为本目录标注。
> 生成器：`extract.py`（纯标准库，确定性输出，可重跑复现）；断言结果与诚实性注记见 `README.md`。

> 工作表「6.负载清单」R2–R15（表头 R1），6 列 × 14 负载。

| 负载ID | 名称 | 类型 | 定义/输入与oracle | 主要覆盖单元 | 模式 |
|---|---|---|---|---|---|
| W0 | MiniCheck | 自设最小正确性探针 | 短数组校验和、guard page、指针链、load/store round-trip；每次运行产生确定 golden output | 全部；注入器冒烟与传播调试 | SE |
| W1 | MiBench-TC23 | 公开/论文复现 | blowfish、patricia、fft、gsm、dijkstra、rijndael、sha、bitcount、edge、smooth；最大输入集 | DTLB、SQ、L1D；与 TC'23 定性/定量对照 | FS 优先 |
| W2 | BEEBS-DelayAVF | 公开/论文复现 | md5、libbubblesort、libstrstr、matmult、libfibcall | LSQ 与预取器的时延故障规律对照；不直接比较绝对值 | SE |
| W3 | AGU-AddrModes | 自设定向负载 | 覆盖 base+imm、base+index、LSL、UXTW/SXTW、pre/post-index、LDP/STP、非对齐和页边界；每地址附软件 oracle | AGU | SE |
| W4 | TLB-AliasPerm | 自设定向负载 | 4KiB/2MiB 页、ASID 切换、同 VA 不同 PA、只读/不可执行页、TLBI 后重填、跨页 load/store | L1d-TLB | FS |
| W5 | SQ-Forward | 自设定向负载 | 同地址与部分重叠 store-to-load forwarding、不同字节掩码、地址晚到/数据晚到、alias、replay | Store Queue/内存依赖预测器 | SE |
| W6 | Cache-DirtyEvict | 自设定向负载 | working set=0.5×/1×/2×L1D；读改写、dirty eviction、writeback、conflict set、共享行 false sharing | L1d-Cache | SE + 多核 FS 子集 |
| W7 | Atomic-Litmus | 公开 litmus + 自设 | MP、SB、LB、IRIW、Dekker、ticket lock、CAS counter、LDXR/STXR 竞争；每轮检查禁出现结果 | 原子与同步 | 多核 FS |
| W8 | Prefetch-Stride | 自设定向负载 | 正/负/交错 stride、随机 pointer chase、跨页 stride、训练后变步长、需求/预取竞争 | 数据预取器 | SE |
| W9 | GAP/Graph500 子集 | 公开通用 | BFS/SSSP/PR，使用固定图与结果哈希；强调不规则地址和大 working set | DTLB、Cache、AGU、Prefetch | FS/SE |
| W10 | STREAM+PointerChase | 公开通用 + 自设 | STREAM Copy/Scale/Add/Triad 加随机 pointer chase；检查数组 hash 与遍历节点数 | 带宽、MSHR、预取、AGU | SE |
| W11 | SPEC CPU2017 采样区间 | 公开通用（需许可证） | 选择 mcf、omnetpp、xalancbmk、lbm 的固定 SimPoint/checkpoint；不跑全程 | 外部有效性；主结论之后复核 | FS/SE |
| W12 | SQLite-Speedtest1 | 真实应用 | SQLite speedtest1 固定数据库与事务脚本；用 PRAGMA integrity_check、查询结果和数据库文件哈希作为 oracle | AGU、Load Queue、Store Queue、L1d-Cache | SE/FS |
| W13 | PARSEC-Selected | 多线程真实应用 | PARSEC 中选 dedup、ferret、streamcluster 等共享队列/锁密集程序；固定线程数与输入，核对参考输出和结果哈希 | L1d-Cache一致性、原子与同步、数据预取器 | 多核 FS |

## 接线状态〔提取注，派生自「7.展开执行矩阵」〕

- **已接入展开矩阵（14/14 个，全部接入）**：W0=6 格；W1=27 格；W10=27 格；W11=12 格；W12=15 格；W13=6 格；W2=6 格；W3=24 格；W4=24 格；W5=54 格；W6=55 格；W7=29 格；W8=25 格；W9=15 格。
- **已定义、未接入（0 个）**：与 OoO V2.0（3 个负载未接线）不同，本簿全部 14 个负载均出现在展开矩阵中。

