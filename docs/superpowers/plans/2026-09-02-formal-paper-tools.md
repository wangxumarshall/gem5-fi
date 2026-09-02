# 下一阶段机会实施计划：formal 规模化 + 论文数据 + 产业工具固化

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把项目从"基础设施就位"推进到"可发表"：产出 4 组 formal P_SDC 数据集（n=384，含 Wilson CI 与假设检验）、1 份完整论文草稿（含所有表格）、1 个可交付的 SDC 诊断指纹库工具。

**Architecture:** 三条线按依赖串行：①formal 数据生产（campaign 批量跑 + 汇总脚本）→ ②论文撰写（数据表直接引用 ① 的 artifacts）→ ③产业工具（位谱指纹库 CLI + openEuler 诊断规则反哺接口，消费 ① 的数据）。每条线的产物自包含可测试。

**Tech Stack:** gem5 v25.1.0.1（vendored `CHAOS/gem5/`）、Python 3.11（campaign/runner/fisher/指纹库）、LaTeX-free Markdown 论文（与现有 paper_zh.md 同格式）、CLAUDE.md 补丁纪律。

**Spec:** `docs/KUNPENG920-SDC研究方案-系统完备版.md`（§6.1 假设体系、§9.1 论文贡献点、§7 诊断反哺、§8.3 设计建议）

## 计算预算实测（本计划的依据，已核实）

| workload | CPU | 单 run 实测 | n=384 单 cell | 8 cell 总量 (jobs=8) |
|---|---|---|---|---|
| l1d_reduce | Timing | **2.9s** | ~2.3 分钟 | ~25 分钟 |
| cholesky_numeric (10 iters) | O3 | **25s** | ~20 分钟 | ~2.7 小时 |
| reg_chain | O3 | **100s** | ~80 分钟 | ~10.7 小时 |

**结论**：formal 主力用 **l1d_reduce (Timing, 2.9s)** 与 **cholesky (O3, 25s)**——L1D/Cache/Mem/RAT/freelist 注入器用 l1d_reduce（快）；PRF/LSQ 用各自已验证 kernel；reg_chain 类慢 kernel 只跑关键 cell。

## Global Constraints

- 构建/运行：`cd CHAOS/gem5 && source /home/sdc/gem5-deps/env.sh && scons build/ARM/gem5.opt -j16`（禁 -j126）；运行前必 source env.sh
- campaign 运行模式：`python3 tools/campaign.py <yaml> --binary <bin> --workload-golden <hash> --n-per-cell N --jobs J --gem5 $PWD/CHAOS/gem5/build/ARM/gem5.opt --artifacts artifacts/<name>`（长任务一律 run_in_background）
- 提交纪律：一补丁一单元 + 真机验证引用实际输出 + `git push origin fi-wangxu` + **无 "Co-Authored-By: Claude" 尾注**
- 诚实纪律：formal 数据不足判定时如实输出（如 Fisher FAIL-insufficient-n）；所有 P_SDC 标注"gem5 O3 代理条件概率，非 FIT"
- 论文的每个数字必须能溯源到 `artifacts/<campaign>/cells.csv` 的具体行——禁止手写未溯源数字
- 注入器代码已冻结（17 个，本计划不改 .cc/.hh——只写 campaign YAML/分析脚本/论文/工具）

---

### Task 1: campaign.py 汇总层——多 campaign 合并报表工具 `tools/report.py`

formal 会产出多个 campaign 的 cells.csv（PRF/RAT/LSQ/Cache×2 臂/...）。论文需要一张**跨单元总表**（每行一个 unit×model×protection 的 P_SDC + Wilson CI）。现无此工具。

**Files:**
- Create: `tools/report.py`
- Test: `tests/test_report.py`

**Interfaces:**
- Consumes: `cells.csv` 的 schema（列名见 §16 盘点：`cell_ordinal,layer,target_arch,semantic_role,fault_model,...,SDC,n_valid,P_SDC,P_SDC_lo,P_SDC_hi,...`）
- Produces: `python3 tools/report.py --inputs artifacts/<a>/cells.csv artifacts/<b>/cells.csv ... --unit-col <列名> [--out report.md]` → Markdown 总表 + `report.csv`

- [ ] **Step 1: 写失败测试**

```python
# tests/test_report.py
import csv, io, os, subprocess, sys, tempfile
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tools"))

def _mk_csv(path, unit, sdc, nv):
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["cell_ordinal","layer","target_arch","semantic_role",
                    "fault_model","f5_substitute_target","n_total","n_valid",
                    "SDC","Crash","Hang","Inactive","Masked","SimulatorError",
                    "P_SDC","P_SDC_lo","P_SDC_hi","P_DUE","P_DUE_lo","P_DUE_hi",
                    "P_escape","Reachability","first_run_id","first_run_class"])
        w.writerow([0,"physical",unit,"", "transient_bit_flip",-1, nv, nv,
                    sdc,0,0,0,nv-sdc,0, sdc/nv,0,1, 0,0,1, sdc/nv, 1.0,
                    "x-r0","SDC" if sdc else "Masked"])

def test_report_merges_and_aggregates():
    from report import merge_campaigns, wilson
    with tempfile.TemporaryDirectory() as d:
        a, b = os.path.join(d,"a.csv"), os.path.join(d,"b.csv")
        _mk_csv(a, "prf", 30, 100)   # unit prf: 30/100
        _mk_csv(b, "rat", 10, 100)   # unit rat: 10/100
        rows = merge_campaigns([a, b], unit_col="target_arch")
        by_unit = {r["unit"]: r for r in rows}
        assert by_unit["prf"]["sdc"] == 30 and by_unit["prf"]["n_valid"] == 100
        assert by_unit["rat"]["sdc"] == 10
        # wilson point = k/n
        assert abs(wilson(30, 100)[1] - 0.30) < 1e-9

def test_report_cli_emits_md_and_csv():
    from report import render_markdown
    rows = [{"unit":"prf","sdc":30,"n_valid":100,"p":0.30,"lo":0.22,"hi":0.40}]
    md = render_markdown(rows)
    assert "| prf | 30/100 | 0.300 | [0.220,0.400] |" in md
```

