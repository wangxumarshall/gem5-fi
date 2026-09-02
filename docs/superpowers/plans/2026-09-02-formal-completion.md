# formal-paper-tools 计划收尾实施计划（T4 收尾 / T5 / T6 / T8）

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 完成 `docs/superpowers/plans/2026-09-02-formal-paper-tools.md` 中未执行的 4 个任务：T4 LSQ 矩阵收尾（补齐中断的 phase/stale cell）、T5 method1 F5 两臂正式数据集、T6 论文 t3/t4 数据表回填、T8 progress.md 与方案文档收尾。

**Architecture:** 三段串行：①T4 补跑（fp_fwd_kernel 5 模式矩阵的 phase cell 全缺、stale cell 缺 18 rep——续跑 `tools/fp_fwd_matrix_batch.sh` 补齐后汇总提交）→ ②T5 method1 formal（提交已修正的 campaign YAML → 冒烟 n=10 确认注入非零 → 两臂 n=384 × 4 cell → Fisher 判定）→ ③T6/T8 论文表与文档回填。T6 依赖 T4/T5 的数据产物。

**Tech Stack:** gem5 v25.1.0.1（`CHAOS/gem5/build/ARM/gem5.opt`，1.1GB 已存在）、Python 3.11（campaign.py/runner.py/fisher_test.py/report.py）、bash batch 脚本、Markdown 论文。

**Spec:** `docs/superpowers/plans/2026-09-02-formal-paper-tools.md`（Task 4/5/6/8）；权威方案 `docs/KUNPENG920-的SDC故障的微架构故障注入和规律研究的详细方案设计和需求开发实现文档.md` §5.2（method1 H 验收）/§5.4E（LSQ 矩阵）。

## 执行前必读的现状事实（已核实，2026-09-02）

1. **T4 已中途改向**：原计划"3 几何 × 5 模式"（`tools/lsq_matrix_batch.sh` + fwd_7case 二进制）执行中发现 **fwd_7case 的 C 模式（volatile 无 asm barrier）在 -O2 下根本不触达 store→load 转发路径**（注入日志 0 字节、输出==golden）——已诚实废弃该轴，改用 `fp_fwd_kernel`（asm back-to-back，已证 fails=1 锚点）。新脚本 `tools/fp_fwd_matrix_batch.sh` **未提交**（untracked）。
2. **fpfwd 矩阵当前进度**（`artifacts/lsq-matrix/fpfwd_*.csv`）：
   - `fpfwd_bitflip.csv` 64/64 ✅（SDC=64）
   - `fpfwd_structural.csv` 64/64 ✅（SDC=64）
   - `fpfwd_fwdsrc.csv` 64/64 ✅（Masked=64，注入日志确认 `numFwdSourceSub` 位置注入发生但 fails=0——诚实数据：fp_fwd_kernel 同址反复转发，替换源后 ring buffer 里仍是同 vaddr 数据）
   - `fpfwd_stale.csv` **46/64**（中断；rep 0–45 全 Masked；r_fp_stale_46 目录存在且注入日志有 1 次注入但无输出——该 rep 结果无效需重跑）
   - `fpfwd_phase.csv` **0/64**（完全未跑；r_fp_phase_* 目录不存在）
   - 判据是 fail_count oracle（`fails>0 → SDC`），不依赖 golden hash；`goldens.txt` 中 `fp_fwd` 行为空（无 golden，按 fails 判定）——该文件已有一行未提交修改（`+fp_fwd `），提交时保留。
3. **T5 未开始**：`campaigns/method1-f5-cholesky-formal.yaml` 的参数修正（trigger 50000→2000、target_arch [-1]→[0,1,2,3]）已改但**未提交**；m1-smoke2 不存在；两臂 formal 未跑。
4. **T6 半完成**：`docs/paper/sdc-fi-paper.md` 骨架完整（`1ad1b1bb`），但 §4.3 引用的 `tables/t3-lsq-matrix.md` 不存在（正文写"3 几何（same/twocand/ldxr）× 5 模式"——**与新范围 fp_fwd 5 模式不符，需改写**）、§4.4 引用的 `tables/t4-method1-fisher.txt` 不存在；`docs/paper/tables/t1-prf.csv` untracked（report.py 产物，与已提交的 t1-prf.md 同源）。
5. **预算实测**：fp_fwd_kernel 单 run 秒级（simSeconds 0.001，host 端 ~5–15s）；cholesky 10-iters O3 单 run ~25s；T5 两臂 = 384×4cell×2 = 3072 runs × 25s / 8 jobs ≈ **2.7 小时**（plan 原估 5.5h 偏保守）。机器 128 核 29GB（jobs=8 上限，禁更高——历史 OOM 教训用 -j16/jobs=8）。
6. gem5.opt 在 `CHAOS/gem5/build/ARM/gem5.opt`（仓库根 `build/` 不存在此文件，**用 CHAOS 路径**）。

