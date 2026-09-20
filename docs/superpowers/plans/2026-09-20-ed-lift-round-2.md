# ED Lift Round 2——gap 定向序列 + N≥400 + l2c 臂的 lift 重裁实施计划

> **For agentic workers:** 用 superpowers:subagent-driven-development（推荐）或 superpowers:executing-plans 逐任务实施。所有步骤用 `- [ ]` checkbox 跟踪。
> **纪律（CLAUDE.md）**：一补丁一单元 → 真机三步自验证（干净增量构建零新警告 + 功能验证引用真实输出 + 不相关回归）→ commit（无 Co-Authored-By 尾注）→ push `feat/sdc-ed-eval`。

**Goal:** 把 Round 1 lift 实验的三条负结果归因（功效不足 / 库存池 ED 差异在微权重轴 / L2C 主导 gap 无注入臂）一次性变现：用 gap 定向序列生成拉开 ED 序间差，补 l2c 注入臂，按 N≥400 功效预算重跑 lift 裁决——回答「ED 高的序列是否真的检测率更高」。

**前提实证（findings.md，2026-09-20）：**
1. 库存 10 负载 `l2cReads=0`（32KB 工作集全 L1D 命中）——ED 的 L2C 轴（quota=0.236 最大）在旧池上恒 0，**旧池结构上不可分辨**；
2. conflict_seq + `--mem-bytes 262144` 激活 L2（l2cReads=63、tagReads=211、LSU 轴 0.47）——定向路径现成；
3. l2c 注入臂（harp_eval --structure l2c_tag|l2c_data）与 6.1 标定协议现成；
4. 功效预算（lift-report §2）：分辨 2 倍 ED 差需 N≥400/序列。

**Architecture（实验设计，预注册）：**

```
高 ED 组（H，6 条）: gap 定向生成——L2C-tag 激活（>128KiB 足迹 + 同 tag
                     冲突）× LSU 前转密集 × IRF 长链，advice 规则驱动
低 ED 组（L，6 条）: 旧池代表（微 OoO 轴）+ 定向反例（死链/纯 int 短链）
裁决臂:             l2c_tag + l2c_data + irf × N=400/序列
判据（预注册，不许改）:
  J1 组级: H 组 detection > L 组（Wilson CI 不重叠）
  J2 AUC: AUC(ED, detection) > 0.5 且点估计 ≥ 0.7
  J3 轴级: H−L 的 lift 集中在 l2c_tag 臂（ED 预测的主导轴）
  若 J1-J3 失败: 残差归因表 + 功效复盘，负结果入档（同 Round 1 纪律）
```

**Tech Stack:** gem5.opt（现有构建）、Python 3 工具链（harp_wrap/harp_eval/ed_score/harp_advice）、AArch64 gcc。

**Spec（用户需求，2026-09-20 /planning-with-files 制定实现方案）:** 执行 lift-report.md §6 的杠杆 ①②③——evolve gap 定向序列 + N≥400 功效预算 + l2c 注入臂，重跑 lift 裁决。

---

## 一、任务分解（4 Phase / 12 任务，一补丁一单元）

### Phase 0 — 前置核对（臂-采集一致性）

- [ ] **Task 0.1 l2c 注入臂与采集器的配置一致性核对**
  内容: harp_eval l2c_* 臂走 `configs/se/arm_chaos_cache.py`（classic 层级 l2-cache-0），采集走 `two_level_taishan.py --cov-l2`（TS 私有 L2）——两套配置的 L2 容量/组织是否一致决定「注入面=采集面」。diff 两 config 的 L2 参数；不一致则统一（改 harp_eval 增 --l2-config 或改采集侧对齐）。
  验证: 两 config 的 L2 参数对照表落盘（容量/assoc/延迟/位置），一致或修正后一致；conflict_seq 在两 config 下 l2cReads 同量级。

### Phase 1 — gap 定向序列生成（拉开 ED 差）

- [ ] **Task 1.1 evolve 定向目标扩展（l2c/lsu/ed）**
  Files: `tools/harp_evolve.py`。
  内容: TARGETS 增加 `l2c`（key=l2cTagFaceRatio，规则=插入 `add x8,x8,4096; str xN,[x8]` 步进对扩足迹）与 `ed`（key=None，fitness 已支持——用 advice 的 L2C-tag 规则做定向步）。advice_step 增 l2c 分支。
  验证: 从 sample_seq 起 12 步 `--target l2c`：covUnits::L2C 单调上升（>0）；终态序列 l2cReads>0。
- [ ] **Task 1.2 高 ED 组（H6）生成与标定**
  内容: 用 Task 1.1 的定向 evolve + 手工模板（conflict_seq 派生）生成 6 条：足迹 >128KiB、前转对密集（str→ldr 同址）、IRF 长链混合。每条跑 --cov --cov-l2 记录 7 维 + ED。
  验证: H 组 ED 均值 ≥ 5×L 组；L2C/LSU 轴非零且组间分离（每轴 H 中位数 > L 最大值）。