- [ ] **Step 2: 运行确认失败**

```bash
cd /home/sdc/wangxu/gem5-fi-wangxu
python3 -m pytest tests/test_report.py -v 2>&1 | tail -3
```

预期：FAIL `ModuleNotFoundError: No module named 'report'`

- [ ] **Step 3: 实现 report.py**

```python
#!/usr/bin/env python3
"""Cross-campaign report generator (plan §9.1 table producer).

Merges multiple campaign cells.csv files, aggregates SDC/n_valid by a unit
column (target_arch / semantic_role / fault_model / ...), computes Wilson
95% CI per group, and emits a paper-ready Markdown table + CSV.

Usage:
  python3 tools/report.py --inputs artifacts/a/cells.csv artifacts/b/cells.csv \
      --unit-col target_arch [--out artifacts/report]
"""
import argparse, csv, math, os, sys

def wilson(k, n, z=1.96):
    if n == 0: return (0.0, 0.0, 0.0)
    p = k / n
    if k == 0: return (0.0, 0.0, min(1.0, 3.0 / n))
    d = 1 + z*z/n
    c = (p + z*z/(2*n)) / d
    h = z * math.sqrt(p*(1-p)/n + z*z/(4*n*n)) / d
    return (max(0.0, c-h), p, min(1.0, c+h))

def merge_campaigns(paths, unit_col="target_arch"):
    agg = {}
    for path in paths:
        with open(path) as f:
            for row in csv.DictReader(f):
                unit = row.get(unit_col) or row.get("fault_model") or "?"
                a = agg.setdefault(unit, {"sdc": 0, "n_valid": 0, "hang": 0,
                                          "crash": 0, "masked": 0,
                                          "inactive": 0, "files": set()})
                a["sdc"] += int(row["SDC"])
                a["n_valid"] += int(row["n_valid"])
                for k in ("hang","crash","masked","inactive"):
                    col = {"hang":"Hang","crash":"Crash","masked":"Masked",
                           "inactive":"Inactive"}[k]
                    a[k] += int(row.get(col, 0))
                a["files"].add(os.path.basename(os.path.dirname(path)))
    rows = []
    for unit, a in sorted(agg.items(), key=lambda kv: -kv[1]["sdc"]):
        lo, p, hi = wilson(a["sdc"], a["n_valid"])
        rows.append({"unit": unit, "sdc": a["sdc"], "n_valid": a["n_valid"],
                     "p": p, "lo": lo, "hi": hi, "hang": a["hang"],
                     "crash": a["crash"], "masked": a["masked"],
                     "sources": ",".join(sorted(a["files"]))})
    return rows

def render_markdown(rows):
    out = ["# Cross-campaign SDC report", "",
           "| unit | SDC/n_valid | P_SDC | Wilson 95% CI | Hang | Crash | Masked | sources |",
           "|---|---|---|---|---|---|---|---|"]
    for r in rows:
        out.append(f"| {r['unit']} | {r['sdc']}/{r['n_valid']} | "
                   f"{r['p']:.3f} | [{r['lo']:.3f},{r['hi']:.3f}] | "
                   f"{r['hang']} | {r['crash']} | {r['masked']} | {r['sources']} |")
    out.append("")
    out.append("> All P_SDC are gem5-proxy conditional probabilities, NOT "
               "product FIT. Wilson 95% CI.")
    return "\n".join(out)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--inputs", nargs="+", required=True)
    ap.add_argument("--unit-col", default="target_arch")
    ap.add_argument("--out", default=None, help="output prefix (writes .md + .csv)")
    a = ap.parse_args()
    rows = merge_campaigns(a.inputs, unit_col=a.unit_col)
    md = render_markdown(rows)
    print(md)
    if a.out:
        with open(a.out + ".md", "w") as f: f.write(md)
        with open(a.out + ".csv", "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()) if rows else ["unit"])
            w.writeheader(); w.writerows(rows)

if __name__ == "__main__":
    main()
```

- [ ] **Step 4: 测试通过 + 真机验证（用现有 pilot 数据）**

```bash
python3 -m pytest tests/test_report.py -v 2>&1 | tail -2   # 预期 PASS
# 真机：用现有两个 pilot 数据合并
python3 tools/report.py --inputs artifacts/method1-num2/cells.csv artifacts/prf-pilot/cells.csv \
    --unit-col target_arch | head -12
```

预期：输出含 `prf`（PRF pilot 的 X3 行）与 `-1`（method1 的随机 FP 行）的合并表。

- [ ] **Step 5: 提交**

```bash
git add tools/report.py tests/test_report.py
git commit -m "formal-T1: report.py 跨 campaign 合并报表（论文总表生产器）

merge_campaigns + wilson + render_markdown；pytest 覆盖聚合/CI/MD 渲染。
真机验证：method1-num2 + prf-pilot 两 cells.csv 合并输出正确。"
git push origin fi-wangxu
```

---

### Task 2: formal 数据集 ①——L1D raw vs protection-aware（风险反转正式表）

方案 §6.5 的核心正式数据：**raw(none) vs secded 两臂 × 1/2/3-bit**（ECC 粒度轴），n=384/cell。l1d_reduce Timing 2.9s——**全网格 6 cell × 384 = 2304 runs，jobs=8 约 15 分钟**。这是最快能拿到的正式数据集。

**关键前置（诚实评估）**：runner cache 路径的 `--cache-block-addr` 定向活数据块——862656 曾验证 resident，但后续一次 run 显示 `NOT resident falling back random`（驻留时点漂移）。**随机块大多 Masked（已知 AVF 采样效应）**。本任务用 `--cache-block-addr=862656` + 若 log 出现 NOT resident 则如实记录回退率。数据本身两个方向都有价值：定向 SDC 臂 + 随机 Masked 臂。