## Global Constraints

- 运行前必 `source /home/sdc/gem5-deps/env.sh`；G5=`$PWD/CHAOS/gem5/build/ARM/gem5.opt`
- 长任务（>5 分钟）一律 run_in_background；jobs=8 上限
- 提交纪律：一补丁一单元 + 真机验证引用实际输出 + `git push origin fi-wangxu` + **无 "Co-Authored-By: Claude" 尾注**
- 诚实纪律：Masked=64（fwdsrc/stale）是真实数据如实入表，不得粉饰；Fisher 若 FAIL-insufficient-n 如实输出；所有 P_SDC 标注"gem5 O3 代理条件概率，非 FIT"
- 论文每个数字必须溯源到 `artifacts/<campaign>/` 具体文件——禁止手写未溯源数字
- 注入器代码已冻结（17 个，不改 .cc/.hh）

---

### Task 1: T4 收尾——补齐 fpfwd 矩阵 phase/stale cell 并提交

**Files:**
- Modify: `tools/fp_fwd_matrix_batch.sh`（加续跑支持）
- Create: `artifacts/lsq-matrix/fpfwd_phase.csv`（64 行）
- Modify: `artifacts/lsq-matrix/fpfwd_stale.csv`（46→64 行）
- Create: `artifacts/lsq-matrix/summary.md`（矩阵汇总表）
- Create: `docs/paper/tables/t3-lsq-matrix.md`（论文表 3）

**Interfaces:**
- Consumes: `tools/fp_fwd_matrix_batch.sh` 的 MODE_ARGS 判定逻辑（`fails>0→SDC, fails=0→Masked, 空→Hang`）；`artifacts/lsq-matrix/fpfwd_*.csv` 的 schema `rep,seed,fails,class`
- Produces: `summary.md` 含 5 模式 × {SDC, Masked, Hang} 计数表；`t3-lsq-matrix.md` 同表（论文格式）——Task 3 的论文 §4.3 改写引用它

- [x] **Step 1: 修改 batch 脚本支持单模式续跑**

把 `tools/fp_fwd_matrix_batch.sh` 的模式循环改为可参数化（第一个参数若在 {bitflip,structural,fwdsrc,stale,phase} 内则只跑该模式），并让 stale 续跑时**跳过 csv 已有的 rep**（追加式，不重写 header）：

```bash
# 修改后的关键部分（完整替换 for mode in ... 循环）：
MODES="${1:-all}"; N="${2:-64}"; JOBS="${3:-8}"
if [ "$MODES" = "all" ]; then MODES="bitflip structural fwdsrc stale phase"; fi
for mode in $MODES; do
  out="$OUT/fpfwd_${mode}.csv"
  if [ ! -f "$out" ]; then echo "rep,seed,fails,class" > "$out"; fi
  # 找已有最大 rep
  done_reps=$(tail -n +2 "$out" | awk -F, '{print $1}' | sort -n | tr '\n' ' ')
  for ((i=0;i<N;i++)); do
    # 跳过已有 rep（stale 0-45 已有）
    case " $done_reps " in *" $i "*) continue;; esac
    ...（原 run 逻辑不变：seed=$((20260825 + i))，grep fails，class 判定，追加 csv）
  done
  wait
done
```

同时把原脚本头部 `N="${1:-64}"; JOBS="${2:-8}"` 的位置参数语义更新为 `MODES/N/JOBS`（旧调用 `bash tools/fp_fwd_matrix_batch.sh 64 8` 的兼容性不需保留——这是未提交脚本，无历史调用方）。

- [x] **Step 2: 补跑 stale 剩余 18 rep + phase 64 rep**

