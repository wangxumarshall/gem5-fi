#!/usr/bin/env python3
"""Render the long-term roadmap ledger to SVG/PNG and a Markdown summary.

Source of truth: docs/roadmap/roadmap.yaml.  Edit the ledger, then run

    python3 tools/render_roadmap.py
    inkscape docs/roadmap/roadmap.svg --export-type=png \
        --export-filename=docs/roadmap/roadmap.png

Status colours distinguish "verified locally", "external evidence",
"partial", "not started" and "environment-gated" milestones so an incomplete
item can never be mistaken for a finished one.
"""

import datetime as dt
import textwrap
from pathlib import Path
from xml.sax.saxutils import escape

import yaml

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "docs/roadmap/roadmap.yaml"
SVG = ROOT / "docs/roadmap/roadmap.svg"
MD = ROOT / "docs/roadmap/ROADMAP.md"

WIDTH = 1600
MARGIN = 40
LEFT_COLUMN = 330
PROGRESS_COLUMN = 90

STATUS = {
    "done-local": {
        "label": "完成（本仓库实测）", "short": "完成",
        "fill": "#E7F4EC", "stroke": "#1D7A46", "dot": "#1D7A46",
        "text": "#14532D",
    },
    "done-external": {
        "label": "完成（外部证据，未本机复验）", "short": "外部证据",
        "fill": "#E8F1F8", "stroke": "#2F7EA8", "dot": "#2F7EA8",
        "text": "#0F3F57",
    },
    "partial": {
        "label": "部分完成", "short": "部分",
        "fill": "#FDF3E3", "stroke": "#C77C02", "dot": "#C77C02",
        "text": "#6B4300",
    },
    "todo": {
        "label": "未开始", "short": "未开始",
        "fill": "#F1F5F9", "stroke": "#94A3B8", "dot": "#94A3B8",
        "text": "#334155",
    },
    "gated": {
        "label": "环境门控（缺硬件/工具链）", "short": "门控",
        "fill": "#F3EDFB", "stroke": "#7C3AED", "dot": "#7C3AED",
        "text": "#4C1D95",
    },
}

ORDER = ("done-local", "done-external", "partial", "todo", "gated")
FONT = "Microsoft YaHei, Noto Sans CJK SC, Droid Sans Fallback, sans-serif"
INK = "#0F172A"
BODY = "#334155"
MUTED = "#64748B"
LINE = "#CBD5E1"
CARD = "#F8FAFC"


def text_width(text, size=12.5):
    units = sum(1.0 if ord(char) >= 0x2E80 else 0.54 for char in text)
    return units * size


def counts(milestones):
    result = {status: 0 for status in ORDER}
    for milestone in milestones:
        result[milestone["status"]] += 1
    return result


def progress(milestones):
    total = len(milestones) or 1
    done = sum(1 for m in milestones
               if m["status"] in ("done-local", "done-external"))
    partial = sum(1 for m in milestones if m["status"] == "partial")
    return (done + 0.5 * partial) / total


def chips_for(milestones):
    return [(m["short"], m["status"], m.get("title", ""), m.get("evidence", ""))
            for m in milestones]


def wrap_chips(chips, max_width, size=12.5, pad=34, gap=8):
    lines, current, used = [], [], 0.0
    for chip in chips:
        width = text_width(chip[0], size) + pad
        if current and used + width + gap > max_width:
            lines.append(current)
            current, used = [], 0.0
        current.append((chip, width))
        used += width + gap
    if current:
        lines.append(current)
    return lines


def chip_svg(x, y, width, height, chip):
    label, status, title, evidence = chip
    style = STATUS[status]
    tooltip = escape(f"{title}｜{STATUS[status]['label']}｜{evidence}")
    return f"""  <g>
    <title>{tooltip}</title>
    <rect x="{x:.1f}" y="{y:.1f}" width="{width:.1f}" height="{height}"
          rx="{height / 2:.1f}" fill="{style['fill']}" stroke="{style['stroke']}"
          stroke-width="1"/>
    <circle cx="{x + 13:.1f}" cy="{y + height / 2:.1f}" r="4"
            fill="{style['dot']}"/>
    <text x="{x + 24:.1f}" y="{y + height / 2 + 4:.1f}" font-size="12.5"
          font-family="{FONT}" fill="{style['text']}">{escape(label)}</text>
  </g>"""