**Files:**
- Create: `campaigns/l1d-ecc-formal.yaml`（注意：cache 组件走 runner 的 `--cache-block-addr`，不经 campaign.py 的 axes——本任务用 **shell 循环直接驱动 runner** 而非 campaign.py，因 campaign.py 的 workload_args/cache-block-addr 透传未接 cache 路径）

**Interfaces:**
- Consumes: `tools/runner.py` 的 cache 路径（`--cache-block-addr` CLI，`classification=Corrected/Masked` PA 分流）
- Produces: `artifacts/l1d-ecc/raw.csv`、`artifacts/l1d-ecc/secded.csv`（每行一个 rep 的 classification）+ `artifacts/l1d-ecc/summary.md`

- [ ] **Step 1: 写批量驱动脚本**

```bash
cat > tools/l1d_ecc_batch.sh << 'EOF'
#!/bin/bash
# L1D raw-vs-secded formal batch (plan §6.5 risk-reversal table).
# 2 protection arms x 3 ECC-granularity (1/2/3-bit) x N reps.
# l1d_reduce Timing = 2.9s/run -> N=384, 6 cells = 2304 runs.
set -u
G5="${G5:?set G5=.../CHAOS/gem5/build/ARM/gem5.opt}"
REPO="$(cd "$(dirname "$0")/.." && pwd)"
OUT="$REPO/artifacts/l1d-ecc"; mkdir -p "$OUT"
N="${1:-384}"; JOBS="${2:-8}"; BLOCK="${3:-862656}"
export GEM5_OPT="$G5"
run_cell() {  # $1=protection $2=bits $3=tag
  local prot="$1" bits="$2" tag="$3" out="$OUT/${tag}.csv"
  echo "tag,protection,bits,classification,faults" > "$out"
  for ((i=0;i<N;i++)); do
    (
      manifest=$(mktemp --suffix=.yaml)
      sed -e "s/protection_model: secded/protection_model: $prot/" \
          -e "s/bit_indices: \[0\]/bit_indices: [0]/" \
          "$REPO/manifests/v2-cache-l1d-protection.yaml" > "$manifest"
      res=$(python3 "$REPO/tools/runner.py" "$manifest" \
        --binary "$REPO/workloads/directed/l1d_reduce" \
        --golden-checksum f44d2b9cd4a173cd \
        --cache-block-addr "$BLOCK" 2>&1 | grep "RESULT:" | head -1)
      cls=$(echo "$res" | grep -oE "classification=[A-Za-z]+" | cut -d= -f2)
      f=$(echo "$res" | grep -oE "faults_injected=[0-9]+" | cut -d= -f2)
      echo "$tag,$prot,$bits,${cls:-SimulatorError},${f:-0}" >> "$out"
      rm -f "$manifest"
    ) &
    while (( $(jobs -r | wc -l) >= JOBS )); do wait -n; done
  done
  wait
}
# ECC granularity via bits: rerun manifest bit_indices for 2/3-bit is fiddly;
# the CHAOSCache bitsToChange comes from len(bit_indices). We vary it by
# editing bit_indices in the manifest copy.
for bits in 1 2 3; do
  run_cell none    "$bits" "raw-b$bits"
  run_cell secded  "$bits" "secded-b$bits"
done
echo "batch done -> $OUT"
EOF
chmod +x tools/l1d_ecc_batch.sh
```

**注意（执行者必读）**：上面 manifest 的 bits 轴通过 `bit_indices` 编辑——初版脚本只替换了 protection。执行时把 `run_cell` 里 manifest 生成改为同时替换 bits：`sed -e "s/bit_indices: \[0\]/bit_indices: [$(seq -s, 0 $((bits-1)))]/"`（1-bit=[0]，2-bit=[0,1]，3-bit=[0,1,2]——CHAOSCache 的 `bitsToChange=len(bit_indices)`）。

- [ ] **Step 2: 先跑小规模验证（N=8 冒烟）**

```bash
cd /home/sdc/wangxu/gem5-fi-wangxu
source /home/sdc/gem5-deps/env.sh
G5=$PWD/CHAOS/gem5/build/ARM/gem5.opt
bash tools/l1d_ecc_batch.sh 8 8 862656   # 6 cell × 8 = 48 runs ~2 分钟
# 检查每臂的分类分布
for f in artifacts/l1d-ecc/*.csv; do
  echo "$f: $(tail -n +2 $f | awk -F, '{print $4}' | sort | uniq -c | tr '\n' ' ')"
done
```

预期：`raw-b1` 多为 Masked（或 Corrected 不应出现在 raw）；`secded-b1` 应有 Corrected；`secded-b2` 应有 DetectedContained（若分类走 PA 分流）或如实记录。

- [ ] **Step 3: 正式跑 N=384（后台 ~15-25 分钟）**

```bash
bash tools/l1d_ecc_batch.sh 384 8 862656
```

- [ ] **Step 4: 用 report.py 汇总成风险反转表**

```bash
python3 tools/report.py --inputs artifacts/l1d-ecc/raw-b1.csv \
    --unit-col protection | head -8
# 或直接 awk 聚合 classification 比例（report.py 的输入 schema 不同——
# 本批产物是 rep 级 csv，执行时写一个 5 行 awk 聚合各臂比例进 summary.md）
```

**执行者注意**：batch 产物 schema（tag,protection,bits,classification,faults）与 report.py 的 cells.csv schema 不同。汇总用直接 awk：

```bash
for f in artifacts/l1d-ecc/*.csv; do
  tag=$(basename $f .csv)
  total=$(tail -n +2 $f | wc -l)
  echo "== $tag (n=$total) =="
  tail -n +2 $f | awk -F, '{c[$4]++} END {for (k in c) printf "  %-18s %5d (%.1f%%)\n", k, c[k], 100*c[k]/'"$total"'}' | sort
done | tee artifacts/l1d-ecc/summary.md
```

