#!/usr/bin/env python3
"""[LSU][P4-FIX-RECLASS] 版本化离线重分类层 v2 + 31 项签名矩阵（2026-10-15）。

背景（docs/gem5-fi/lsu/evidence/P4/lsu_simfail_root_cause_20261015.md）：
  P4 AGU formal 批次（p4_agu_formal_20261012，31 RunID）65% activated 样本
  落入 post_activation_simulator_failure。审计证明其中绝大多数是 SE 模式
  无法向 guest 递交页故障/取指异常造成的"架构结局被记成模拟器中止"，
  另有少量 guard 超时 SIGTERM / gem5 自身 SIGSEGV 被误分类为 guest Crash。

本工具（用户指令 2026-10-15 二）：
  1. 只读：绝不写/改 runs/ 下任何原始 result.json、l5_verdict.json、
     guard.out；输出全部落 evidence 目录或 stdout。
  2. 版本化：rule_version="2"；每个被移动的样本一条记录（原/新类别、
     rule_id、证据文件、命中的原始签名）。
  3. 守恒：逐 RunID 与全批 v1 总数 == v2 总数 == n_scanned；只移桶。

规则（优先级自上而下；仅作用于 injected>=1 的 run；签名规则先于退出码规则）：
  R2.1 guard 含 "Page table fault when accessing virtual address" 且回溯含
       "GenericPageTableFault"（guest 执行/commit 传播路径）→ five.Crash，
       来源 guest_arch_fault；
  R2.2 guard 含 "Attempted to execute unknown instruction" → five.Crash，
       来源 guest_arch_fault；
  R2.5 guard 含 VMA sanity 断言（"_addrRange.start() < _addrRange.end()"）→
       保持 SimulatorFailure，tag VMA_INDETERMINATE；
  R2.6 guard 含 "sizeof(T) <= size" → 保持 SimulatorFailure，
       tag A06_MODEL_CONFLICT；
  R2.7 guard 含 "pkt->getOffset(blkSize) + pkt->getSize() <= blkSize" →
       保持 SimulatorFailure，tag PACKET_GEOMETRY_CONFLICT；
  R2.3 gem5_exit == -15（guard 超时 SIGTERM）→ five.Timeout；
  R2.4 gem5_exit == -11（gem5 自身 SIGSEGV）→ SimulatorFailure。

用法：
  python3 tools/lsu_reclass_v2.py matrix [--repo REPO] [--out JSON]
  python3 tools/lsu_reclass_v2.py verify [--repo REPO] [--per-rule N]
  python3 tools/lsu_reclass_v2.py dryrun [--repo REPO] [--out-dir DIR]
"""
import argparse
import datetime
import glob
import json
import os
import re
import sys
from collections import Counter

RULE_VERSION = "2"

# ---------------------------------------------------------------- item table
# RunID 映射依据：runs/lsu/obs/next_batch_proposal_20261012.json（skipped 段）
# × 冻结文档 runids × 各 ITEM_s0_guard.out 命令行三重交叉验证（审计报告 §3）。
# basis: checklist = runs/lsu/pilot/AGU（20 项，formal 权威）
#        w1        = runs/lsu/pilot_w1/ITEM-XXX/（11 项 W1 载体改指，formal 权威）
# 注意：pilot/AGU 下同名 11 个 result.json 是 2026-09-30/10-08 的 pilot 旧
# 文件（BLOCKED 300/0），已被 pilot_w1 formal 结果取代，本工具不读它们。
ITEMS = {
    "ITEM-001": ("A01-F0-W3", "checklist"), "ITEM-002": ("A01-F0-W9", "checklist"),
    "ITEM-003": ("A01-F1-W3", "w1"),        "ITEM-004": ("A01-F1-W9", "w1"),
    "ITEM-005": ("A01-F2-W3", "w1"),        "ITEM-006": ("A01-F2-W9", "checklist"),
    "ITEM-007": ("A02-F0-W3", "checklist"), "ITEM-008": ("A02-F0-W9", "checklist"),
    "ITEM-009": ("A02-F2-W3", "w1"),        "ITEM-010": ("A02-F2-W9", "checklist"),
    "ITEM-013": ("A04-F0-W3", "checklist"), "ITEM-014": ("A04-F0-W0", "checklist"),
    "ITEM-015": ("A04-F2-W3", "w1"),        "ITEM-016": ("A04-F2-W0", "w1"),
    "ITEM-017": ("A04-F6-W3", "checklist"), "ITEM-018": ("A04-F6-W0", "checklist"),
    "ITEM-019": ("A05-F0-W3", "checklist"), "ITEM-020": ("A05-F2-W3", "w1"),
    "ITEM-021": ("A05-F6-W3", "checklist"), "ITEM-022": ("A06-F0-W3", "checklist"),
    "ITEM-023": ("A06-F0-W5", "checklist"), "ITEM-024": ("A06-F2-W3", "w1"),
    "ITEM-025": ("A06-F2-W5", "w1"),        "ITEM-026": ("A06-F6-W3", "checklist"),
    "ITEM-027": ("A06-F6-W5", "checklist"), "ITEM-034": ("A08-F0-W3", "checklist"),
    "ITEM-035": ("A08-F0-W5", "checklist"), "ITEM-036": ("A08-F2-W3", "w1"),
    "ITEM-037": ("A08-F2-W5", "w1"),        "ITEM-038": ("A08-F6-W3", "checklist"),
    "ITEM-039": ("A08-F6-W5", "checklist"),
}

