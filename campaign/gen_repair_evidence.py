#!/usr/bin/env python3
"""Generate PARTIAL23_REPAIR_EVIDENCE/ — class-focused evidence for the 23
formerly-PARTIAL samples (A: 12 fetch, B: 6 M05 commit-consumer, C: 5 masked).
Reads per_condition.json chains + manifests + oracles; no experiment changes.
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DELIVERY = os.path.join(ROOT, "exports", "MMU_E2E_V3_FINAL_DELIVERY")
ANALYSIS = os.path.join(ROOT, "analysis")
OUT = os.path.join(DELIVERY, "PARTIAL23_REPAIR_EVIDENCE")


def load(p, d=None):
    try:
        with open(p) as f:
            return json.load(f)
    except (OSError, ValueError):
        return d


per = {p["NewSampleRunID"]: p for p in
       load(os.path.join(ANALYSIS, "per_condition.json"), [])}
r2 = load(os.path.join(ANALYSIS, "retry2_map.json"), {})
r2ev = load(os.path.join(ANALYSIS, "retry2_evidence_index.json"), {})

CLASSES = {
    "fetch": ["M03-C02", "M04-C02", "M05-C02", "M07-C05"],
    "m05_commit": ["M05-C04", "M05-C05"],
    "masked": ["M05-C03"],
    "pending": ["M07-C02"],
}
CLASS_DIRS = {
    "fetch": "A_fetch_paths",
    "m05_commit": "B_m05_commit_consumers",
    "masked": "C_masked_paths",
    "pending": "D_roi_pending",
}
CLASS_TITLE = {
    "fetch": "取指传播链 (instruction-fetch IFU)",
    "m05_commit": "M05 错误提交消费者",
    "masked": "掩盖路径 (masked)",
    "pending": "ROI 结束前请求未完成 (REQUEST_PENDING_AT_ROI_END, PARTIAL)",
}


def chain(sid):
    return (per.get(sid) or {}).get("Chain") or {}


def sids_for(model_ctx):
    m, c = model_ctx.split("-")
    return sorted(s for s in r2 if s.startswith("%s-" % m) and
                  ("-" + c + "-") in s)


def edge_str(edges):
    return "; ".join("%s->%s(%s)" % (e.get("source"), e.get("target"),
                                     e.get("basis")) for e in edges)


def write_sample(f, sid, cls):
    ch = chain(sid)
    root = ch.get("root") or {}
    stages = ch.get("stages") or {}
    term = ch.get("terminal") or {}
    edges = ch.get("edges", [])
    branches = ch.get("branches", [])
    summary = ch.get("summary") or {}
    ev = r2ev.get(sid, {})
    f.write("\n### %s\n" % sid)
    f.write("- 激活: %s(%s) @%s (tid=%s)\n" %
            (root.get("event_id", ""), root.get("kind", ""),
             root.get("tick", ""), root.get("translation_id", "")))
    order = ["mutation", "translation", "request", "response", "writeback",
             "consumer", "commit_squash"]
    for name in order:
        e = stages.get(name)
        if e:
            f.write("- %s: %s(%s) @%s tid=%s seq=%s\n" %
                    (name, e.get("event_id", ""), e.get("kind", ""),
                     e.get("tick", ""), e.get("translation_id", ""),
                     e.get("dyn_inst_seq", "")))
    f.write("- 终点: %s(%s) @%s\n" %
            (term.get("event_id", ""), term.get("kind", ""),
             term.get("tick", "")))
    f.write("- 边: %s\n" % edge_str(edges))
    f.write("- 分支: %s\n" % "; ".join(
        "tid=%s %s commit=%s squash=%s" %
        (b.get("translation_id", ""), b.get("terminal_kind", ""),
         b.get("commits", ""), b.get("squashed", "")) for b in branches))
    if summary:
        f.write("- 汇总: outcome=%s masked_reason=%s\n" %
                (summary.get("outcome", ""), summary.get("masked_reason", "")))
    f.write("- trace: %s\n  SHA256: %s\n" % (ev.get("trace", ""),
                                             ev.get("trace_sha256", "")))


def main():
    os.makedirs(OUT, exist_ok=True)
    # per-sample dirs
    for cls, mcs in CLASSES.items():
        d = os.path.join(OUT, CLASS_DIRS[cls])
        os.makedirs(d, exist_ok=True)

    # class-level evidence files
    for cls, mcs in CLASSES.items():
        for mc in mcs:
            sids = sids_for(mc)
            with open(os.path.join(OUT, CLASS_DIRS[cls], mc + ".md"), "w") as f:
                f.write("# %s — %s\n" % (mc, CLASS_TITLE[cls]))
                f.write("样本: %s\n" % ", ".join(sids))
                for sid in sids:
                    write_sample(f, sid, cls)

    # README
    with open(os.path.join(OUT, "README.md"), "w") as f:
        f.write("# PARTIAL23 补全专项证据\n\n")
        f.write("原 23 条 PARTIAL：21 条补全为 FULL（取指 12 + M05 数据消费者 9），"
                "M07-C02-T01/T02 正确重分类为 REQUEST_PENDING_AT_ROI_END "
                "（PARTIAL，请求在 ROI 结束前未完成）。\n\n")
        for cls, mcs in CLASSES.items():
            f.write("## %s (%d 条)\n" % (CLASS_TITLE[cls],
                                          sum(len(sids_for(m)) for m in mcs)))
            for m in mcs:
                f.write("- %s\n" % m)
            f.write("\n")
        f.write("## 核查要点\n\n")
        f.write("- A (取指 12): Fault -> MMU Translation -> Execute Request -> "
                "IFU Response -> Decode -> Commit，以 translation_id + 真实 "
                "dyn_inst_seq 关联；合成 lsu_request 与真实 ifu_response 区分。\n")
        f.write("- B (M05 9): 错误 partial entry 身份 -> PTW -> complete DTB entry "
                "-> 暖命中消费者 -> memory_response -> rf_writeback -> data "
                "consumer(consumer_of) -> consumer commit。\n")
        f.write("- C (掩盖 3): M05-C03 weak/dead consumer 显式掩盖。\n")
        f.write("- D (ROI pending 2): M07-C02 请求在 ROI 结束前未完成，保留 "
                "PARTIAL（非 FULL/非 MASKED）。完整技术核查见交付根目录 "
                "`M07_C02_FINAL_CLOSURE.md`。\n")
    print("PARTIAL23_REPAIR_EVIDENCE:", len(r2), "samples organized")


if __name__ == "__main__":
    main()