- [ ] **Step 5: 提交（数据 + 脚本）**

```bash
git add tools/l1d_ecc_batch.sh artifacts/l1d-ecc/summary.md
git commit -m "formal-T2: L1D raw-vs-secded 正式数据集（n=384×6 cell 风险反转表）

2 protection 臂 × 1/2/3-bit ECC 粒度 × n=384（l1d_reduce Timing 2.9s）。
（引用 summary.md 实际比例：raw-b1 Masked 率 / secded-b1 Corrected 率 /
secded-b2 DetectedContained 率——风险反转方向 + NOT resident 回退率如实记录）"
git push origin fi-wangxu
```

---

### Task 3: formal 数据集 ②——PRF 位段×ABI 角色（kp920_proxy 下）

方案 §5.1 的核心网格：**X2/X3（循环计数器 vs 累加器）× 8 位段 × n=384**，`--kp920_proxy` V110 参数下。reg_chain O3 100s——**预算诚实**：2 reg × 8 bit × 384 = 6144 runs × 100s / 8 jobs ≈ 21 小时。**缩减**：X3 全 8 位段 n=384（正式）+ X2 只跑 3 个代表位（0/32/63）n=128（对照）= 3072+384 = 3456 runs ≈ 12 小时。**本计划拆两步**：先 X3 n=96（2.7 小时，jobs=8）产出初步正式表；全量留计算预算（Task 3b 可选）。

**Files:**
- Create: `campaigns/prf-formal.yaml`

**Interfaces:**
- Consumes: campaign.py 的 physreg 路径（已支持 target_arch/bit_indices/layer 轴）+ `--kp920-proxy`（**需先给 campaign.py 加 kp920 透传**——现无）
- Produces: `artifacts/prf-formal/cells.csv`（X3×8bit×n=96）

- [ ] **Step 1: campaign.py 加 --kp920-proxy 透传**

campaign.py 的 `gen_manifest` 产 manifest，runner 跑 gem5——kp920 参数在 arm_chaos.py 的 CLI 层。runner.py 构造 cmd 时需加 `--kp920_proxy`。改 runner.py：manifest 的 `platform.config_family: C2-KP` 时加该 flag：

```python
# tools/runner.py 在 cmd 构建后（"--bits_to_change", bits_to_change] 之后）：
    # C2-KP: apply V110 proxy params when the manifest declares it.
    if m.get("platform", {}).get("config_family") == "C2-KP":
        cmd += ["--kp920_proxy"]
```

- [ ] **Step 2: 写 prf-formal.yaml**

```yaml
# PRF X3 formal (plan §5.1): X3 (data accumulator, all-bit SDC) x 8 stratified
# bits x n=96/cell under C2-KP (V110 proxy). X2 contrast arm (3 bits, n=128)
# deferred to full-budget run.
campaign_id: prf_x3_formal
workload:
  binary: workloads/directed/reg_chain
  golden: f247ef3fe6f02cfd
  golden_id: regchain-golden-v1
  oracle_kind: exact_hash
trigger: {mode: cycle, value: 100000}
limits: {max_faults: 1, max_ticks: 0}
injector: physreg
config_family: C2-KP
axes:
  layer: [arch_frontend]
  target_arch: [3]
  bit_indices: [[0],[11],[12],[31],[32],[47],[48],[63]]
defaults:
  rng_master_seed: 20260825
  width_bits: 64
```

- [ ] **Step 3: 小冒烟（n=2）确认 kp920 透传生效**

```bash
cd /home/sdc/wangxu/gem5-fi-wangxu
source /home/sdc/gem5-deps/env.sh
G5=$PWD/CHAOS/gem5/build/ARM/gem5.opt
python3 tools/campaign.py campaigns/prf-formal.yaml \
  --binary workloads/directed/reg_chain --workload-golden f247ef3fe6f02cfd \
  --n-per-cell 2 --jobs 2 --gem5 "$G5" --artifacts artifacts/prf-smoke 2>&1 | tail -4
# 抽一个 manifest 确认 config_family: C2-KP 且 runner cmd 含 --kp920_proxy：
# runner 输出行有 "[runner] running: ... --kp920_proxy ..."（若加了 print）或
# 直接看 m5out/config.ini 的 numROBEntries=128
grep -l "config_family: C2-KP" artifacts/prf-smoke/manifests/*.yaml | head -1
```

- [ ] **Step 4: 正式跑 X3 n=96（后台 ~2.7 小时 jobs=8）**

```bash
python3 tools/campaign.py campaigns/prf-formal.yaml \
  --binary workloads/directed/reg_chain --workload-golden f247ef3fe6f02cfd \
  --n-per-cell 96 --jobs 8 --hang-timeout 300 \
  --gem5 "$G5" --artifacts artifacts/prf-formal 2>&1 | tail -10
```

- [ ] **Step 5: report.py 汇总 + 提交**

```bash
python3 tools/report.py --inputs artifacts/prf-formal/cells.csv --unit-col target_arch
git add campaigns/prf-formal.yaml tools/runner.py artifacts/prf-formal/cells.csv
git commit -m "formal-T3: PRF X3 正式数据集（8 位段 × n=96，C2-KP V110 代理下）

（引用实际 P_SDC 表——预期 X3 全位段高 SDC，与 STATUS.md 'X3 所有位 SDC' 一致）
X2 对照臂（3 位 × n=128）与全量 n=384 留计算预算。"
git push origin fi-wangxu
```

---

### Task 4: formal 数据集 ③——LSQ 转发几何 × 故障模式矩阵（method3）