```bash
cd /home/sdc/wangxu/gem5-fi-wangxu
source /home/sdc/gem5-deps/env.sh
export G5=$PWD/CHAOS/gem5/build/ARM/gem5.opt
# stale 续跑（跳过 0-45，补 46-63）+ phase 全跑，后台 ~20 分钟
bash tools/fp_fwd_matrix_batch.sh stale 64 8 && bash tools/fp_fwd_matrix_batch.sh phase 64 8
```

注意：r_fp_stale_46 目录残留（上次中断的半成品）——续跑会重新写入该目录（gem5 --outdir 覆盖），无需手动清理。

- [x] **Step 3: 校验 5 个 csv 全部 64 行且 class 合法**

```bash
for f in artifacts/lsq-matrix/fpfwd_*.csv; do
  n=$(tail -n +2 "$f" | wc -l)
  bad=$(tail -n +2 "$f" | awk -F, '$4!~/^(SDC|Masked|Hang)$/' | wc -l)
  echo "$f: rows=$n badclass=$bad"
done
# 预期：5 个文件全部 rows=64 badclass=0
```

- [x] **Step 4: 生成 summary.md + 论文表 t3**

```bash
{
echo "# LSQ 转发故障模式矩阵（fp_fwd_kernel，n=64/cell，O3，first_clock=1e6，max_faults=1）"
echo ""
echo "> 判据：fail_count oracle（fails>0→SDC）。7 几何轴（fwd_7case）已诚实废弃：其 volatile-no-barrier C 模式在 -O2 下不触达转发路径（注入日志 0 字节）。"
echo ""
echo "| 故障模式 | SDC | Masked | Hang | P_SDC |"
echo "|---|---|---|---|---|"
for mode in bitflip structural fwdsrc stale phase; do
  f=artifacts/lsq-matrix/fpfwd_${mode}.csv
  s=$(tail -n +2 $f | awk -F, '$4=="SDC"' | wc -l)
  m=$(tail -n +2 $f | awk -F, '$4=="Masked"' | wc -l)
  h=$(tail -n +2 $f | awk -F, '$4=="Hang"' | wc -l)
  awk -v s=$s -v mode=$mode 'BEGIN{printf "| %s | %d | %d | %d | %.3f |\n", mode, s, m, h, s/64}'
done
echo ""
echo "> All P_SDC are gem5-proxy conditional probabilities, NOT product FIT."
} | tee artifacts/lsq-matrix/summary.md
cp artifacts/lsq-matrix/summary.md docs/paper/tables/t3-lsq-matrix.md
```

预期结果（基于已有 3 cell 数据的趋势）：bitflip/structural SDC≈64/64；fwdsrc/stale Masked=64/64（注入发生但同址转发数据等价——诚实阴性）；phase 待实测。

- [x] **Step 5: 提交（脚本 + 数据 + 论文表）**

```bash
git add tools/fp_fwd_matrix_batch.sh artifacts/lsq-matrix/fpfwd_*.csv \
  artifacts/lsq-matrix/summary.md artifacts/lsq-matrix/goldens.txt \
  docs/paper/tables/t3-lsq-matrix.md
# 注意：不 add artifacts/lsq-matrix/run_*/ 与 r_fp_*/（中间产物不入库）；先检查 .gitignore 是否已排除，若未排除则用 git add 精确路径（上面的 fpfwd_*.csv 已是精确文件）
git commit -m "formal-T4: LSQ 故障模式矩阵（fp_fwd_kernel 5 模式 × n=64，method3）

7 几何轴诚实废弃：fwd_7case volatile-no-barrier 在 -O2 不触达转发路径
（注入日志 0 字节）；改用 fp_fwd_kernel（asm back-to-back，fails=1 锚点）。
（引用 summary.md 实际矩阵：bitflip/structural SDC 率、fwdsrc/stale 同址
Masked 阴性、phase 实测值）"
git push origin fi-wangxu
```

---

### Task 2: T5——method1 F5 两臂正式数据集

**Files:**
- Modify: `campaigns/method1-f5-cholesky-formal.yaml`（已改好未提交——trigger 2000 + target_arch [0,1,2,3]）
- Create: `artifacts/m1-smoke2/cells.csv`（冒烟）
- Create: `artifacts/m1-formal-num/cells.csv`、`artifacts/m1-formal-both/cells.csv`（两臂）
- Create: `artifacts/m1-formal-verdict.txt`（Fisher 判定）
- Create: `docs/paper/tables/t4-method1-fisher.txt`（论文表 4）