FIVE = ["Masked", "Detected/Contained", "SDC", "Crash", "Timeout"]

SIG_PT = "Page table fault when accessing virtual address"
SIG_UNKNOWN_INSTR = "Attempted to execute unknown instruction"
SIG_SIZEOF = "sizeof(T) <= size"
SIG_CACHELINE = "pkt->getOffset(blkSize) + pkt->getSize() <= blkSize"
SIG_VMA = "_addrRange.start() < _addrRange.end()"
SIG_IMPORT = "ImportError"

EXIT_RE = re.compile(r'"exit_code": (-?\d+)')
FATAL_MSG_RE = re.compile(
    r"^(?:gem5\.opt: )?(src/\S+:\d+: )?(?:panic(?: condition [^\n]*? occurred)?: "
    r"?|Assertion `([^`\n]+)' failed\.?)(.*)$", re.M)


def item_paths(repo, item):
    """(result.json 路径, guard glob 模式, 样本目录基) — 只读。"""
    runid, basis = ITEMS[item]
    if basis == "checklist":
        base = os.path.join(repo, "runs/lsu/pilot/AGU")
        return (os.path.join(base, item + "_result.json"),
                os.path.join(base, item + "_s[0-9]*_guard.out"), base)
    base = os.path.join(repo, "runs/lsu/pilot_w1", item)
    return (os.path.join(base, item + "_result.json"),
            os.path.join(base, item + "_s[0-9]*_guard.out"), base)


def classify_guard(text):
    """返回 (signature, exit_code, fatal_line)。signature ∈
    pt/unknown_instr/sizeof/cacheline/vma/import_error/other_panic/
    other_assert/none。"""
    sig = "none"
    if SIG_IMPORT in text:
        sig = "import_error"
    elif SIG_PT in text and "GenericPageTableFault" in text:
        sig = "pt"
    elif SIG_UNKNOWN_INSTR in text:
        sig = "unknown_instr"
    elif SIG_SIZEOF in text:
        sig = "sizeof"
    elif SIG_CACHELINE in text:
        sig = "cacheline"
    elif SIG_VMA in text:
        sig = "vma"
    else:
        m = re.search(r"panic(?: condition [^\n]* occurred)?: ([^\n]+)", text)
        if m:
            sig = "other_panic"
        elif re.search(r"Assertion `[^`']+' failed", text):
            sig = "other_assert"
    exit_code = None
    for m in EXIT_RE.finditer(text):
        exit_code = int(m.group(1))
    fatal = None
    for line in text.splitlines():
        if (SIG_PT in line or SIG_UNKNOWN_INSTR in line or SIG_SIZEOF in line
                or SIG_CACHELINE in line or SIG_VMA in line
                or "panic" in line or "Assertion" in line or "ImportError" in line):
            fatal = line.strip()[:300]
            break
    return sig, exit_code, fatal


def v1_bucket(verdict):
    """复刻 tools/lsu_unit_pilot.py audit() 的 v1 口径（只读推导，不 import
    ——避免对 runs 数据的工具侧耦合）。"""
    if verdict.get("error") or verdict.get("outcome") == "INCONCLUSIVE":
        return "clf"
    if (verdict.get("activated") or 0) >= 1:
        if (verdict.get("crash_kind") == "simulator_assert"
                and verdict.get("outcome") == "Crash"):
            return "simfail"
        return "five:" + str(verdict.get("outcome"))
    return "ina"