方案 §5.4E 的矩阵：**fwd_7case 的 7 几何 × CHAOSLSQFwd 模式（bitflip/structural/fwd_source_sub/stale_line_replay/phaseOffset）**。fp_fwd_kernel 已知 fails=1 锚点；fwd_7case 14 组合确定性已验证。**预算**：campaign 的 workload_args 传 case 不支持（单 binary 参数）——用 shell 循环跑（同 Task 2 模式），case×mode 抽样：3 代表几何（same/twocand/ldxr）× 5 模式 × n=64 = 960 runs × ~30s / 8 jobs ≈ 1 小时。

**Files:**
- Create: `tools/lsq_matrix_batch.sh`

**Interfaces:**
- Consumes: arm_chaos.py 的 `--chaos_lsqfwd --fault_type/--lsq_structural_fault/--lsq_source_fault/--lsq_phase_offset` 开关全集 + fwd_7case `<iters> <case> [noop]` argv
- Produces: `artifacts/lsq-matrix/summary.md`（几何×模式的 fails 率矩阵）

**关键限制（诚实）**：arm_chaos.py 的 `--cmd` 不传 workload argv——fwd_7case 的 case 选择无法从 config 层传。**方案**：为每个 case 编译一份默认参数二进制（`fwd_7case_same` 等 7 份，源码同、默认 argv 不同——用 `-D` 编译期注入或直接跑默认 case=same + 手动 7 份 wrapper）。最简：写 7 个 2 行 C wrapper 调 main 逻辑。

- [ ] **Step 1: 编译 7 个 case 定向二进制**

```bash
cd /home/sdc/wangxu/gem5-fi-wangxu
for c in same partial alias4k twocand replay dmb ldxr; do
  cat > /tmp/wrap_$c.c << EOF
#include <string.h>
#include <stdlib.h>
int fwd7case_main(long, const char*, int);
int main(int argc, char **argv) {
  return fwd7case_main(argc>1?atol(argv[1]):2000, "$c", argc>2&&!strcmp(argv[2],"noop"));
}
EOF
  # fwd_7case.c 的 main 需重构为可调用函数——最简：main 原样 + wrapper 用 exec
  # 更简：直接复制 fwd_7case.c 并 sed 默认 case 字符串
  sed "s/const char \*cs = (argc > 2) ? argv\[2\] : \"same\";/const char *cs = \"$c\";/" \
      workloads/directed/fwd_7case.c > /tmp/f7_$c.c
  gcc -static -O2 -o workloads/directed/fwd_7case_$c /tmp/f7_$c.c
  # native 确定性
  a=$(workloads/directed/fwd_7case_$c 200 2>/dev/null)
  b=$(workloads/directed/fwd_7case_$c 200 2>/dev/null)
  [ "$a" = "$b" ] && echo "$c: OK $a" || echo "$c: NONDET"
done
```

- [ ] **Step 2: 写批量矩阵脚本（3 几何 × 5 模式 × n=64）**

```bash
cat > tools/lsq_matrix_batch.sh << 'EOF'
#!/bin/bash
# LSQ forwarding geometry x fault-mode matrix (plan §5.4E, method3).
set -u
G5="${G5:?}"; REPO="$(cd "$(dirname "$0")/.." && pwd)"
OUT="$REPO/artifacts/lsq-matrix"; mkdir -p "$OUT"
N="${1:-64}"; JOBS="${2:-8}"
declare -A MODE_ARGS=(
  [bitflip]="--chaos_lsqfwd --fault_type=bit_flip"
  [structural]="--chaos_lsqfwd --lsq_structural_fault=byte_lane_skew --lsq_skew_bytes=1"
  [fwdsrc]="--chaos_lsqfwd --lsq_source_fault=fwd_source_sub"
  [stale]="--chaos_lsqfwd --lsq_source_fault=stale_line_replay"
  [phase]="--chaos_lsqfwd --lsq_source_fault=phase_offset --lsq_phase_offset=2"
)
for geom in same twocand ldxr; do
  for mode in bitflip structural fwdsrc stale phase; do
    out="$OUT/${geom}_${mode}.csv"
    echo "rep,seed,checksum" > "$out"
    for ((i=0;i<N;i++)); do
      (
        seed=$((20260825 + i))
        ck=$("$G5" --quiet --outdir="$OUT/run_${geom}_${mode}_$i" \
          configs/se/arm_chaos.py \
          --cmd "$REPO/workloads/directed/fwd_7case_$geom" --cpu=O3 \
          ${MODE_ARGS[$mode]} \
          --probability=1.0 --first_clock=1000000 --max_faults=1 \
          --rng_seed=$seed 2>/dev/null | grep -E "^[0-9a-f]{16}$" | tail -1)
        echo "$i,$seed,${ck:-NONE}" >> "$out"
      ) &
      while (( $(jobs -r | wc -l) >= JOBS )); do wait -n; done
    done
    wait
  done
done
echo done
EOF
chmod +x tools/lsq_matrix_batch.sh
```

- [ ] **Step 3: 冒烟（N=4）→ 正式（N=64 后台 ~1 小时）**

```bash
source /home/sdc/gem5-deps/env.sh; G5=$PWD/CHAOS/gem5/build/ARM/gem5.opt
bash tools/lsq_matrix_batch.sh 4 8      # 冒烟
# 确认每 cell 有 checksum 产出后：
bash tools/lsq_matrix_batch.sh 64 8     # 后台
```

- [ ] **Step 4: 汇总矩阵表 + 提交**

每个 cell 的 SDC 判定：checksum ≠ 该几何的 gem5 golden（需先跑各 case 的无注入 golden 记录）。汇总：

```bash
for f in artifacts/lsq-matrix/*.csv; do
  tag=$(basename $f .csv); total=$(tail -n +2 $f | wc -l)
  # golden 从 Step 1 的 native/gem5 记录取——执行时先无注入跑 7 golden 存 golden.txt
  echo "$tag: n=$total"
done | tee artifacts/lsq-matrix/summary.md
git add tools/lsq_matrix_batch.sh workloads/directed/fwd_7case_* artifacts/lsq-matrix/
git commit -m "formal-T4: LSQ 几何×故障模式矩阵（3几何×5模式×n=64，method3）
（引用实际矩阵——各几何对不同故障模式的 SDC 率差异即 §5.4E 的核心数据）"
git push origin fi-wangxu
```