**Interfaces:**
- Consumes: `tools/campaign.py`（`--n-per-cell/--jobs/--workload-args/--hang-timeout/--gem5/--artifacts`）；`tools/fisher_test.py`（两 cells.csv → Fisher p + ratio + Wilson）；cholesky 的 fail_count oracle（stderr `iters=N fails=M variant=...`，runner 解析）
- Produces: verdict.txt 的格式由 fisher_test.py 输出决定（P(per-arm SDC)、Fisher p、ratio 与 [2,8] 判定）——Task 3 论文 §4.4 直接引用

**关键前置认知**：pilot（`artifacts/method1-num2`）随机 FP 类 F5 在 0/10 SDC 的根因是"随机全类大多命中非活跃映射 + first_clock=50000 过晚"。修正 = 定向 V0-V7 + first_clock=2000。**若冒烟仍 0/10**：进一步定向 V0-only（target_arch: [0]，d0 主累加器）再冒烟一次；若 V0-only 仍 0，如实记录"该 kernel 下 F5 V0-V7 不达 SDC"并以实际数据跑 formal（阴性也是数据——method1 复现失败要如实写）。

- [x] **Step 1: 提交已修正的 campaign YAML（单独补丁，先于数据）**

```bash
git add campaigns/method1-f5-cholesky-formal.yaml
git commit -m "formal-T5a: method1 formal YAML 参数修正（pilot 0/10 根因）

trigger 50000→2000（cholesky 10-iters 数值段内）+ target_arch [-1]→[0,1,2,3]
定向 V0-V7 低段（d0 累加器所在；随机全类大多命中非活跃映射）。"
git push origin fi-wangxu
```

- [x] **Step 2: 冒烟 n=10 确认注入非零**

```bash
cd /home/sdc/wangxu/gem5-fi-wangxu
source /home/sdc/gem5-deps/env.sh
G5=$PWD/CHAOS/gem5/build/ARM/gem5.opt
python3 tools/campaign.py campaigns/method1-f5-cholesky-formal.yaml \
  --binary workloads/directed/cholesky_numeric --workload-golden 0 \
  --n-per-cell 10 --jobs 8 --hang-timeout 400 --workload-args "10" \
  --gem5 "$G5" --artifacts artifacts/m1-smoke2 2>&1 | tail -6
cat artifacts/m1-smoke2/cells.csv | head -5
```

判定：cells.csv 的 SDC 列或 first_run_class 出现非 Masked（SDC）即参数修正生效；若仍全 Masked，按上面"关键前置认知"降级到 V0-only 再冒烟（修改 yaml 的 target_axes 后重复本步，两个 YAML 版本都在 commit 历史里可见）。

- [x] **Step 3: 两臂正式跑（n=384 × 4 cell × 2，后台 ~3 小时 jobs=8）**

```bash
# 臂1 numeric（run_in_background）
python3 tools/campaign.py campaigns/method1-f5-cholesky-formal.yaml \
  --binary workloads/directed/cholesky_numeric --workload-golden 0 \
  --n-per-cell 384 --jobs 8 --hang-timeout 400 --workload-args "10" \
  --gem5 "$G5" --artifacts artifacts/m1-formal-num 2>&1 | tail -8
# 臂1 完成后跑臂2 compute-both
python3 tools/campaign.py campaigns/method1-f5-cholesky-formal.yaml \
  --binary workloads/directed/cholesky_numeric --workload-golden 0 \
  --n-per-cell 384 --jobs 8 --hang-timeout 400 --workload-args "10 both" \
  --gem5 "$G5" --artifacts artifacts/m1-formal-both 2>&1 | tail -8
```

注意：campaign.py 两臂串行执行（同时跑会超 8 jobs 内存预算）；每臂 4 cell（V0/V1/V2/V3 各 384 rep）× 25s ≈ 1.3 小时。

- [x] **Step 4: Fisher 正式检验**

```bash
python3 tools/fisher_test.py artifacts/m1-formal-num/cells.csv \
  artifacts/m1-formal-both/cells.csv | tee artifacts/m1-formal-verdict.txt
cp artifacts/m1-formal-verdict.txt docs/paper/tables/t4-method1-fisher.txt
```

判定标准（plan §5.2 H 验收）：P(history_residue)>0 且 Fisher p<0.05 才算 method1 复现成立；ratio ∈ [2,8] 对照现场 1.0%/0.27%。**若 p≥0.05 或 SDC=0，verdict 如实记录 FAIL/insufficient——这是诚实结论，照样入论文（"本代理下未能复现 4× 比值"是有效负结果）。**

