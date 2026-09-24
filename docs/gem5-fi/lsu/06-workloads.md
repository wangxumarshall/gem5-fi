# 06 · 负载清单

> 源：工作表「6.负载清单」（15 行 × 6 列：r1 表头 + r2–r15 共 W0–W13 十四个负载数据行；6 列全列逐字转录）。
> 转录规则：单元格文本逐字转录；表格内 `\n` → `<br>`、`|` → `\|`（与 extract.py 的 `md_cell` 一致）；「Excel行」列为行号标注，非源表列。

| Excel行 | 负载ID | 名称 | 类型 | 定义/输入与oracle | 主要覆盖单元 | 模式 |
|---|---|---|---|---|---|---|
| 2 | W0 | MiniCheck | 自设最小正确性探针 | 短数组校验和、guard page、指针链、load/store round-trip；每次运行产生确定 golden output | 全部；注入器冒烟与传播调试 | SE |
| 3 | W1 | MiBench-TC23 | 公开/论文复现 | blowfish、patricia、fft、gsm、dijkstra、rijndael、sha、bitcount、edge、smooth；最大输入集 | DTLB、SQ、L1D；与 TC'23 定性/定量对照 | FS 优先 |
| 4 | W2 | BEEBS-DelayAVF | 公开/论文复现 | md5、libbubblesort、libstrstr、matmult、libfibcall | LSQ 与预取器的时延故障规律对照；不直接比较绝对值 | SE |
| 5 | W3 | AGU-AddrModes | 自设定向负载 | 覆盖 base+imm、base+index、LSL、UXTW/SXTW、pre/post-index、LDP/STP、非对齐和页边界；每地址附软件 oracle | AGU | SE |
| 6 | W4 | TLB-AliasPerm | 自设定向负载 | 4KiB/2MiB 页、ASID 切换、同 VA 不同 PA、只读/不可执行页、TLBI 后重填、跨页 load/store | L1d-TLB | FS |
| 7 | W5 | SQ-Forward | 自设定向负载 | 同地址与部分重叠 store-to-load forwarding、不同字节掩码、地址晚到/数据晚到、alias、replay | Store Queue/内存依赖预测器 | SE |
| 8 | W6 | Cache-DirtyEvict | 自设定向负载 | working set=0.5×/1×/2×L1D；读改写、dirty eviction、writeback、conflict set、共享行 false sharing | L1d-Cache | SE + 多核 FS 子集 |
| 9 | W7 | Atomic-Litmus | 公开 litmus + 自设 | MP、SB、LB、IRIW、Dekker、ticket lock、CAS counter、LDXR/STXR 竞争；每轮检查禁出现结果 | 原子与同步 | 多核 FS |
| 10 | W8 | Prefetch-Stride | 自设定向负载 | 正/负/交错 stride、随机 pointer chase、跨页 stride、训练后变步长、需求/预取竞争 | 数据预取器 | SE |
| 11 | W9 | GAP/Graph500 子集 | 公开通用 | BFS/SSSP/PR，使用固定图与结果哈希；强调不规则地址和大 working set | DTLB、Cache、AGU、Prefetch | FS/SE |
| 12 | W10 | STREAM+PointerChase | 公开通用 + 自设 | STREAM Copy/Scale/Add/Triad 加随机 pointer chase；检查数组 hash 与遍历节点数 | 带宽、MSHR、预取、AGU | SE |
| 13 | W11 | SPEC CPU2017 采样区间 | 公开通用（需许可证） | 选择 mcf、omnetpp、xalancbmk、lbm 的固定 SimPoint/checkpoint；不跑全程 | 外部有效性；主结论之后复核 | FS/SE |
| 14 | W12 | SQLite-Speedtest1 | 真实应用 | SQLite speedtest1 固定数据库与事务脚本；用 PRAGMA integrity_check、查询结果和数据库文件哈希作为 oracle | AGU、Load Queue、Store Queue、L1d-Cache | SE/FS |
| 15 | W13 | PARSEC-Selected | 多线程真实应用 | PARSEC 中选 dedup、ferret、streamcluster 等共享队列/锁密集程序；固定线程数与输入，核对参考输出和结果哈希 | L1d-Cache一致性、原子与同步、数据预取器 | 多核 FS |

> 提取注：W4/W7/W13 为 FS/多核 FS 结构性依赖；W1 标注 FS 优先、W6 标注 SE+多核 FS 子集。