def apply_rules(sig, exit_code, bucket):
    """返回 (rule_id, new_bucket, source_tag) 或 None。仅激活样本可被移动。"""
    if bucket in ("ina", "clf"):
        return None
    if sig == "pt":
        return ("R2.1", "five:Crash", "guest_arch_fault")
    if sig == "unknown_instr":
        return ("R2.2", "five:Crash", "guest_arch_fault")
    if sig == "vma":
        return ("R2.5", bucket, "VMA_INDETERMINATE")      # 保持，打标
    if sig == "sizeof":
        return ("R2.6", bucket, "A06_MODEL_CONFLICT")     # 保持，打标
    if sig == "cacheline":
        return ("R2.7", bucket, "PACKET_GEOMETRY_CONFLICT")  # 保持，打标
    if sig in ("other_panic", "other_assert", "none", "import_error"):
        if exit_code == -15:
            return ("R2.3", "five:Timeout", "guard_sigterm")
        if exit_code == -11:
            return ("R2.4", "simfail", "simulator_sigsegv")
    return None


def scan_item(repo, item):
    """扫描一个 RunID 的全部 live 样本（排除 *.quarantine*，要求样本目录
    存在且 l5_verdict.json 可读）。只读。"""
    runid, basis = ITEMS[item]
    rj_path, guard_glob, _base = item_paths(repo, item)
    result_json = json.load(open(rj_path)) if os.path.exists(rj_path) else None
    samples = []
    for g in sorted(glob.glob(guard_glob),
                    key=lambda p: int(re.search(r"_s(\d+)_guard", p).group(1))):
        sdir = g[:-len("_guard.out")]
        if ".quarantine" in sdir or not os.path.isdir(sdir):
            continue  # 隔离样本 = 未记账；孤儿 guard = 目录已隔离
        vp = os.path.join(sdir, "l5_verdict.json")
        if not os.path.exists(vp):
            continue  # 无有效 verdict（driver 未记账的目录）
        verdict = json.load(open(vp))
        with open(g, errors="replace") as fh:
            text = fh.read()
        sig, exit_code, fatal = classify_guard(text)
        bucket = v1_bucket(verdict)
        samples.append(dict(
            sample=os.path.basename(sdir), verdict=verdict, sig=sig,
            exit_code=exit_code, fatal=fatal, bucket=bucket,
            guard=os.path.relpath(g, repo)))
    return runid, basis, result_json, samples


def aggregate_v1(samples):
    five = Counter(); simfail = 0; ina = 0; clf = 0
    for s in samples:
        b = s["bucket"]
        if b.startswith("five:"):
            five[b[5:]] += 1
        elif b == "simfail":
            simfail += 1
        elif b == "ina":
            ina += 1
        else:
            clf += 1
    return dict(five_class={k: five.get(k, 0) for k in FIVE},
                simfail=simfail, ina=ina, clf=clf,
                total=len(samples))