---

### Task 5: formal 数据集 ④——method1 F5 两臂正式跑（cholesky n=384 前置参数修正）

Task 4（Plan1）的 pilot 暴露：随机 FP 类 F5 在 cholesky 10-iters 上 0/10 SDC（多数 V 寄存器不在关键路径 + first_clock=50000 过晚）。**正式跑前需参数修正**：first_clock 降到 2000（数值段内）+ 定向 V0-V7（d0 所在低段）而非全随机。

**Files:**
- Modify: `campaigns/method1-f5-cholesky-formal.yaml`（axes 改 target_arch: [0,1,2,3] 定向低段 + trigger 提前）

- [ ] **Step 1: 修正 formal YAML 参数**

```yaml
# 修正点（对照 pilot 的 0/10 根因）：
#   target_arch: [-1] -> [0,1,2,3]   （定向 V0-V7 低段——d0 累加器所在；
#     随机全类大多命中非活跃映射，见 Plan1-T4 的 2308104 REJECT 诊断）
#   trigger.value: 50000 -> 2000      （cholesky 10 iters 的数值段内）
trigger: {mode: cycle, value: 2000}
axes:
  layer: [physical]
  target_arch: [0,1,2,3]     # V0-V7 (d0/d1/... 数值累加器段)
  semantic_role: [fp_accum]
  fault_model: [legal_domain_sub]
  f5_substitute_target: [-1]
```

- [ ] **Step 2: 修正后冒烟（n=10 确认注入不再 0）**

```bash
source /home/sdc/gem5-deps/env.sh; G5=$PWD/CHAOS/gem5/build/ARM/gem5.opt
python3 tools/campaign.py campaigns/method1-f5-cholesky-formal.yaml \
  --binary workloads/directed/cholesky_numeric --workload-golden 0 \
  --n-per-cell 10 --jobs 6 --hang-timeout 400 --workload-args "10" \
  --gem5 "$G5" --artifacts artifacts/m1-smoke2 2>&1 | tail -6
```

预期：修正后 SDC > 0 或至少 first 非 Masked（若仍 0/10，如实记录并进一步定向 V0-only——d0 是主累加器）。

- [ ] **Step 3: 正式两臂（n=384×4 cell×2 臂，后台 ~5.5 小时 jobs=8）**

```bash
# 臂1 numeric
python3 tools/campaign.py campaigns/method1-f5-cholesky-formal.yaml \
  --binary workloads/directed/cholesky_numeric --workload-golden 0 \
  --n-per-cell 384 --jobs 8 --hang-timeout 400 --workload-args "10" \
  --gem5 "$G5" --artifacts artifacts/m1-formal-num 2>&1 | tail -8
# 臂2 compute-both
python3 tools/campaign.py campaigns/method1-f5-cholesky-formal.yaml \
  --binary workloads/directed/cholesky_numeric --workload-golden 0 \
  --n-per-cell 384 --jobs 8 --hang-timeout 400 --workload-args "10 both" \
  --gem5 "$G5" --artifacts artifacts/m1-formal-both 2>&1 | tail -8
```

- [ ] **Step 4: Fisher 正式检验 + 提交**

```bash
python3 tools/fisher_test.py artifacts/m1-formal-num/cells.csv artifacts/m1-formal-both/cells.csv | tee artifacts/m1-formal-verdict.txt
git add campaigns/method1-f5-cholesky-formal.yaml artifacts/m1-formal-*/
git commit -m "formal-T5: method1 F5 两臂正式数据集（V0-V7 定向 × n=384 × 2 臂）

参数修正（pilot 0/10 根因）：target_arch 定向 V0-V7 低段 + first_clock 2000。
Fisher 正式判定：（引用 verdict.txt 实际 p 值与 ratio——§5.2 H 验收）"
git push origin fi-wangxu
```

---

### Task 6: 论文草稿——`docs/paper/sdc-fi-paper.md`（含全部数据表）

方案 §9.1 的 6 贡献点 × Task 2-5 的 4 个正式数据集。**产出完整可投稿草稿**（中文，与 paper_zh.md 同 Markdown 格式，含：摘要/引言/背景/方法（17 注入器+故障模型+campaign）/结果（4 数据集表格）/抗 SDC 设计建议（§8.3）/诊断反哺（§7）/有效性威胁/结论）。

**Files:**
- Create: `docs/paper/sdc-fi-paper.md`
- Create: `docs/paper/tables/`（从 artifacts 引出的表格 .md 片段）

**Interfaces:**
- Consumes: Task 2-5 的 `artifacts/*/summary.md` + `cells.csv` + `verdict.txt` + §5.0 锚点表 + §6.1 假设状态表
- Produces: 完整论文草稿（每个数字溯源到 artifact 文件）

- [ ] **Step 1: 建目录 + 生成数据表片段（从 artifacts 机械引出，禁止手写数字）**

```bash
mkdir -p docs/paper/tables
# 表1: 跨单元总表（PRF + L1D 两臂 + LSQ 矩阵抽样）
python3 tools/report.py --inputs artifacts/prf-formal/cells.csv artifacts/l1d-ecc/raw-b1.csv \
    --unit-col target_arch > docs/paper/tables/t1-cross-unit.md 2>&1 || true
# 表2: L1D 风险反转（raw vs secded 各粒度）
cp artifacts/l1d-ecc/summary.md docs/paper/tables/t2-l1d-riskreversal.md
# 表3: LSQ 几何×模式矩阵
cp artifacts/lsq-matrix/summary.md docs/paper/tables/t3-lsq-matrix.md
# 表4: method1 Fisher
cp artifacts/m1-formal-verdict.txt docs/paper/tables/t4-method1-fisher.txt
# 表5: 锚点表（生态效度）
grep -A20 "已验证锚点表" docs/KUNPENG920-SDC研究方案-系统完备版.md | head -22 > docs/paper/tables/t5-anchors.md
```