def legend_svg(counts_all):
    x = MARGIN
    y = 150
    parts = []
    for status in ORDER:
        style = STATUS[status]
        label = f"{style['label']}  {counts_all[status]}"
        width = text_width(label, 12.5) + 40
        parts.append(f"""  <g>
    <rect x="{x:.1f}" y="{y}" width="{width:.1f}" height="26" rx="13"
          fill="{style['fill']}" stroke="{style['stroke']}" stroke-width="1"/>
    <circle cx="{x + 14:.1f}" cy="{y + 13}" r="4.5" fill="{style['dot']}"/>
    <text x="{x + 26:.1f}" y="{y + 17.5}" font-size="12.5" font-family="{FONT}"
          fill="{style['text']}">{escape(label)}</text>
  </g>""")
        x += width + 12
    return "\n".join(parts)


def bar_svg(x, y, width, height, milestones, radius=8):
    total = len(milestones) or 1
    result = [f"""  <rect x="{x}" y="{y}" width="{width}" height="{height}"
        rx="{radius}" fill="#E2E8F0"/>"""]
    cursor = x
    for status in ORDER:
        amount = sum(1 for m in milestones if m["status"] == status)
        if not amount:
            continue
        segment = width * amount / total
        result.append(f"""  <rect x="{cursor:.1f}" y="{y}" width="{segment:.2f}"
        height="{height}" fill="{STATUS[status]['dot']}" opacity="0.9"/>""")
        cursor += segment
    return "\n".join(result)