- [x] **Step 5: 提交**

```bash
git add campaigns/method1-f5-cholesky-formal.yaml artifacts/m1-formal-num/cells.csv \
  artifacts/m1-formal-both/cells.csv artifacts/m1-formal-verdict.txt \
  docs/paper/tables/t4-method1-fisher.txt
# cells.csv 若过大（>10MB）检查 git 可容；manifests/ 中间件不入库
git commit -m "formal-T5: method1 F5 两臂正式数据集（V0-V7 定向 × n=384 × 2 臂）

（引用 verdict.txt 实际 p 值/ratio——§5.2 H 验收判定；若 FAIL 如实写）"
git push origin fi-wangxu
```

---

### Task 3: T6——论文 §4.3/§4.4 回填 + t1-prf.csv 入库

**Files:**
- Modify: `docs/paper/sdc-fi-paper.md`（§4.3 改写为 fp_fwd 5 模式；§4.4 填 Fisher 实际结果；摘要与结论的"4 组正式数据集"表述核对）
- Add: `docs/paper/tables/t1-prf.csv`（untracked 的 report.py 产物）

**Interfaces:**
- Consumes: Task 1 的 `t3-lsq-matrix.md`（5 模式矩阵表）；Task 2 的 `t4-method1-fisher.txt`（Fisher verdict）
- Produces: 论文 §4.3/§4.4 完整可投稿文本（每个数字溯源 tables/）

- [x] **Step 1: 改写 §4.3（旧文本引用了废弃的 3 几何轴）**

把论文 §4.3 当前占位段落：

```markdown
### 4.3 LSQ 转发几何×模式矩阵（表 3——T4 数据）

3 几何（same/twocand/ldxr）× 5 模式 × n=64（见 tables/t3 与 artifacts/lsq-matrix/）。
```

替换为（数字从 t3-lsq-matrix.md 机械抄录，bitflip/structural 用实际值；fwdsrc/stale 的阴性如实写）：

```markdown
### 4.3 LSQ 转发故障模式矩阵（表 3——T4 数据）

fp_fwd_kernel（asm back-to-back store→load）× 5 故障模式 × n=64（tables/t3-lsq-matrix.md）：
bitflip 与 structural（byte_lane_skew rol1）SDC 率 <实际值>；fwd_source_sub 与
stale_line_replay 为 Masked 阴性（注入确认发生——numFwdSourceSub/numStaleLineReplay
计数=1——但 fp_fwd_kernel 的同址转发使替换源数据等价，fails=0）；phase_offset(N=2)
<实际值>。**诚实边界**：原计划的 fwd_7case 7 几何轴被废弃——其 volatile-no-barrier
C 模式在 -O2 下不触达 gem5 转发路径（注入日志 0 字节），矩阵降为单几何 × 5 模式。
```

- [x] **Step 2: 回填 §4.4（Fisher 实际结果）**

把占位：

```markdown
### 4.4 method1 状态泄漏 Fisher 判定（表 4——T5 数据）

V0–V7 定向 F5 × n=384 × 2 臂（numeric/compute-both），Fisher exact（见 tables/t4）。
```

替换为引用 verdict.txt 实际数字的完整段落（p 值、两臂 P_SDC、ratio 与 [2,8] 判定；若 FAIL 如实写负结果及原因分析——单 kernel 代理与现场 256 规模差异）。

- [x] **Step 3: 核对摘要/结论的"4 组正式数据集"表述**

摘要与结论当前写"③LSQ 转发几何×故障模式矩阵"——与新范围（单几何 5 模式）不符，改为"③LSQ 转发故障模式矩阵"。逐处检查 `grep -n "几何" docs/paper/sdc-fi-paper.md` 并同步。

- [x] **Step 4: 数字溯源自查 + 提交**

```bash
# 自查：§4.3/§4.4 的每个数字能在 t3/t4 表中找到
grep -oE "[0-9]+\.[0-9]+%|[0-9]+/64|p=[0-9.]+" docs/paper/sdc-fi-paper.md | head -20
# 人工比对 t3-lsq-matrix.md / t4-method1-fisher.txt
git add docs/paper/sdc-fi-paper.md docs/paper/tables/t1-prf.csv
git commit -m "paper-T6: 论文 §4.3/§4.4 回填正式数据（LSQ 矩阵 + method1 Fisher）

§4.3 改写为 fp_fwd 5 模式矩阵（3 几何轴废弃诚实标注）；§4.4 填 Fisher
verdict 实际 p/ratio；摘要/结论'几何×模式'表述同步。t1-prf.csv 入库。"
git push origin fi-wangxu
```