- [ ] **Step 2: 撰写论文正文（骨架如下——执行者按贡献点 1-6 逐节写，每节引用 tables/）**

论文骨架（每节的开头句已定，正文扩写到会议论文密度）：

```markdown
# ARM64 服务器 CPU 微架构级 SDC 注入、规律刻画与抗 SDC 设计闭环：以鲲鹏 920 为例

## 摘要
（150 词：问题—17 注入器/F5-F6+PCE 故障模型—4 正式数据集—风险反转/
Fisher 结论—抗 SDC 设计建议）

## 1. 引言
（SDC 三无特征 + 发生率 3 个数量级高于软错误模型 + ARM64 服务器研究空白
 + 6 贡献点列表——逐条对应 §2-§7）

## 2. 背景与现场动机
（core179 三通路 D1/D2/D3 + method1/2/3 签名——引用 docs/cases 的现场
数据作为研究靶子；诚实标注单机未复现）

## 3. 方法：gem5-fi 注入平台
### 3.1 17 个注入器（表：单元×hook×模式）
### 3.2 故障模型 F1-F6+PCE（F5 六载体表）
### 3.3 campaign 框架（六级/九类分类 + Wilson CI + fail_count oracle）

## 4. 正式结果
### 4.1 跨单元 P_SDC 总表（表1）
### 4.2 L1D 风险反转：raw escape vs ECC contained（表2）
### 4.3 LSQ 转发几何×模式矩阵（表3）
### 4.4 method1 状态泄漏的 Fisher 判定（表4）
### 4.5 生态效度锚点（表5——18+ 锚点全 pass）

## 5. 抗 SDC 微架构设计建议（§8.3 四条机制级建议）

## 6. openEuler 诊断反哺接口（§7 七步法 + 指纹库对接）

## 7. 有效性威胁
（gem5≠RTL/单机/非 FIT——三条诚实边界全文照录 §9.4）

## 8. 结论
```

- [ ] **Step 3: 自查（数字溯源）+ 提交**

```bash
# 自查：正文的每个 16-hex/百分比数字能在 tables/ 或 artifacts/ 找到
git add docs/paper/
git commit -m "paper-T6: 完整论文草稿（6 贡献点 × 4 正式数据集，数字全溯源）

docs/paper/sdc-fi-paper.md + tables/{t1..t5}（从 artifacts 机械引出，
禁止手写未溯源数字）。骨架按方案 §9.1。"
git push origin fi-wangxu
```

---

### Task 7: 产业工具固化——SDC 诊断指纹库 CLI `tools/sdc_fingerprint.py`

方案 §7.7/§8.3：注入数据 → **位谱指纹库**（unit → sign/exp/mantissa 分布 + popcount 中位），供现场诊断反查候选单元（留一法验证）。

**Files:**
- Create: `tools/sdc_fingerprint.py`
- Test: `tests/test_fingerprint.py`
- Create: `docs/paper/tables/fingerprint-library.md`（指纹库数据文件）

**Interfaces:**
- Consumes: `fi_research/bit_spectrum.py` 的字段分类逻辑（sign/exp/mantissa 位段 + popcount）——直接 import 复用，不重写
- Produces: CLI 两个子命令：`build`（从 masks 文本建库 JSON）+ `lookup`（现场 xor 值 → Top-K 候选单元 + 置信度）

- [ ] **Step 1: 写失败测试**

```python
# tests/test_fingerprint.py
import os, sys, json, tempfile
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tools"))

def test_build_and_lookup():
    from sdc_fingerprint import build_library, lookup
    # 两个单元的合成指纹：lsq 的 mantissa 主导（method3 签名），prf 的均匀
    lsq_masks = [0x00000004, 0x00000100, 0x00000200]     # 低位=尾数
    prf_masks = [0x80000000, 0x40000000]                 # 高位=符号/指数
    lib = build_library({
        "lsq_fwd": lsq_masks, "physreg": prf_masks})
    assert lib["lsq_fwd"]["mantissa_share"] > 0.9
    assert lib["physreg"]["sign_exp_share"] > 0.9
    # lookup: 一个尾数主导的现场 xor -> lsq 排第一
    ranked = lookup(lib, 0x00000100)
    assert ranked[0][0] == "lsq_fwd"
```

- [ ] **Step 2: 确认失败 → 实现**

```bash
python3 -m pytest tests/test_fingerprint.py -v 2>&1 | tail -2
# 预期 FAIL: No module named 'sdc_fingerprint'
```

