# 06 · 负载清单（W0–W13）

> 来源：《gem5-fi-OoO单元故障注入方案V2.0.xlsx》（WPS 生成，9 表），逐格忠实提取：单元格文字原文照录，仅版式/标题排版；〔提取注〕为本目录标注。
> 生成器：`extract.py`（纯标准库，确定性输出，可重跑复现）；断言结果与诚实性注记见 `README.md`。

> 工作表「6.负载清单」R2–R15（表头 R1），6 列 × 14 负载。

| 负载ID | 名称 | 类型 | 定义/输入与oracle | 主要覆盖单元 | 模式 |
|---|---|---|---|---|---|
| W0 | MiniCheck-OOO | 自设最小正确性探针 | 短整数/FP/NEON 算术、依赖链、分支、异常恢复；逐提交 trace 和最终 hash 双 oracle | 全部；注入器冒烟与传播调试 | SE |
| W1 | MiBench-TC23 | 公开/论文复现 | blowfish、patricia、fft、gsm、dijkstra、rijndael、sha、bitcount、edge、smooth；最大输入集；输出与 golden 比对 | Int Dispatch/ROB；与 TC'23 定性/定量对照 | FS优先 |
| W2 | BEEBS-DelayAVF | 公开/论文复现 | md5、libbubblesort、libstrstr、matmult、libfibcall；固定输入和输出 | Int Decode；只对照时延故障排序，不比较绝对 SDC 率 | SE |
| W3 | A64-DecodeProbe | 自设定向负载 | 系统覆盖 data-processing immediate/register、shift/extend、conditional select、branch、load/store 解码边界；每条指令有软件参考值和 expected decode tuple | Int Decode | SE |
| W4 | Rename-Dependency | 自设定向负载 | RAW/WAR/WAW 链、x0、同周期多目的、长活跃区间、寄存器压力、分支嵌套；检查映射唯一性和最终寄存器 hash | Int Rename | SE |
| W5 | ROB-Recovery | 自设定向负载 | 深 ROB、长/短延迟混合、连续 mispredict、精确异常、squash 后重分派；逐提交 PC/opcode/目的和值比较 | Int Dispatch/ROB | SE+FS子集 |
| W6 | CoreMark+Embench | 公开通用 | CoreMark 与 Embench 全集；固定编译器/优化/输入；使用内置校验及输出 hash | 整数 OOO 全链 | SE/FS |
| W7 | GAP-Selected | 公开通用 | BFS、SSSP、PageRank；固定图和结果 hash；制造不规则依赖、长延迟和 ROB 压力 | Int Rename、Dispatch/ROB | SE/FS |
| W8 | FP-ScalarProbe | 自设定向负载 | FP32/FP64 add/mul/div/sqrt/FMA、NaN/Inf/±0/subnormal、四种舍入、FP exception；位级结果与 FPSR/FPCR oracle | FP/SIMD Decode、Rename、Dispatch/ROB | SE |
| W9 | NEON-LaneProbe | 自设定向负载 | 8/16/32/64-bit lane、整数/浮点 AdvSIMD、lane extract/insert、widen/narrow、permute、reduce；逐 lane 比对 | FP/SIMD 三单元 | SE |
| W10 | PolyBench | 公开通用 | gemm、2mm、lu、cholesky、jacobi-2d；固定规模；输出数组逐元素/容差双校验 | FP/SIMD 三单元与长依赖链 | SE |
| W11 | libjpeg-turbo-NEON | 真实应用 | 固定图像做压缩/解压，启用 AArch64 NEON；逐像素、文件 hash 和格式合法性检查 | FP/SIMD 三单元 | SE/FS |
| W12 | SPEC CPU2017 SimPoint | 公开通用（需许可证） | 整数选 mcf/xalancbmk，浮点选 lbm/cam4；固定 SimPoint/checkpoint，主结论后复核 | 外部有效性 | SE/FS |
| W13 | FP-ExceptionRecovery | 自设定向负载 | FP invalid/div0/overflow/underflow/inexact 与分支误预测/精确异常交叉；检查 FPSR、目的寄存器和提交边界 | FP/SIMD Dispatch/ROB | FS |

## 接线状态〔提取注，派生自「7.展开执行矩阵」〕

- **已接入展开矩阵（11 个）**：W9=48 格；W5=42 格；W10=42 格；W8=38 格；W4=27 格；W6=25 格；W3=24 格；W7=21 格；W13=20 格；W11=12 格；W1=11 格。
- **已定义、未接入（3 个）**：W0（MiniCheck-OOO）、W12（SPEC CPU2017 SimPoint）、W2（BEEBS-DelayAVF）——「7.展开执行矩阵」310 格中无任何以之为负载的格。