---

### Task 4: T8——progress.md 收尾 + 方案文档假设表回填

**Files:**
- Modify: `progress.md`（追加本轮 4 任务产物段）
- Modify: `docs/KUNPENG920-SDC研究方案-系统完备版.md`（§6.1 假设表若有"待 formal"项回填 verdict 引用）
- Modify: `docs/superpowers/plans/2026-09-02-formal-paper-tools.md`（勾选已完成 checkbox）

**Interfaces:**
- Consumes: Task 1–3 的全部产物路径
- Produces: 文档最终状态（无未提交工作树残留）

- [x] **Step 1: progress.md 追加本轮段落**

按 progress.md 既有格式（`## 本轮（2026-09-02）formal 计划收尾：T4/T5/T6/T8`）记录：T4 几何轴废弃原因 + 5 模式矩阵实际值；T5 冒烟→两臂→Fisher verdict（含 FAIL 时的诚实记录）；T6 论文表回填；每项附 commit hash。

- [x] **Step 2: 方案文档假设表回填**

```bash
grep -n "待 formal\|H8" docs/KUNPENG920-SDC研究方案-系统完备版.md | head -10
# 找到 §6.1 假设表的"待 formal"行，把已产出的（H0 L1D 风险反转已闭环——T2 先前已提交；
# method1 相关行）改为引用 artifacts/<campaign>/summary.md 或 verdict.txt
```

只回填**本次产出支撑的行**（T4 矩阵、T5 Fisher）；其余"待 formal"保持原状（诚实——没跑的不改）。

- [x] **Step 3: 勾选 2026-09-02 计划的 checkbox**

把 `docs/superpowers/plans/2026-09-02-formal-paper-tools.md` 中 Task 1–8 已完成步骤的 `- [ ]` 改 `- [x]`（T1/T2/T3/T7 在先前 commit 已完成但 checkbox 未勾——一并补勾；T4/T5/T6/T8 本轮完成）。

- [x] **Step 4: 提交 + 最终状态核查**

```bash
git add progress.md docs/KUNPENG920-SDC研究方案-系统完备版.md \
  docs/superpowers/plans/2026-09-02-formal-paper-tools.md
git commit -m "docs: formal 计划收尾（T4 矩阵 + T5 Fisher + T6 论文回填 + T8 状态）

§6.1 假设表回填本次产出支撑的行；progress 记录 4 任务产物；
2026-09-02 计划 checkbox 全勾。"
git push origin fi-wangxu
git status --short   # 预期：仅剩 docs/KUNPENG920-的SDC...md（用户手写文档，不属本计划）
```

---

## Self-Review 结论

**1. 覆盖检查**：T4（补 phase/stale + 汇总 + 提交脚本）→ Task 1；T5（YAML 提交→冒烟→两臂→Fisher→提交）→ Task 2；T6（§4.3/§4.4 回填 + t1-prf.csv）→ Task 3；T8（progress + 假设表 + checkbox）→ Task 4。原计划 T1/T2/T3/T7 已在先前 commit 完成，不重复。

**2. 占位符扫描**：无 TBD。Task 1 Step 4 的"phase 待实测"与 Task 2 Step 2 的"若仍 0/10 降级 V0-only"是条件指令（数据依赖分支），非占位——降级路径的具体命令已给出（改 yaml target_axes 重复冒烟）。

**3. 类型一致性**：fpfwd csv schema（`rep,seed,fails,class`）与已有 4 个文件一致；fisher_test.py 输入（两 cells.csv 的 SDC/n_valid 列）与 campaign.py 产物 schema 一致（已用 method1-num2/cells.csv 核实列名）；t3/t4 表文件名与论文 §4.3/§4.4 引用一致。

**预算**：Task 1 ~20 分钟（后台）；Task 2 冒烟 ~10 分钟 + 两臂 ~3 小时（后台，期间可做 Task 1 的汇总与 Task 3 的文本准备）；Task 3/4 各 ~15 分钟。总计墙钟 ~4 小时（大部分后台）。