- [ ] **Task 1.3 低 ED 组（L6）定案**
  内容: 旧池选 3（sample/dead_read/mul——Round 1 实测最低 ED 段）+ 定向反例 3（纯 int 短链、32KB 内工作集、死读链）。同协议测 7 维 + ED。
  验证: L 组 ED 与 H 组无重叠（或重叠 <1 对）；组间差全部写入实验登记表。

### Phase 2 — N=400 裁决战役（真值闭环）

- [ ] **Task 2.1 harp_eval 批量/断点支持核对**
  内容: 核对 --n 400 --jobs 16 的运行稳定性（Round 1 只跑过 50）；若单臂超时风险则加 --append 续跑模式（按已有 runs/ 目录跳过）。实测一个臂的 wall-time。
  验证: 单臂 N=400 完整落盘（无 SimulatorError 风暴）；wall-time 记录入 findings。
- [ ] **Task 2.2 l2c_tag × {H6, L6} × N=400**（J3 主臂）
  验证: 12 臂全部 summary.md 落盘，六类分布 + Wilson CI。
- [ ] **Task 2.3 l2c_data × {H6, L6} × N=400**（对照臂：data-face SECDED 下应近 0——臂有效性 sanity）
  验证: 同上；data 臂 detection 显著低于 tag 臂（复现 6.1 双面分化）。
- [ ] **Task 2.4 irf × {H6, L6} × N=400**（轴级对照：IRF 轴组间差应小于 l2c 轴——J3 的反向证据）
  验证: 同上。

### Phase 3 — 裁决与报告

- [ ] **Task 3.1 三判据计算与预注册裁决**
  内容: J1 组级 Wilson 检验、J2 AUC(ED, detection)（12 序列点）、J3 轴级 lift 分解（H−L per arm）。**判据不许改**；失败走残差归因。
  验证: 三判据各附计算脚本输出（真实数字）；无论成败如实入报告。
- [ ] **Task 3.2 `docs/sdc-ed/lift-report-round2.md` + 旧报告交叉引用**
  内容: Round 1 归因 → Round 2 设计 → 结果 → 裁决 → 残差（若有）；method.md §7 与 AGENT_TASKS 登记；本计划勾选收尾。
  验证: 双回归锚（reg_chain f247ef3fe6f02cfd + sample_seq SUM=17994817166615565002/CRC=8f333d15）+ 增量构建零新警告 + push。

## 二、验证命令速查

```bash
# 定向序列生成（Task 1.1-1.3）
python3 tools/harp_evolve.py --seq workloads/harp/sample_seq.S --target l2c \
    --steps 12 --fitness ed --out artifacts/sdc-ed-r2/evolve-l2c
CHAOS/gem5/build/ARM/gem5.opt --silent-redirect -d <dir> \
    smoke_test/configs/two_level_taishan.py --binary <seq> \
    --mode baseline --cov --cov-l2

# N=400 裁决臂（Task 2.x）
python3 tools/harp_eval.py --seq <seq> --structure l2c_tag --n 400 \
    --jobs 16 --out artifacts/sdc-ed-r2/harp-eval-l2c_tag-<seq>

# 回归锚
CHAOS/gem5/build/ARM/gem5.opt -r -e --silent-redirect -d /tmp/reg \
    smoke_test/configs/two_level_taishan.py \
    --binary workloads/directed/reg_chain --mode baseline   # f247ef3fe6f02cfd
```

## 三、风险与预案（预注册）

| 风险 | 缓解 |
|---|---|
| N=400×12 臂 ≈ 4800 runs 数小时 | jobs=16 分臂串行（臂间独立）；Task 2.1 实测单臂 wall-time 后再决定是否需要断点 |
| l2c 臂与采集配置不一致 | Task 0.1 前置核对（注入面≠采集面则 lift 无意义） |
| H 组 l2c 轴饱和后与其他轴耦合（LSU 0.47） | J3 用臂级差分（l2c_tag 臂 lift > irf 臂 lift）而非纯相关性 |
| 判据再次失败 | 残差归因 + 功效复盘入档；**不许改判据、不许事后选臂**（同 Round 1 纪律） |

## 四、与既有工作的关系

- 不推翻 Round 1：负结果与归因保留（lift-report.md §6 即本计划的输入）
- 复用全部现有资产：advice 规则引擎、conflict_seq 模板、--mem-bytes、l2c 臂、ed_score/ed_select、功效公式
- 本计划是 lift-report.md §6 杠杆 ①②③ 的打包执行；④（checker/golden 统一窗口）不在本轮