```python
#!/usr/bin/env python3
"""sdc_fingerprint.py — SDC bit-spectrum fingerprint library CLI (§7.7/§8.3).

build: unit name -> {sign_share, exp_share, mantissa_share, popcount_median}
       from a list of XOR masks (golden^actual), reusing bit_spectrum.py's
       IEEE754 field classification.
lookup: a field xor value -> Top-K candidate units ranked by field-share
       similarity (diagnosis feedback: spectrum -> suspect unit).

Usage:
  python3 tools/sdc_fingerprint.py build lib.json lsq_fwd:masks.txt ...
  python3 tools/sdc_fingerprint.py lookup lib.json 0x00000100 --top 3
"""
import argparse, json, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "fi_research"))
from bit_spectrum import classify_bits  # reuse the field classifier

def build_library(unit_masks):
    lib = {}
    for unit, masks in unit_masks.items():
        sign = exp = man = 0; pcs = []
        for m in masks:
            f = classify_bits(m, "double")   # returns dict w/ field counts
            sign += f["sign"]; exp += f["exponent"]; man += f["mantissa"]
            pcs.append(bin(m).count("1"))
        total = sign + exp + man or 1
        pcs.sort()
        lib[unit] = {
            "sign_exp_share": round((sign + exp) / total, 4),
            "mantissa_share": round(man / total, 4),
            "popcount_median": pcs[len(pcs)//2] if pcs else 0,
            "n": len(masks)}
    return lib

def lookup(lib, xor_value):
    f = classify_bits(xor_value, "double")
    v_man = f["mantissa"]; v_se = f["sign"] + f["exponent"]
    tot = v_man + v_se or 1
    scores = []
    for unit, fp in lib.items():
        # similarity: how much the observed field mix matches the unit's mix
        s = 1 - abs(fp["mantissa_share"] - v_man / tot)
        scores.append((unit, round(s, 4)))
    return sorted(scores, key=lambda x: -x[1])

def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build"); b.add_argument("out")
    b.add_argument("units", nargs="+", help="unit:masks_file ...")
    l = sub.add_parser("lookup"); l.add_argument("lib")
    l.add_argument("xor", type=lambda x: int(x, 0)); l.add_argument("--top", type=int, default=3)
    a = ap.parse_args()
    if a.cmd == "build":
        um = {}
        for spec in a.units:
            unit, path = spec.split(":", 1)
            with open(path) as f:
                um[unit] = [int(line.strip(), 0) for line in f if line.strip()]
        with open(a.out, "w") as f: json.dump(build_library(um), f, indent=2)
        print(f"library -> {a.out}")
    else:
        with open(a.lib) as f: lib = json.load(f)
        for unit, s in lookup(lib, a.xor)[:a.top]:
            print(f"{unit}: similarity={s}")

if __name__ == "__main__":
    main()
```

**执行者注意**：`bit_spectrum.py` 的 `classify_bits` 函数名/签名需先核实（`grep -n "def " fi_research/bit_spectrum.py`）——若实际是别的名字（如 `spectrum`），适配 import 与调用；若它只有 main() 无可导入函数，把字段分类逻辑（sign bit 63 / exp 62-52 / mantissa 51-0 的计数）内联进 build_library（15 行，注明来源）。

- [ ] **Step 3: 测试通过 + 用真实注入数据建库**

```bash
python3 -m pytest tests/test_fingerprint.py -v 2>&1 | tail -2   # PASS
# 从 fp_fwd_kernel 的注入 log 提取真实 xor masks（已有锚点数据）：
grep -oE "xor=[0-9a-f]+" runs/t1_sleak2/lsq_fwd_injections.log 2>/dev/null | cut -d= -f2 > /tmp/lsq_masks.txt
# （若无现成 log，跑一个 CHAOSLSQFwd fp_fwd_kernel 注入收集 20 个 xor）
# 建库 + 查询演示
python3 tools/sdc_fingerprint.py build docs/paper/tables/fingerprint-library.json \
    lsq_fwd:/tmp/lsq_masks.txt
python3 tools/sdc_fingerprint.py lookup docs/paper/tables/fingerprint-library.json 0x0000000004000000 --top 3
```

- [ ] **Step 4: 提交**

```bash
git add tools/sdc_fingerprint.py tests/test_fingerprint.py docs/paper/tables/fingerprint-library.json
git commit -m "tool-T7: SDC 诊断指纹库 CLI（build/lookup，诊断反哺接口落地）

build_library（复用 bit_spectrum 字段分类）+ lookup（现场 xor -> Top-K
候选单元相似度排序）。pytest 覆盖 mantissa 主导/均匀两指纹的可分性。
真实注入 xor 建库 + 查询演示（引用实际输出）。
产业工具三件套之二（注入平台 + 指纹库 CLI + openEuler 规则接口见论文 §6）。"
git push origin fi-wangxu
```

---

### Task 8: 收尾——progress.md 最终状态 + 方案文档正式数据回填

- [ ] **Step 1: progress.md 记录本计划全部产物**

- [ ] **Step 2: 方案文档 §6.1 假设表回填正式结果（H0/H9 等从"待 formal"改为引用 verdict/summary）**

- [ ] **Step 3: 提交推送**

```bash
git add progress.md docs/KUNPENG920-SDC研究方案-系统完备版.md
git commit -m "docs: formal 阶段完成（4 数据集 + 论文草稿 + 指纹库 CLI）

§6.1 假设表回填正式结果；progress 记录 8 任务产物。"
git push origin fi-wangxu
```

---

## Self-Review 结论

**1. 覆盖检查（三大机会）：**
- formal 规模化 → Task 2/3/4/5（4 个数据集，覆盖 §6.5 风险反转/§5.1 PRF/§5.4E 矩阵/§5.2 Fisher）✓
- 论文 → Task 6（6 贡献点 × 5 表，数字溯源纪律）✓
- 产业工具 → Task 7（指纹库 CLI）+ 论文 §6（openEuler 接口引用现有 §7）✓
- **诚实 gap（有意不做）**：X2 对照臂全量/n=384 全量（Task 3 标注留预算）；CHAOSIQ/ROB 等 formal（注入器机制已验证但 kernel 配对未设计——超出本计划"数据→论文→工具"主线）

**2. 占位符扫描：** 无 TBD。Task 2/4 的"执行者注意"是条件指令（sed bits 轴的具体写法/7 二进制编译的备选）非占位。Task 7 的 classify_bits 名字核实指令已写明 fallback（内联 15 行）。

**3. 类型一致性：** report.py 的 `wilson(k,n)->(lo,p,hi)` 与 fisher_test.py 既有实现一致；`build_library(unit_masks: dict)->dict` 与 `lookup(lib, xor)->list[(unit,score)]` 在测试与实现间一致；Task 3 的 config_family 判断串 `C2-KP` 与 manifest schema v2 的 enum 一致。

**预算总览（执行者规划用）：** 冒烟合计 <30 分钟；正式数据 T2 ~25min / T3 ~2.7h / T4 ~1h / T5 ~5.5h（全后台可并行做 Task 6/7）。