def render():
    ledger = yaml.safe_load(LEDGER.read_text())
    tracks = ledger["tracks"]
    all_milestones = [m for track in tracks for phase in track["phases"]
                      for m in phase["milestones"]]
    overall_counts = counts(all_milestones)
    overall_progress = progress(all_milestones)

    chips_max = WIDTH - MARGIN * 2 - LEFT_COLUMN - PROGRESS_COLUMN - 20
    body = []
    y = 200

    # Overall bar.
    body.append(f"""  <text x="{MARGIN}" y="{y}" font-size="14" font-family="{FONT}"
        fill="{BODY}" font-weight="bold">总体进度</text>
  <text x="{WIDTH - MARGIN}" y="{y}" font-size="14" font-family="{FONT}"
        fill="{MUTED}" text-anchor="end">完成度 {overall_progress * 100:.1f}%
        （{sum(1 for m in all_milestones if m['status'] in ('done-local', 'done-external'))}
        / {len(all_milestones)} 完成，其中本仓库实测
        {sum(1 for m in all_milestones if m['status'] == 'done-local')}；
        {overall_counts['partial']} 部分，{overall_counts['todo']} 未开始，
        {overall_counts['gated']} 门控）</text>""")
    y += 10
    body.append(bar_svg(MARGIN, y, WIDTH - MARGIN * 2, 18, all_milestones))
    y += 46

    for track in tracks:
        body.append(f"""  <text x="{MARGIN}" y="{y}" font-size="17" font-family="{FONT}"
        fill="{INK}" font-weight="bold">{escape(track['title'])}</text>""")
        y += 14
        body.append(f"""  <line x1="{MARGIN}" y1="{y}" x2="{WIDTH - MARGIN}" y2="{y}"
        stroke="{LINE}" stroke-width="1.2"/>""")
        y += 18
        for phase in track["phases"]:
            milestones = phase["milestones"]
            phase_counts = counts(milestones)
            phase_progress = progress(milestones)
            body.append(f"""  <text x="{MARGIN}" y="{y + 6}" font-size="14"
        font-family="{FONT}" fill="{INK}" font-weight="bold">{escape(phase['title'])}</text>
  <text x="{MARGIN}" y="{y + 24}" font-size="11.5" font-family="{FONT}"
        fill="{MUTED}">窗口 {escape(phase['window'])} · {len(milestones)} 项</text>""")
            chip_x = MARGIN + LEFT_COLUMN
            chip_y = y - 4
            lines = wrap_chips(chips_for(milestones), chips_max)
            for line in lines:
                cursor = chip_x
                for chip, width in line:
                    body.append(chip_svg(cursor, chip_y, width, 28, chip))
                    cursor += width + 8
                chip_y += 36
            row_height = max(len(lines) * 36 + 10, 52)
            done_count = sum(1 for m in milestones
                             if m['status'] in ('done-local', 'done-external'))
            local_done = sum(1 for m in milestones
                             if m['status'] == 'done-local')
            body.append(f"""  <text x="{WIDTH - MARGIN}" y="{y + 6}" font-size="13"
        font-family="{FONT}" fill="{INK}" font-weight="bold" text-anchor="end">完成 {done_count}/{len(milestones)}</text>
  <text x="{WIDTH - MARGIN}" y="{y + 24}" font-size="11.5" font-family="{FONT}"
        fill="{MUTED}" text-anchor="end">实测 {local_done}/{len(milestones)} · {phase_progress * 100:.0f}%</text>
  <line x1="{MARGIN}" y1="{y + row_height - 6}" x2="{WIDTH - MARGIN}"
        y2="{y + row_height - 6}" stroke="#E2E8F0" stroke-width="1"/>""")
            y += row_height
        y += 16

    height = int(y + 70)
    updated = ledger.get("updated", "")
    footer = f"""  <line x1="{MARGIN}" y1="{height - 46}" x2="{WIDTH - MARGIN}"
        y2="{height - 46}" stroke="{LINE}" stroke-width="1"/>
  <text x="{MARGIN}" y="{height - 24}" font-size="11.5" font-family="{FONT}"
        fill="{MUTED}">台账：{LEDGER.relative_to(ROOT)} · 更新 {updated} · 重生成：
        python3 tools/render_roadmap.py</text>
  <text x="{WIDTH - MARGIN}" y="{height - 24}" font-size="11.5"
        font-family="{FONT}" fill="{MUTED}" text-anchor="end">生成于
        {dt.datetime.now().strftime('%Y-%m-%d %H:%M')}</text>"""

    header = f"""  <rect x="0" y="0" width="{WIDTH}" height="{height}" fill="#FFFFFF"/>
  <text x="{MARGIN}" y="62" font-size="27" font-family="{FONT}" fill="{INK}"
        font-weight="bold">{escape(ledger['title'])}</text>
  <text x="{MARGIN}" y="92" font-size="12.5" font-family="{FONT}" fill="{MUTED}">
        {escape(ledger['subtitle'])}</text>
  <text x="{WIDTH - MARGIN}" y="62" font-size="12.5" font-family="{FONT}"
        fill="{MUTED}" text-anchor="end">更新日期 {updated}</text>
  <text x="{WIDTH - MARGIN}" y="84" font-size="12.5" font-family="{FONT}"
        fill="{MUTED}" text-anchor="end">总里程碑 {len(all_milestones)}</text>"""

    svg = f"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{height}"
     viewBox="0 0 {WIDTH} {height}" role="img"
     aria-label="sdcfuzz 长期任务进度图">
{header}
{legend_svg(overall_counts)}
{chr(10).join(body)}
{footer}
</svg>
"""
    SVG.write_text(svg)
    write_markdown(ledger, tracks, all_milestones, overall_counts,
                   overall_progress)
    print(f"svg: {SVG.relative_to(ROOT)}  ({WIDTH}x{height})")
    print(f"md:  {MD.relative_to(ROOT)}")
    return svg


def write_markdown(ledger, tracks, all_milestones, overall_counts,
                   overall_progress):
    lines = [f"# {ledger['title']}", "",
             f"> {ledger['subtitle']}", "",
             f"- 更新日期：{ledger['updated']}",
             f"- 总进度：**{overall_progress * 100:.1f}%**"
             f"（完成 {overall_counts['done-local'] + overall_counts['done-external']}"
             f"/{len(all_milestones)}，其中本仓库实测 {overall_counts['done-local']}；"
             f"部分 {overall_counts['partial']}，"
             f"未开始 {overall_counts['todo']}，门控 {overall_counts['gated']}）",
             "",
             "![路线进度图](roadmap.svg)", "",
             "## 状态图例", ""]
    for status in ORDER:
        style = STATUS[status]
        lines.append(f"- `{status}` — {style['label']}")
    lines += ["", "## 里程碑明细", ""]
    for track in tracks:
        lines.append(f"### {track['title']}")
        lines.append("")
        for phase in track["phases"]:
            percent = progress(phase["milestones"]) * 100
            lines.append(f"#### {phase['title']}（{phase['window']}，"
                         f"{percent:.0f}%）")
            lines.append("")
            lines.append("| 里程碑 | 状态 | 证据 / 缺口 |")
            lines.append("|---|---|---|")
            for milestone in phase["milestones"]:
                lines.append(
                    f"| {milestone['title']} | `{milestone['status']}` | "
                    f"{milestone.get('evidence', '')} |")
            lines.append("")
    lines += [
        "## 维护方式", "",
        "1. 修改 `docs/roadmap/roadmap.yaml`（状态取值见文件头注释）。",
        "2. 重新生成：`python3 tools/render_roadmap.py`。",
        "3. 需要 PNG 时：",
        "",
        "```bash",
        "inkscape docs/roadmap/roadmap.svg --export-type=png \\",
        "  --export-filename=docs/roadmap/roadmap.png",
        "```",
        "",
    ]
    MD.write_text("\n".join(lines))


if __name__ == "__main__":
    render()