def reclassify(samples):
    moves = []
    v2_five = Counter(); v2_simfail_tags = Counter(); v2_ina = 0; v2_clf = 0
    sig_cols = Counter()          # simfail 样本的签名分解（矩阵列）
    exit_cols = Counter()         # exit -15/-11（任意 v1 桶）
    diag = Counter()              # 诊断：import_error 等（任意桶）
    for s in samples:
        if s["sig"] == "import_error":
            diag["import_error_live"] += 1   # D 类废样本（v1 记账 ina）
        rule = apply_rules(s["sig"], s["exit_code"], s["bucket"])
        b2 = s["bucket"]; tag = None
        if rule:
            rid, b2, tag = rule
            moves.append(dict(
                item=None, sample=s["sample"], rule_id=rid,
                rule_version=RULE_VERSION, orig=s["bucket"], new=b2,
                source_tag=tag, evidence=s["guard"],
                signature=s["fatal"] or ("exit_code=%s" % s["exit_code"])))
        if s["bucket"] == "simfail":
            sig_cols[s["sig"]] += 1
        if s["exit_code"] == -15:
            exit_cols["exit_m15"] += 1
        if s["exit_code"] == -11:
            exit_cols["exit_m11"] += 1
        if b2.startswith("five:"):
            v2_five[b2[5:]] += 1
        elif b2 == "simfail":
            v2_simfail_tags[tag or "other"] += 1
        elif b2 == "ina":
            v2_ina += 1
        else:
            v2_clf += 1
    return moves, dict(
        five_class={k: v2_five.get(k, 0) for k in FIVE},
        simfail_by_tag=dict(v2_simfail_tags), ina=v2_ina, clf=v2_clf,
        total=len(samples)), sig_cols, exit_cols, diag


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("mode", choices=["matrix", "verify", "dryrun"])
    ap.add_argument("--repo", default=str(
        __import__("pathlib").Path(__file__).resolve().parents[1]),
        help="仓库根（默认=工具所在仓库；审计时指向主仓）")
    ap.add_argument("--out", default=None, help="matrix 模式输出 JSON 路径")
    ap.add_argument("--out-dir", default=None, help="dryrun 模式输出目录")
    ap.add_argument("--per-rule", type=int, default=3, help="verify 每类样本数")
    args = ap.parse_args()

    now = datetime.datetime.now().strftime("%F %T")
    items_out, moved_records = [], []
    batch = Counter()
    for item in sorted(ITEMS):
        runid, basis, result_json, samples = scan_item(args.repo, item)
        v1 = aggregate_v1(samples)
        moves, v2, sig_cols, exit_cols, diag = reclassify(samples)
        for mv in moves:
            mv["item"] = item
        moved_records.extend(moves)
        # 与 result.json 对账（权威记账 vs 本次 live 扫描）
        delta = None
        if result_json:
            fc = result_json.get("five_class") or {}
            delta = dict(
                attempted=(result_json.get("attempted_runs") or 0) - v1["total"],
                activated=(result_json.get("activated_runs") or 0)
                          - (sum(v1["five_class"].values()) + v1["simfail"]),
                simfail=(result_json.get("post_activation_simulator_failure") or 0)
                        - v1["simfail"],
                ina=(result_json.get("injected_not_activated_runs") or 0) - v1["ina"])
        conservation = ("OK" if v1["total"] == v2["total"] else "VIOLATION")
        # 矩阵列（simfail 签名分解 + other）
        other_simfail = v1["simfail"] - sum(
            sig_cols[k] for k in ("pt", "unknown_instr", "sizeof", "cacheline", "vma"))
        items_out.append(dict(
            item=item, runid=runid, basis=basis,
            result_json=os.path.relpath(item_paths(args.repo, item)[0], args.repo),
            n_scanned=v1["total"], v1=v1, v2=v2,
            matrix=dict(
                activated=sum(v1["five_class"].values()) + v1["simfail"],
                five_class_total=sum(v1["five_class"].values()),
                PageTableFault=sig_cols.get("pt", 0),
                unknown_instruction=sig_cols.get("unknown_instr", 0),
                sizeof_assert=sig_cols.get("sizeof", 0),
                cacheline_assert=sig_cols.get("cacheline", 0),
                vma_assert=sig_cols.get("vma", 0),
                other_simfail=other_simfail,
                exit_m15=exit_cols.get("exit_m15", 0),
                exit_m11=exit_cols.get("exit_m11", 0),
                import_error_live=diag.get("import_error_live", 0)),
            moves_by_rule=dict(Counter(m["rule_id"] for m in moves)),
            conservation=conservation, result_json_delta=delta))

    if args.mode == "matrix":
        out = dict(
            generated=now, rule_version=RULE_VERSION,
            note=("31 formal RunID 统一根因交叉表。扫描基准=live(未隔离)且有 "
                  "l5_verdict.json 的样本目录；signature 列=该 RunID 全部 "
                  "v1-simfail 样本的 guard.out 致命签名分解；exit_m15/m11 为 "
                  "扫描到的对应退出码样本数（v1 记账位于 five.Crash）；"
                  "result_json_delta=live 扫描 vs result.json 权威记账差。"
                  "11 个 pilot/AGU 旧 BLOCKED result.json 已被 pilot_w1 formal "
                  "取代，不在本表（见审计报告 §2.1）。"),
            items=items_out,
            batch=dict(
                n_items=len(items_out),
                n_scanned=sum(i["n_scanned"] for i in items_out),
                conservation=("OK" if all(
                    i["conservation"] == "OK" for i in items_out) else "VIOLATION"),
                totals=dict(
                    (k, sum(i["matrix"][k] for i in items_out)) for k in (
                        "activated", "five_class_total", "PageTableFault",
                        "unknown_instruction", "sizeof_assert",
                        "cacheline_assert", "vma_assert", "other_simfail",
                        "exit_m15", "exit_m11", "import_error_live"))))
        batch_v1_simfail = sum(i["v1"]["simfail"] for i in items_out)
        batch_v1_five = sum(sum(i["v1"]["five_class"].values()) for i in items_out)
        out["batch"]["totals"]["v1_simfail_scanned"] = batch_v1_simfail
        out["batch"]["totals"]["v1_five_scanned"] = batch_v1_five
        path = args.out or "lsu_simfail_signature_matrix.json"
        with open(path, "w") as fh:
            json.dump(out, fh, indent=1, ensure_ascii=False)
        print(f"matrix -> {path} ({len(items_out)} items, "
              f"{out['batch']['n_scanned']} samples scanned)")
        for i in items_out:
            m = i["matrix"]
            print(f"{i['item']} {i['runid']:12} act={m['activated']:>5} "
                  f"five={m['five_class_total']:>5} PT={m['PageTableFault']:>5} "
                  f"UI={m['unknown_instruction']:>3} sizeof={m['sizeof_assert']:>4} "
                  f"CL={m['cacheline_assert']:>3} VMA={m['vma_assert']:>3} "
                  f"other_sf={m['other_simfail']:>3} -15={m['exit_m15']:>2} "
                  f"-11={m['exit_m11']:>2} cons={i['conservation']} "
                  f"delta={i['result_json_delta']}")

    elif args.mode == "verify":
        # 每类 ≥N 样本人工对照（stdout，供人工核对后存档 manual_check.md）
        by_rule = {}
        for mv in moved_records:
            by_rule.setdefault(mv["rule_id"], []).append(mv)
        for rid in sorted(by_rule):
            print(f"\n===== {rid} ({len(by_rule[rid])} moved) — "
                  f"{args.per_rule} samples =====")
            for mv in by_rule[rid][:args.per_rule]:
                print(f"  sample : {mv['item']}/{mv['sample']}")
                print(f"  orig   : {mv['orig']}  ->  new: {mv['new']}"
                      f"  (source_tag={mv['source_tag']})")
                print(f"  evidence: {mv['evidence']}")
                print(f"  signature: {mv['signature']}")
        print(f"\ntotal moved={len(moved_records)}")

    else:  # dryrun
        outdir = args.out_dir or "."
        os.makedirs(outdir, exist_ok=True)
        v1_five = Counter(); v1_simfail = v1_ina = v1_clf = 0
        for i in items_out:
            for k, v in i["v1"]["five_class"].items():
                v1_five[k] += v
            v1_simfail += i["v1"]["simfail"]
            v1_ina += i["v1"]["ina"]
            v1_clf += i["v1"]["clf"]
        v2_five = Counter(); v2_tags = Counter(); v2_ina = v2_clf = 0
        for i in items_out:
            for k, v in i["v2"]["five_class"].items():
                v2_five[k] += v
            for k, v in i["v2"]["simfail_by_tag"].items():
                v2_tags[k] += v
            v2_ina += i["v2"]["ina"]
            v2_clf += i["v2"]["clf"]
        out = dict(
            generated=now, rule_version=RULE_VERSION, mode="dryrun",
            note=("预计结果（不写 Excel、不改任何原始文件）。v2 five/simfail "
                  "仅在本表移动；批准后由回填工具另行消费。"),
            before=dict(five_class={k: v1_five.get(k, 0) for k in FIVE},
                        simfail=v1_simfail, ina=v1_ina, clf=v1_clf),
            after=dict(five_class={k: v2_five.get(k, 0) for k in FIVE},
                       simfail_by_tag=dict(v2_tags), simfail_total=sum(v2_tags.values()),
                       ina=v2_ina, clf=v2_clf),
            moves_by_rule=dict(Counter(m["rule_id"] for m in moved_records)),
            conservation=dict(
                per_item={i["item"]: i["conservation"] for i in items_out},
                batch=("OK" if all(i["conservation"] == "OK" for i in items_out)
                       and sum(v2_five.values()) + sum(v2_tags.values())
                       + v2_ina + v2_clf
                       == sum(v1_five.values()) + v1_simfail + v1_ina + v1_clf
                       else "VIOLATION")),
            items=[dict(item=i["item"], runid=i["runid"],
                        v1=i["v1"], v2=i["v2"],
                        moves_by_rule=i["moves_by_rule"],
                        result_json_delta=i["result_json_delta"])
                   for i in items_out],
            moved_records=moved_records)
        path = os.path.join(outdir, "reclass_v2_dryrun.json")
        with open(path, "w") as fh:
            json.dump(out, fh, indent=1, ensure_ascii=False)
        print(f"dryrun -> {path}")
        print(f"BEFORE: five={dict((k, v1_five.get(k, 0)) for k in FIVE)} "
              f"simfail={v1_simfail} ina={v1_ina} clf={v1_clf}")
        print(f"AFTER : five={dict((k, v2_five.get(k, 0)) for k in FIVE)} "
              f"simfail={sum(v2_tags.values())} (tags={dict(v2_tags)}) "
              f"ina={v2_ina} clf={v2_clf}")
        print(f"moves : {dict(Counter(m['rule_id'] for m in moved_records))}")
        print(f"conservation: {out['conservation']['batch']}")


if __name__ == "__main__":
    main()
