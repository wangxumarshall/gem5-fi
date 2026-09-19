#!/usr/bin/env python3
"""五款 CPU 微架构功能图生成器（第三代：逐芯片差异化布局 + 统一视觉语言）。

视觉语言统一取自 sdc-fig-arm64.html 模板：
  - 画布白底 + 标题/副标题
  - 分组色带：浅色底 + 深色圆角标题签 + 组内白盒卡片（#7c93a8 描边 1.5）
  - 箭头 #5a6b7c 1.6（数据流实线 / 控制流紫虚线）
  - ★ 金粗框 #b45309 3px = 独有/标志性部件；灰虚线盒 = 未公开/黑盒
  - 红 #b91c1c = SDC 高危/无保护；绿 #047857 = 有保护披露

差异化为第一目标：每芯片一个独立布局函数，盒子结构反映各自微架构事实
（内容基准 = 第一代逐芯片图 git cae54212，已过事实核验）。
乱码修复：输出带 <?xml encoding="UTF-8"?> 头；正文避开 GBK 外字符
（✓→[v]、✗→[x]、µ→u、·→ ASCII 安全的 · 保留——中文字符在 UTF-8 声明下安全）。
"""

FONT = "system-ui,'PingFang SC','Noto Sans CJK SC','Microsoft YaHei',sans-serif"
C = dict(
    fetch_bg="#eaf2fb", fetch_st="#a9c9ec", fetch_tag="#4a5f78",
    ooo_bg="#eaf6ee", ooo_st="#a9d9bc", ooo_tag="#3f7a58",
    ex_bg="#fdf2e5", ex_st="#edcba0", ex_tag="#a05a2c",
    mem_bg="#f1edfb", mem_st="#cfc0ef", mem_tag="#6d5aa0",
    sys_bg="#f0f4f8", sys_st="#c3ced9", sys_tag="#46586b",
    box="#7c93a8", sub_bg="#fff8ef", sub_st="#e0b98a",
    arrow="#5a6b7c", ctrl="#7c3aed",
    txt="#1f2937", sub="#6b7280",
    gold="#b45309", gold_bg="#fffbeb",
    unknown_st="#9ca3af", unknown_bg="#f9fafb",
    green="#047857", red="#b91c1c",
)

def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

class Fig:
    """统一视觉原语 + 自由画布（每芯片自定布局）。"""
    def __init__(self, slug, title, subtitle, w, h):
        self.w, self.h = w, h
        self.buf = []
        self.slug, self.title, self.subtitle = slug, title, subtitle
        self._hdr()

    def _hdr(self):
        self.buf.append(f'<?xml version="1.0" encoding="UTF-8" standalone="no"?>')
        self.buf.append(
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.w} {self.h}" '
            f'width="{self.w}" height="{self.h}" font-family="{FONT}">'
        )
        self.buf.append(
            '  <defs>'
            '<marker id="arr" markerWidth="11" markerHeight="9" refX="9.5" refY="4.5" orient="auto" markerUnits="userSpaceOnUse"><path d="M0,0 L11,4.5 L0,9 Z" fill="#5a6b7c"/></marker>'
            '<marker id="arrC" markerWidth="11" markerHeight="9" refX="9.5" refY="4.5" orient="auto" markerUnits="userSpaceOnUse"><path d="M0,0 L11,4.5 L0,9 Z" fill="#7c3aed"/></marker>'
            '</defs>'
        )
        self.buf.append(f'  <rect x="0" y="0" width="{self.w}" height="{self.h}" fill="#ffffff"/>')
        self.buf.append(f'  <text x="30" y="34" font-size="20" font-weight="700" fill="{C["txt"]}">{esc(self.title)}</text>')
        self.buf.append(f'  <text x="30" y="56" font-size="12" fill="{C["sub"]}">{esc(self.subtitle)}</text>')

    # ---------- 原语 ----------
    def group(self, x, y, w, h, tag, tag_w, bg, st, tag_fill, note=None):
        """分组色带：浅底 + 深色标题签（模板核心视觉）。note 为标题签右侧斜体说明。"""
        self.buf.append(f'  <rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10" fill="{bg}" stroke="{st}" stroke-width="1.5"/>')
        self.buf.append(f'  <rect x="{x}" y="{y-24}" width="{tag_w}" height="24" rx="5" fill="{tag_fill}"/>')
        self.buf.append(f'  <text x="{x+11}" y="{y-6.5}" font-size="14" fill="#ffffff" font-weight="600">{esc(tag)}</text>')
        if note:
            self.buf.append(f'  <text x="{x+tag_w+16}" y="{y-7}" font-size="11.5" fill="{tag_fill}" font-style="italic">{esc(note)}</text>')

    def box(self, x, y, w, h, title, lines, gold=False, unknown=False,
            fs=13, lfs=10.5, center=True, tfs=None):
        """卡片盒。lines 元素可为 str 或 (text, color) 或 (text, color, weight)。"""
        sw = '3' if gold else '1.5'
        st = C["gold"] if gold else (C["unknown_st"] if unknown else C["box"])
        dash = ' stroke-dasharray="6,4"' if unknown else ''
        fill = C["gold_bg"] if gold else (C["unknown_bg"] if unknown else "#ffffff")
        self.buf.append(f'  <rect x="{x}" y="{y}" width="{w}" height="{h}" rx="7" fill="{fill}" stroke="{st}" stroke-width="{sw}"{dash}/>')
        tx = x + w / 2 if center else x + 12
        anchor = "middle" if center else "start"
        tfs = tfs or fs
        self.buf.append(f'  <text x="{tx}" y="{y+22}" font-size="{tfs}" fill="{C["txt"]}" text-anchor="{anchor}" font-weight="700">{esc(title)}</text>')
        yy = y + 42
        for ln in lines:
            color, weight, size = C["txt"], '', lfs
            if isinstance(ln, tuple):
                text, color = ln[0], ln[1]
                if len(ln) == 3 and ln[2]:
                    weight = f' font-weight="600"'
                # 短文本行用小号
                if len(text) <= 14 and w >= 180:
                    size = lfs
            else:
                text = ln
            self.buf.append(f'  <text x="{tx}" y="{yy}" font-size="{size}" fill="{color}" text-anchor="{anchor}"{weight}>{esc(text)}</text>')
            yy += 17

    def text(self, x, y, s, fs=12, fill=None, anchor="middle", bold=False, italic=False):
        fill = fill or C["txt"]
        extra = ''
        if bold: extra += ' font-weight="600"'
        if italic: extra += ' font-style="italic"'
        self.buf.append(f'  <text x="{x}" y="{y}" font-size="{fs}" fill="{fill}" text-anchor="{anchor}"{extra}>{esc(s)}</text>')

    def arr(self, d, dashed=False, color=None, marker="arr"):
        dash = ' stroke-dasharray="5,4"' if dashed else ''
        color = color or C["arrow"]
        mk = f'url(#{marker})'
        self.buf.append(f'  <path d="{d}" fill="none" stroke="{color}" stroke-width="1.6"{dash} marker-end="{mk}"/>')

    def line(self, x1, y1, x2, y2, color=None, width=3, dash=None):
        d = f' stroke-dasharray="{dash}"' if dash else ''
        color = color or C["red"]
        self.buf.append(f'  <line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="{width}"{d}/>')

    def banner(self, y, title, rows, fill="#fef2f2", stroke=None, h=None, tcol=None):
        """底部 RAS 横幅（红=裸奔 / 绿=有防御）。rows: [(label, val, color)]"""
        stroke = stroke or C["red"]
        tcol = tcol or C["red"]
        h = h or 30 + len(rows) * 20 + 10
        self.buf.append(f'  <rect x="30" y="{y}" width="{self.w-60}" height="{h}" rx="10" fill="{fill}" stroke="{stroke}" stroke-width="2"/>')
        self.buf.append(f'  <text x="46" y="{y+26}" font-size="15" fill="{tcol}" font-weight="700">{esc(title)}</text>')
        yy = y + 48
        for label, val, color in rows:
            self.buf.append(f'  <text x="46" y="{yy}" font-size="11.5" fill="{C["txt"]}">{esc(label)}</text>')
            self.buf.append(f'  <text x="{46+360}" y="{yy}" font-size="11.5" fill="{color}">{esc(val)}</text>')
            yy += 19

    def legend(self, items, y=None):
        """通用图例条（每图一致的 token 图例）。items: [(kind, label)]"""
        y = y or 72
        self.buf.append(f'  <rect x="30" y="{y}" width="{self.w-60}" height="36" rx="6" fill="#f7f9fb" stroke="#c6d2dd"/>')
        x = 46
        for kind, label in items:
            if kind == 'flow':
                self.buf.append(f'    <line x1="{x}" y1="{y+18}" x2="{x+26}" y2="{y+18}" stroke="{C["arrow"]}" stroke-width="2" marker-end="url(#arr)"/>')
                x += 32
            elif kind == 'ctrl':
                self.buf.append(f'    <line x1="{x}" y1="{y+18}" x2="{x+26}" y2="{y+18}" stroke="{C["ctrl"]}" stroke-width="2" stroke-dasharray="5,3" marker-end="url(#arrC)"/>')
                x += 32
            elif kind == 'gold':
                self.buf.append(f'    <rect x="{x}" y="{y+11}" width="14" height="14" fill="{C["gold_bg"]}" stroke="{C["gold"]}" stroke-width="2.6"/>')
                x += 20
            elif kind == 'unknown':
                self.buf.append(f'    <rect x="{x}" y="{y+11}" width="14" height="14" fill="{C["unknown_bg"]}" stroke="{C["unknown_st"]}" stroke-width="1.3" stroke-dasharray="4,3"/>')
                x += 20
            elif kind == 'sdc':
                self.buf.append(f'    <line x1="{x}" y1="{y+18}" x2="{x+22}" y2="{y+18}" stroke="{C["red"]}" stroke-width="3.5"/>')
                x += 28
            self.buf.append(f'    <text x="{x}" y="{y+22}" font-size="11.5" fill="{C["txt"]}">{esc(label)}</text>')
            x += self._tw(label) + 26

    @staticmethod
    def _tw(s):
        return sum(18 if ord(c) > 0x2e80 else 7 for c in s)

    def save(self, path):
        self.buf.append('</svg>')
        open(path, 'w', encoding='utf-8').write('\n'.join(self.buf) + '\n')
        return path


R, G, U = C["red"], C["green"], C["sub"]
GOLD = C["gold"]

def build_fig(spec, out_path):
    fig = Fig(spec['slug'], spec['title'], spec['subtitle'], spec['w'], spec['h'])
    fig.legend(spec['legend'])
    spec['draw'](fig)
    return fig.save(out_path)


# ════════════════════════════════════════════════════════════════
# 1. Kunpeng 920 (TaiShan v110) — 实测口径，chiplet L3 三模式
# ════════════════════════════════════════════════════════════════
def draw_920(f):
    Y = 130
    # —— 前端（4 宽，无 uop cache）——
    f.group(30, Y, 1420, 240, "前端 Fetch（按序 · 4 宽）", 190, C['fetch_bg'], C['fetch_st'], C['fetch_tag'],
            "无 uop-cache → 取指带宽悬崖：L1I 内 4 条/cyc → L2 ~1.75 → L3/内存 ~0.25")
    f.box(50, Y+36, 260, 178, "BPU 分支预测", [
        ("· BTB 两级：L1 64 项（taken 1c）", C["txt"]),
        ("· L2 BTB ~2048 项", C["txt"]),
        ("· 方向：两级动态（≈A73 水平）", C["txt"]),
        ("· RAS 31–32 · 间接 ~256 目标", C["txt"]),
        ("· 无任何 ECC/parity 披露（无 PAC）", R, 1),
        ("· mcf MPKI 16.64（N1 为 15.03）", C["sub"]),
    ], center=False, fs=13.5, lfs=10.5)
    f.box(50, Y+228+8, 260, 0, "", [])  # spacer no-op
    f.box(340, Y+36, 200, 96, "L1-I-cache 64KB 4-way", [
        ("64B 行 · AIVIVT（L1Ip=2 实测）", GOLD, 1),
        ("厂商称 ECC（无架构化证据）", R, 1),
    ], gold=True)
    f.box(340, Y+146, 200, 68, "取指+译码", [
        "4 条/周期 · 定长 32-bit",
        "仅 AArch64（无 AArch32）",
    ])
    f.arr(f"M300,{Y+120} L334,{Y+120}")
    f.arr(f"M440,{Y+132} L440,{Y+142}", color=C['ctrl'], marker='arrC')
    f.text(452, Y+128, "下一 PC", 10, C['ctrl'], "start")
    f.box(570, Y+36, 250, 178, "Rename / Dispatch", [
        ("· PRF 式：31 GPR → INT ~128 物理寄存器", C["txt"]),
        ("· Flag 重命名 ~31 · move elimination", C["txt"]),
        ("· FP/向量 PRF 偏小（易压满）", C["txt"]),
        ("· 按类分流 → 三类统一式调度器", C["txt"]),
        ("· PRF 翻转=直接 SDC（无保护披露）", R, 1),
        ("· squash 回滚依赖历史缓冲正确性", C["sub"]),
    ], center=False)
    f.arr(f"M540,{Y+120} L564,{Y+120}")
    f.box(850, Y+36, 290, 178, "ISA 精确边界（ID 寄存器 EL0 实测）", [
        ("有：LSE 完整 · AES+PMULL · SHA1/256（无 512）", C["txt"]),
        ("　　CRC32 · UDOT/SDOT · FHM · JSCVT · FCMA", C["txt"]),
        ("无：SVE · PAC · BTI · LRCPC · MTE · AArch32", R, 1),
        ("CTR：DIC=IDC=0（无 I/D 自动一致）· ERG=64B", C["txt"]),
        ("CASAL 实测 43c · NOP 0.26c ≈ 3.9 IPC", C["sub"]),
        ("MMFR0/DFR0 部分字段固件实现不全（已判可信边界）", C["sub"]),
    ], center=False)
    f.arr(f"M820,{Y+120} L844,{Y+120}")

    # —— 后端（乱序）——
    Y2 = 400
    f.group(30, Y2, 1420, 300, "后端 OoO Execute", 150, C['ex_bg'], C['ex_st'], C['ex_tag'],
            "ROB ~128 uop（实测有效 108–110）· 三类统一式调度器各 ~33 项")
    f.box(50, Y2+36, 250, 150, "发射队列（3 类统一式）", [
        ("· ALU 类 ~33 · 访存类 ~33 · FP/向量类 ~33", C["txt"]),
        ("· 唤醒-选择环路 1–2c", C["txt"]),
        ("· 控制触发器密集 = SDC 敏感区", R, 1),
        ("· 每源寄存器一条等待链", C["sub"]),
        ("· 对照：Neoverse V2 为 9 个分立 IQ", C["sub"]),
    ], center=False)
    f.box(330, Y2+36, 250, 150, "PRF + 旁路网络", [
        ("· INT PRF ~128 · Flag ~31 · FP PRF 偏小", C["txt"]),
        ("· 记分牌：读 PRF 或等旁路", C["txt"]),
        ("· 旁路=纯导线+传输门，无任何保护", R, 1),
        ("· 背靠背链不写 PRF（转发掩蔽）", C["sub"]),
    ], center=False)
    f.box(610, Y2+36, 380, 150, "执行单元簇", [
        ("· ALU×3（加 1c）· MUL/DIV×1（乘 4c；除 19c/早退 6.2c）", C["txt"]),
        ("· FP0/FP1 双 128-bit FMA（FP32 5c · FP64 quarter-rate）", C["txt"]),
        ("· 分支两口 · 1 taken/cyc · CRC32X 1c · AESD 3c", C["txt"]),
        ("· NEON 128b 上限（无 SVE）", C["txt"]),
        ("· 进位链/FMA 树=时序违例重灾区（纯 SDC 通路）", R, 1),
    ], center=False)
    f.box(1020, Y2+36, 400, 150, "ROB ~128 uop + Commit（4 宽）", [
        ("· 按程序序飞行指令账本 · 头部完成且无异常才退休", C["txt"]),
        ("· squash 从出错点回滚全部后继", C["txt"]),
        ("· 结果退休进架构态 · store 放行写 L1D（C7）", C["txt"]),
        ("· x86 ROB 320–512 vs ARM 640–768+（面积账对照）", C["sub"]),
        ("· 反压：ROB/IQ/LSQ 满 → rename 停", C["sub"]),
    ], center=False)
    f.arr(f"M300,{Y2+110} L324,{Y2+110}")
    f.arr(f"M580,{Y2+110} L604,{Y2+110}")
    f.arr(f"M990,{Y2+110} L1014,{Y2+110}")

    # —— 访存 ——
    Y3 = 730
    f.group(30, Y3, 1420, 200, "访存 LSU + MMU", 150, C['ooo_bg'], C['ooo_st'], C['ooo_tag'],
            "AGU×2 · store 不投机 · TLB 无保护（RAS=0）")
    f.box(50, Y3+36, 300, 140, "LSU：AGU×2 + L1D", [
        ("· 2 load 或 1L+1S /cyc · 2×128b 读", C["txt"]),
        ("· L1D 64KB 4-way · load-to-use 4c", C["txt"]),
        ("· store 转发 6–7c（跨 16B +1~2c）", C["txt"]),
        ("· LSE 原子在 L1 争用下 43c（CASAL 实测）", C["txt"]),
        ("· 厂商称 ECC（无架构化证据）", R, 1),
    ], center=False)
    f.box(380, Y3+36, 320, 140, "LSQ（LQ + SQ）· STLF", [
        ("· store 不投机：退休后才写 L1D", C["txt"]),
        ("· load 乱序但先查 SQ（STLF）", C["txt"]),
        ("· STLF：CAM 匹配直转，不经 cache/PRF", C["txt"]),
        ("· STLF 段 ECC 全失明", R, 1),
        ("· （五款共同的 SDC 盲区）", C["sub"]),
    ], center=False)
    f.box(730, Y3+36, 330, 140, "MMU：TLB + PTW", [
        ("· iTLB 32 项全相联 · dTLB 32 项全相联", C["txt"]),
        ("· L2 TLB 1024 项 I/D 共用，命中 +11c", C["txt"]),
        ("· PTW 4KB/16KB/64KB 粒度", C["txt"]),
        ("· TLB 无保护披露（RAS=0）", R, 1),
        ("· 4KB×4=16KB 恰处 VIPT 别名临界（实测无别名）", C["sub"]),
    ], center=False)
    f.arr(f"M680,{Y3+100} L704,{Y3+100}")

    # —— 内存层级（chiplet L3 三模式 = 920 标志）——
    Y4 = 960
    f.group(30, Y4, 1420, 240, "内存层级 Memory（chiplet）", 200, C['mem_bg'], C['mem_st'], C['mem_tag'],
            "chiplet：2 计算 die(SCCL)+1 IO die，CoWoS · 每 die 8 CCL(4核簇) · Hydra 互联 · 距离 10/12/20/22")
    f.box(50, Y4+36, 240, 120, "L1-Dcache 64KB 4-way", [
        "load 54.6 / store 41.2 GB/s",
        "4c load-to-use（依赖链实测 2.87）",
        ("ECC 强度不可验证", R, 1),
        "L1←L2 ~32B/cyc（refill 可观测）",
    ])
    f.box(320, Y4+36, 250, 120, "L2 私有 512KB/核 8-way", [
        "10c · 64B · PoU",
        "实测 4.88ns（256KB 工作集）",
        ("厂商称 ECC（无证据）", R, 1),
        "load 42.8 GB/s（256KB）",
    ])
    f.box(600, Y4+36, 400, 178, "L3 / SLC 每 die 32MB", [
        ("· 8 bank×4MB · 15-way 伪随机", C["txt"]),
        ("· 128B 行（L1/L2 是 64B！）", C["txt"]),
        ("· tag 在簇侧 · 数据 bank 在 NoC 侧", C["txt"]),
        ("· 三模式 Shared/Private/Partition(默认)", GOLD, 1),
        ("· partition 近端 4MB ~36c → 全容量 >90c", C["txt"]),
        ("· 双核共享退化为全容量高延迟", C["txt"]),
    ], center=False, gold=True)
    f.box(1030, Y4+36, 390, 120, "DDR4-2933 ×8ch", [
        "每 die 读 ~63 GB/s",
        "空载 ~96ns · 实测 163.5ns（256MB）",
        ("Registered-DDR4 SECDED（ghes_edac 实证）", G, 1),
        "ce/ue 计数实测为 0",
    ])
    f.arr(f"M290,{Y4+96} L314,{Y4+96}")
    f.arr(f"M570,{Y4+96} L594,{Y4+96}")
    f.arr(f"M1000,{Y4+96} L1024,{Y4+96}")

    # —— RAS 横幅（红：裸奔平台）——
    f.banner(1240, "RAS / 保护状态（SDC 视角）——RAS=0，五款中敏感性最高", [
        ("架构化 RAS (ERR*/ESB/poison)", "无 —— ID_AA64PFR0_EL1.RAS = 0（EL0 实测）：无 ERR* 记录寄存器、无 ESB、无架构化 poison、无 FHI/ERI、无架构化错误注入", R),
        ("核内翻转归宿", "性能异常 / 崩溃 / 静默（SDC）——最后一类无任何架构级可见信号", R),
        ("厂商宣称冲突", "宣称 I$/D$ ECC、Memory Poisoning 与 RAS=0 冲突：即便有也是非架构化私有实现，SDC 实验不可依赖", R),
        ("平台级 RAS", "ACPI HEST/EINJ/BERT/ERST 全在（EINJ 368B 固件注入可用）· ghes_edac DDR SECDED · MPAM · SDEI", G),
        ("uncore 观测", "每 die L3C×8（back_invalid=一致性干扰）· HHA×2 · DDRC×4 · 需 perf_event_paranoid≤1 · 调频粒度=die 级", C["sub"]),
    ])


# ════════════════════════════════════════════════════════════════
# 2. 920f (HiSilicon 0xd22) — 黑盒实测，SVE512 无 LLC
# ════════════════════════════════════════════════════════════════
def draw_920f(f):
    Y = 130
    f.group(30, Y, 1420, 240, "前端 Fetch（规格未公开）", 210, C['fetch_bg'], C['fetch_st'], C['fetch_tag'],
            "分支预测器容量待测（bpbench 未完成）· 仅 AArch64 · CTR_EL0=0x9444c004（ERG=64B）")
    f.box(50, Y+36, 250, 130, "BPU（未公开）", [
        "BTB/RAS/间接预测容量",
        "均未测得（待 bpbench）",
        ("CSV2/3=1（推测攻击缓解在）", C["txt"]),
    ], unknown=True)
    f.box(340, Y+36, 210, 130, "L1-I-cache 32KB 4-way", [
        "64B 行（CTR 实测）",
        ("ECC/parity 未披露", R, 1),
        "（RAS=1 但无 TRM）",
    ])
    f.box(580, Y+36, 210, 130, "译码 / 重命名 / 派遣", [
        "宽度未公开",
        "仅 A64 指令集",
        "（无 AArch32）",
    ], unknown=True)
    f.box(820, Y+36, 330, 178, "SVE 512-bit + SME/SME2（五款唯一宽向量）", [
        ("· SVEver=1 · f32mm/f64mm/BF16=1 · 实测 VL=64B", C["txt"]),
        ("· SME2：f64f64/b16f32/f32f32/i8i32（fa64=0）", C["txt"]),
        ("· Z0–Z31 × 512b + 矩阵 tile = 新增大面积无保护数据面", R, 1),
        ("· SVE512 FMA 实测 ≥13.6 flop/cyc（理论 16）", C["txt"]),
        ("· 单向量翻转影响 64B 连续数据", R, 1),
    ], center=False, gold=True)
    f.box(1180, Y+36, 240, 130, "ISA 扩展（实测）", [
        "SHA1/2/512 · SHA3 · SM3/SM4",
        "LRCPC2/3 · i8mm · bf16 · RPRES",
        "WFXT · SVE2 全集 · AES · LSE",
        ("BTI=0 · MTE=0 · RNDR=0", R, 1),
    ], center=False)
    f.arr(f"M300,{Y+100} L334,{Y+100}", color=C['ctrl'], marker='arrC')
    f.arr(f"M550,{Y+100} L574,{Y+100}")
    f.arr(f"M790,{Y+100} L814,{Y+100}")
    f.arr(f"M1150,{Y+100} L1174,{Y+100}")

    Y2 = 400
    f.group(30, Y2, 1420, 300, "后端 OoO Execute（吞吐实测）", 210, C['ex_bg'], C['ex_st'], C['ex_tag'],
            "标量 FMA 2/cyc · NEON128 FMA 2/cyc · SVE512 FMA ≥2/cyc——三级向量吞吐阶梯全部双发")
    f.box(50, Y2+36, 300, 150, "标量 / NEON 通路", [
        ("· 标量 FMADD 8 链：8.0 Gflop/s = 4 flop/cyc", C["txt"]),
        ("· NEON128 8×2lane：13.5 Gflop/s ≈ 6.75", C["txt"]),
        ("· 标量 FMA 双端口实证（920 为 FP 单口怪点）", GOLD, 1),
        ("· 单核理论 128 Gflop/s（SVE512 FP64）", C["txt"]),
    ], center=False)
    f.box(380, Y2+36, 330, 178, "SVE512 数据通路", [
        ("· SVE512 8×8lane：27.2 Gflop/s 下限（~13.6）", C["txt"]),
        ("· 608 核节点理论 ~77.8 Tflop/s（FP64）", C["txt"]),
        ("· 单向量翻转影响 64B 连续数据", R, 1),
        ("· flopbench 修正版待复测（初版被编译器削链）", C["sub"]),
        ("· 全部数据面无保护披露", R, 1),
    ], center=False, gold=True)
    f.box(740, Y2+36, 300, 150, "PRF / ROB / 调度器（未公开）", [
        "容量/结构黑盒",
        "与五款一致：无任何保护披露",
        "FI 实验按 gem5 O3 通用模型注入",
    ], unknown=True)
    f.box(1070, Y2+36, 350, 150, "LSU / 访存", [
        ("· LSE 原子 · LRCPC2/3（LDAPR 系增强）", C["txt"]),
        ("· DC ZVA 64B", C["txt"]),
        ("· LSQ/store buffer 保护未披露（五款共同盲区）", R, 1),
        ("· 定频 2.0GHz（userspace 锁 MAX）→ 测量无变频噪声", C["sub"]),
    ], center=False)
    f.arr(f"M350,{Y2+110} L374,{Y2+110}")
    f.arr(f"M710,{Y2+110} L734,{Y2+110}")
    f.arr(f"M1040,{Y2+110} L1064,{Y2+110}")

    Y3 = 730
    f.group(30, Y3, 1420, 240, "内存层级 + MMU（无 LLC）", 210, C['mem_bg'], C['mem_st'], C['mem_tag'],
            "16 计算 NUMA + 16 无 CPU 内存节点（疑似 CXL/近存）· 跨 socket 距离 61–91 · 8×200GbE RoCE 聚合 1.6Tb/s")
    f.box(50, Y3+36, 250, 150, "L1-Dcache 32KB 8-way", [
        "64B 行 · 实测 ~5.0ns（≈10c）",
        ("8-way（同代 Neoverse 为 4-way）", GOLD, 1),
        ("ECC 未披露", R, 1),
        "容量 32KB < 920 的 64KB",
    ])
    f.box(330, Y3+36, 290, 150, "L2 私有 768KB 12-way", [
        "统一 I+D · 实测 ~8.7ns（≈17c）",
        ("五款中最大私有 L2（N3 可配 2MB 追平）", GOLD, 1),
        ("12-way 非常规（920:8 / N 系:8）", GOLD, 1),
        ("ECC 未披露", R, 1),
    ], gold=True)
    f.box(650, Y3+36, 300, 150, "无 L3 / LLC", [
        ("sysfs 无 index3 · CLIDR 陷阱实证", GOLD, 1),
        "SCN 网状远端 8–16MB → 45–90ns",
        "（网络侧缓存，非核侧 LLC）",
        ("少一级缓存 = 少一级 SDC 暴露面", C["txt"]),
    ], gold=True)
    f.box(980, Y3+36, 440, 150, "DRAM / NUMA", [
        "565GB · 16×31–33GB 计算节点",
        "远程 NUMA 实测 ~130ns",
        "node16–31 无 CPU 各 4GB（性质待确认：CXL? HBM?）",
        ("PMUv3 6 计数器 + SPE + AMU=1 · DIT=1", C["txt"]),
    ], center=False)
    f.arr(f"M300,{Y3+110} L324,{Y3+110}")
    f.arr(f"M620,{Y3+110} L644,{Y3+110}")
    f.arr(f"M950,{Y3+110} L974,{Y3+110}")

    Y4 = 1010
    f.group(30, Y4, 1420, 170, "MMU：TLB + PTW", 160, C['ooo_bg'], C['ooo_st'], C['ooo_tag'],
            "TLB 容量未测（缺口，待补）")
    f.box(50, Y4+36, 620, 110, "64KB 强制页（TGran4=0xf）", [
        ("· 单 TLB entry 翻转波及面 ×16（vs 4KB 页）——SDC 放大器", R, 1),
        ("· PAGESIZE=4096 是内核兼容层假象", C["txt"]),
        ("· 未被文献覆盖的放大器实验设计点", GOLD, 1),
    ], center=False, gold=True)
    f.box(700, Y4+36, 720, 110, "uncore 观测", [
        "171 perf 设备 = 8 SCCL×(4 DDRC+4 HHA+16 UC) + 14 SICL L3（hisi_sicl3_pa/h60pa）+ SPE + PCIe PTT",
        "隔离：isolcpus + nohz_full 覆盖 608 核，每 NUMA 留末核处理中断（FI 实验绑核须避开）",
        ("复现入口：dnode -l cn23154 / dattach -c '/home/share/suke/archprobe/...'（详见 920f.md §6）", C["sub"]),
    ], center=False)

    f.banner(1215, "RAS / 保护状态（SDC 视角）——RAS=1 但防御矩阵黑盒", [
        ("架构化 RAS", "ID_AA64PFR0_EL1.RAS = 1（实测）—— 有 ARMv8.2+ RAS 架构扩展，但防御矩阵黑盒", G),
        ("与 920 的关键代差", "ERR* 寄存器 / ESB / 架构化 poison 理论上存在 · 具体注入寄存器布局未知（无厂商 TRM）", C["txt"]),
        ("其他", "DIT=1（数据无关时间）· CSV2/3=1 · AMU=1 · 无 MTE（内存标签纠错不可用）", C["txt"]),
        ("SDC 实验定位", "RAS=1 但无文档 → 有防御潜力但强度未知；64KB 页 × TLB 注入是未被文献覆盖的放大器实验", R),
        ("未决项（920f.md §7 原文）", "SVE512 峰值复测 · 分支预测器容量（bpbench 中断过）· node16–31 内存节点性质（需 ddrc PMU 或 dmesg root）", C["sub"]),
    ])


# ════════════════════════════════════════════════════════════════
# 3. Neoverse N1 — TRM 全披露参照系
# ════════════════════════════════════════════════════════════════
def draw_n1(f):
    Y = 130
    f.group(30, Y, 1420, 240, "前端 Fetch（按序 · TRM §3.1）", 220, C['fetch_bg'], C['fetch_st'], C['fetch_tag'],
            "取指→译码→重命名→派遣 · A32/T32/A64 三指令集译码 · I$ 硬件一致性可配（COHERENT_ICACHE，推荐 L2=1MB）")
    f.box(50, Y+36, 260, 130, "程序流预测（TRM §7.3）", [
        "动态分支预测器 + BTB + 间接预测",
        "容量 TRM 未披露",
        ("Table 9-1 明示：BTB / GHB / BPIQ", R, 1),
        ("全部 None（无保护）", R, 1),
    ], center=False)
    f.box(340, Y+36, 220, 130, "L1-I-cache 64KB 4-way", [
        "64B 行 · 硬件一致性可配（§3.1.1）",
        ("tag: 1 parity/39b · data: SED/72b", G, 1),
        "错误→行失效重取（无数据丢失）",
    ])
    f.box(590, Y+36, 200, 130, "译码（§3.1.2）", [
        "A32 / T32 / A64",
        "NEON+FP 各态支持",
        ("AArch32 EL0（五款唯一）", GOLD, 1),
    ])
    f.box(820, Y+36, 200, 130, "重命名（§3.1.3）", [
        "寄存器重命名促乱序",
        "分发至各发射队列",
        ("PRF 保护无披露", R, 1),
    ])
    f.box(1050, Y+36, 180, 130, "发射（§3.1.4）", [
        "issue queues 暂存",
        "待派发指令",
        "（容量未披露）",
    ])
    f.box(1270, Y+36, 160, 130, "ETM（§2.2）", [
        "Embedded Trace",
        "Macrocell",
        "指令 trace only",
        ("N2/N3 为 ETE+TRBE 型", GOLD, 1),
    ], gold=True)
    f.arr(f"M310,{Y+100} L334,{Y+100}", color=C['ctrl'], marker='arrC')
    f.arr(f"M560,{Y+100} L584,{Y+100}")
    f.arr(f"M790,{Y+100} L814,{Y+100}")
    f.arr(f"M1020,{Y+100} L1044,{Y+100}")

    Y2 = 400
    f.group(30, Y2, 1420, 300, "后端 OoO Execute", 150, C['ex_bg'], C['ex_st'], C['ex_tag'],
            "INT 单元 + 向量单元（NEON+FP，可选 Crypto）· 写回经记分牌仲裁 · 推测错路径经 squash 回滚")
    f.box(50, Y2+36, 300, 150, "整数执行（§3.1.5）", [
        ("· 算术/逻辑数据处理 · ROB 128（公开规格）", C["txt"]),
        ("· LDAPR 系（RCpc v8.3，ISAR1 实证）", C["txt"]),
        ("· ALU 位翻转=纯 SDC 通路（无任何校验）", R, 1),
        ("· LOR：4 个 Limited Ordering Region 描述符", C["sub"]),
    ], center=False)
    f.box(380, Y2+36, 300, 150, "向量执行（§3.1.5）", [
        ("· NEON 128b SIMD + FP32/FP64", C["txt"]),
        ("· Crypto 可选（AES/SHA）· 无 SVE", C["txt"]),
        ("· FMA 树=时序违例重灾区", R, 1),
    ], center=False)
    f.box(710, Y2+36, 330, 150, "三级原子执行（§7.4.1）", [
        ("· near atomic：L1 命中且 unique 态，核内完成", C["txt"]),
        ("· far atomic：miss/共享 → CHI 接口送互联", C["txt"]),
        ("· 全簇 miss → DSU L3 分配执行（可配 L3 时）", C["txt"]),
        ("· CPUECTLR 可配各类原子倾向 near · PLDW/PRFM 提示", C["sub"]),
    ], center=False, gold=True)
    f.box(1080, Y2+36, 340, 150, "观测单元（§2.2）", [
        ("PMU + SPE + AMU", C["txt"]),
        ("TrustZone · PBHA", C["txt"]),
        ("Crypto 可选扩展", C["txt"]),
    ])
    f.arr(f"M350,{Y2+110} L374,{Y2+110}")
    f.arr(f"M680,{Y2+110} L704,{Y2+110}")

    Y3 = 730
    f.group(30, Y3, 1420, 240, "访存 LSU + MMU", 150, C['ooo_bg'], C['ooo_st'], C['ooo_tag'],
            "L1D 64KB 4-way VIPT · ECC per 32 bits · 两级 TLB")
    f.box(50, Y3+36, 330, 178, "LSU + L1D（§3.1.6/§7.4）", [
        ("· L1D 64KB 4-way VIPT 64B · ECC per 32 bits", C["txt"]),
        ("· 内部独占监视器（LL/SC）", C["txt"]),
        ("· transient/non-temporal 特化", C["txt"]),
        ("· write streaming 模式（§7.2.7）", C["txt"]),
        ("· L1 PHT 无保护（Table 9-1）", R, 1),
    ], center=False)
    f.box(410, Y3+36, 280, 130, "预取（§7.5）", [
        "数据预取器 + L1 PHT",
        ("PHT：Table 9-1 明示 None", R, 1),
        "（预取错地址多被掩盖，低危）",
    ])
    f.box(720, Y3+36, 700, 178, "MMU：两级 TLB（§6.2）", [
        ("· iTLB 48 项全相联（4K–32M）· dTLB 48 项全相联（4K–512M）· L1 命中 1c", C["txt"]),
        ("· L2 TLB 1280 项 5-way 共享（§6.2.3）· 4 并行 walk / 2 lookup · 连续 6 miss 停顿", C["txt"]),
        ("· L1 TLB 用触发器实现 → 无 cache 保护（TRM 原文注释）", R, 1),
        ("· MMUTC 2-bit 交错 parity/71b", C["txt"]),
    ], center=False)

    Y4 = 1010
    f.group(30, Y4, 1420, 240, "内存层级（L1 → L2 → DSU）", 230, C['mem_bg'], C['mem_st'], C['mem_tag'],
            "异步 CPU bridge 连 DSU · 组件常在 · 与 DSU 间仅一致性接口可配同步")
    f.box(50, Y4+36, 280, 178, "L1-Dcache 64KB 4-way VIPT", [
        "64B 行 · ECC per 32 bits（§3.1.6）",
        ("Table 9-1: tag SECDED 42+7b", G, 1),
        ("data SECDED 32+1 poison+7b", G, 1),
        "poison 粒度 64b（L1D 特例 32b）",
        "UC→evict 纠正回填（§9.2）",
    ])
    f.box(360, Y4+36, 330, 178, "L2 私有 256/512/1024KB 8-way", [
        "私有统一（§3.1.7）· 2 bank",
        ("tag SECDED（50–57 tag+7 ECC）", G, 1),
        ("data SECDED 8 ECC/64b", G, 1),
        ("TQ 24/36/48 项可配（2bank×12/18/24）", GOLD, 1),
        ("L2 victim 阵列：None（Table 9-1）", R, 1),
    ])
    f.box(720, Y4+36, 330, 178, "DSU（簇共享单元）", [
        "≤4 核 + 可选 L3 / snoop filter",
        "单核直连配置可无 L3/SCU",
        "L3 保护 = DSU TRM 范围",
        "（core TRM 不披露）",
    ])
    f.box(1080, Y4+36, 340, 150, "SoC 侧", [
        "48-bit PA · GICv4.1 CPU 接口",
        "PMU + SPE + AMU（§2.2）",
        "TrustZone · PBHA",
        "Crypto 可选扩展",
    ])
    f.arr(f"M330,{Y4+110} L354,{Y4+110}")
    f.arr(f"M690,{Y4+110} L714,{Y4+110}")
    f.arr(f"M1050,{Y4+110} L1074,{Y4+110}")

    f.banner(1290, "RAS 扩展（TRM §9 全披露）——五款中的透明度参照系", [
        ("架构化机制", "ERR<n>FR/CTLR/MISC0-1+PFGF · SEA/AEA/ERI · FHI/ERI 中断 · ESB 指令 · poison 传播（64b 粒度，L1D 32b）", G),
        ("错误注入（§9.7）", "CE/DE/UC/RE 四类全可注入（ERRSELR_EL1 选 record 0 + ERR0CTLR），注入不破坏真实 RAM 数据/校验逻辑", G),
        ("tag UC 处置", "失效整行 + ERI 通知（地址/一致性态未知，无法 poison，软件被告知数据可能丢失——显式非静默）", C["txt"]),
        ("SDC 判定基准", "TRM §9.1 直接给出 SDC 定义（silent data corruptions）——本仓库 SDC 判定基准的引用源", GOLD),
        ("明示无保护清单", "L1 BTB · GHB · BPIQ · L1 PHT · MMU replacement/biased-repl · L2 victim · L1 TLB（flops）", R),
        ("SED 弱点", "I$ tag parity+data SED（弱于 L1D SECDED）→ TRM 承认 SED 双位错 might cause data corruption", R),
    ], fill="#f0fdf4", stroke=C["green"], tcol=C["green"])


# ════════════════════════════════════════════════════════════════
# 4. Neoverse N2 — L0 MOP + SVE2 + MMUTC SED
# ════════════════════════════════════════════════════════════════
def draw_n2(f):
    Y = 130
    f.group(30, Y, 1420, 240, "前端 Fetch（按序 · TRM §3.1 p40）", 250, C['fetch_bg'], C['fetch_st'], C['fetch_tag'],
            "L1I 64KB 4-way 64B · iTLB 全相联（4K/16K/64K/2M 原生页）· A32/T32/A64 全译码（AArch32 全保留）")
    f.box(50, Y+36, 250, 130, "程序流预测（§7.3 p66）", [
        "BTB（taken 目标）+ 方向预测器（历史）",
        "返回栈 + 静态预测器 + 间接预测器",
        ("BTB/GHB/BIM 保护未列（Table 11-1）", R, 1),
        "A32↔T32 状态切换分支也预测",
    ], center=False)
    f.box(330, Y+36, 200, 130, "L1-I-cache 64KB 4-way", [
        "64B 行 · I$ 硬件一致性（§7.4）",
        ("tag/data: SED parity（Table 11-1）", G, 1),
        "投机取指行为 §7.2 约束",
    ])
    f.box(560, Y+36, 310, 178, "L0 MOP 缓存（§3.1 p40）", [
        ("1536 项 · 4-way 倾斜相联（skewed）", GOLD, 1),
        ("存已译码+已优化指令", C["txt"]),
        ("data: SED（Table 11-1）", G, 1),
        ("弱保护 × 高命中 × 指令面", R, 1),
        ("（五款唯一 MOP 结构）", GOLD, 1),
    ], center=False, gold=True)
    f.box(900, Y+36, 250, 130, "重命名 / 发射（§3.1）", [
        "重命名促乱序",
        "分发至各发射队列",
        ("PRF 保护未披露", R, 1),
    ])
    f.box(1190, Y+36, 230, 130, "ETE + TRBE", [
        "Embedded Trace Ext",
        "+ Trace Buffer",
        "（替代 N1 ETM 型式）",
    ], gold=True)
    f.arr(f"M300,{Y+100} L324,{Y+100}", color=C['ctrl'], marker='arrC')
    f.arr(f"M530,{Y+100} L554,{Y+100}")
    f.arr(f"M870,{Y+100} L894,{Y+100}")
    f.arr(f"M1150,{Y+100} L1174,{Y+100}")

    Y2 = 400
    f.group(30, Y2, 1420, 300, "后端 OoO Execute（TRM §3.1 p41-42）", 260, C['ex_bg'], C['ex_st'], C['ex_tag'],
            "整数执行 + 向量执行（FPU · NEON · SVE/SVE2 128b 向量长度 · Crypto 可选含 SM3/SM4）")
    f.box(50, Y2+36, 290, 150, "整数执行单元", [
        ("· 算术/逻辑数据处理（§3.1）", C["txt"]),
        ("· RNG 支持（§16，RNDR/RNDRRS）", C["txt"]),
        ("· ALU 数据通路无保护披露", R, 1),
    ], center=False)
    f.box(370, Y2+36, 350, 178, "向量执行：SVE / SVE2（§14）", [
        ("· 向量长度 128-bit（与 NEON 等宽，非宽向量）", C["txt"]),
        ("· SVE2 全集：predication/gather/permute", C["txt"]),
        ("· 五款 Neoverse 侧第一个 SVE 世代（920f 为 512b）", GOLD, 1),
    ], center=False, gold=True)
    f.box(750, Y2+36, 330, 178, "Crypto 扩展（可选 · §3.1）", [
        ("· AES · SHA-1/224/256/384/512", C["txt"]),
        ("· SM3/SM4（v8.2-SM）· 有限域（GCM/ECC）", C["txt"]),
        ("· 独立授权许可（实现时可含/不含）", C["sub"]),
    ], center=False)
    f.box(1120, Y2+36, 300, 150, "LSU + L1D（§8 p69-72）", [
        ("· L1D 64KB 4-way 64B · tag/data SECDED", G),
        ("· 独占监视器（§8.3）· DC ZVA 64B", C["txt"]),
        ("· write streaming（read allocate）L1+L2 双级（§8.5）", GOLD, 1),
    ], center=False)
    f.arr(f"M340,{Y2+110} L364,{Y2+110}")
    f.arr(f"M720,{Y2+110} L744,{Y2+110}")

    Y3 = 730
    f.group(30, Y3, 1420, 240, "预取 + MMU", 150, C['ooo_bg'], C['ooo_st'], C['ooo_tag'],
            "两级 TLB + MMUTC SED（Table 6-1 p57-58）")
    f.box(50, Y3+36, 360, 130, "预取器（§8.4）", [
        ("load 侧 VA → L1+L2 · store 侧 PA → 仅 L2（分裂式）", C["txt"]),
        ("+ TLB 预取器 · region 预取器（CPUECTLR 可控）", C["txt"]),
    ], center=False)
    f.box(440, Y3+36, 480, 178, "MMU：两级 TLB + MMUTC（§6.1）", [
        ("· iTLB 48 项全相联 · dTLB 44 项全相联 · L2 TLB 1280 项 5-way I/D 共享", C["txt"]),
        ("· TRBE TLB 2 项 · 翻译表预取器（ECtlR 可关）· L2 命中 +3c 罚", C["txt"]),
        ("· MMUTC：SED（Table 11-1）——N1 仅 2-bit 交错 parity，N2 升级", GOLD, 1),
    ], center=False)
    f.box(950, Y3+36, 470, 150, "观测单元", [
        ("48-bit PA · PMU 6 计数器（§3.1 p42）", C["txt"]),
        ("SPE（v8.4 可选实现）· AMU", C["txt"]),
        ("GIC CPU 接口 · RNG", C["txt"]),
        ("Debug/ELA 可选（§2.5）", C["sub"]),
    ], center=False)

    Y4 = 1010
    f.group(30, Y4, 1420, 240, "内存层级（L1 → L2 → DSU-110）", 250, C['mem_bg'], C['mem_st'], C['mem_tag'],
            "异步 CPU bridge 连 DSU-110（缓冲+同步核与簇）· 组件常在（All components always present §3）")
    f.box(50, Y4+36, 330, 178, "L1-Dcache 64KB 4-way", [
        "64B 行（§3.1 p42）",
        ("tag/data: SECDED（Table 11-1）", G, 1),
        "双位错=检出/上报/延迟",
        ("dirty 行双位错→数据可能丢失（显式）", C["txt"]),
    ])
    f.box(410, Y4+36, 330, 178, "L2 私有 512KB/1024KB 8-way", [
        "统一 I+D（§3.1 p42 · §9）",
        ("tag/data: SECDED", G, 1),
        ("L2 TQ：SECDED（表 11-1 唯一队列类保护）", G, 1),
        ("victim 表未列（N1 明示 None，N2 未披露）", C["txt"]),
    ])
    f.box(770, Y4+36, 330, 178, "DSU-110 簇", [
        "L3/SCU/snoop filter = DSU TRM 范围",
        "CPU bridge 异步（频/电/面积解耦）",
        "DSU 依赖特性见 TRM §2.3",
    ])
    f.box(1130, Y4+36, 290, 130, "SoC 侧", [
        "48-bit PA",
        "GIC CPU 接口",
        "RNG · Debug/ELA",
    ])

    f.banner(1290, "RAS 扩展（TRM §11 p96-100）——含至 Armv9.0-A 全量", [
        ("保护矩阵（Table 11-1）", "SECDED = L1D tag/data · L2 tag/data · L2 TQ；SED = L1I tag/data · L0 MOP · MMUTC", G),
        ("TRM 原文承认", "SED RAM 双位错 core does not detect … might cause data corruption——I$/MOP/MMUTC 是承认的 SDC 通道", R),
        ("错误遏制（§11.2）", "数据错误经 poison 传播不静默扩散 · evict 双错可 poison · L1D/L2 tag 不可遏制错误（UC 声明）", C["txt"]),
        ("错误注入（§11.5）", "CE（L1D 单 ECC）· DE（L1→L2 evict 双 ECC / snoop）· UC（L1 tag evict 后双 ECC）· ERR0PFGCDN 倒计数", G),
        ("报告机制", "FHI=nCOREFAULTIRQ · ERI=nCOREERRIRQ · 消费时 SEA/AEA/ERI · MEMORY_ERROR PMU 事件联动 · ESB · Node 0=L1+L2", G),
        ("SDC 视角", "N2 相对 N1 的增量 = MMUTC SED + MOP SED；新增 MOP 是弱保护×高命中率×指令面三重叠加的独立注入靶点", GOLD),
    ], fill="#f0fdf4", stroke=C["green"], tcol=C["green"])


# ════════════════════════════════════════════════════════════════
# 5. Neoverse N3 — 分裂 TLB + aux tag + ECC granule，防御最厚
# ════════════════════════════════════════════════════════════════
def draw_n3(f):
    Y = 130
    f.group(30, Y, 1420, 240, "前端 Fetch（按序 · TRM §2.1 p31）", 240, C['fetch_bg'], C['fetch_st'], C['fetch_tag'],
            "L1I 32KB 或 64KB（可配）4-way 64B · iTLB 全相联 32 项 · 仅 A64 译码（无 AArch32）· 动态分支预测器单列组件")
    f.box(50, Y+36, 260, 130, "程序流预测（§6.3 p59）", [
        "BTB + BP 方向预测器（历史）",
        "返回栈（BL/BLR* push · RET* pop）",
        "静态 + 间接预测器",
        "不预测：ERET/SVC/HVC/SMC",
    ], center=False)
    f.box(340, Y+36, 230, 130, "L1-I-cache 32/64KB 4-way", [
        "64B 行（§2.1 · §1.2 可配）",
        ("tag/data: SED（Table 10-1）", G, 1),
        "硬件一致性 §6.4（与 L2 弱包含）",
    ])
    f.box(600, Y+36, 220, 130, "译码（§2.1）", [
        ("仅 A64（无 A32/T32）", GOLD, 1),
        "AArch64 内部格式",
        ("无 MOP 结构（N2 删减）", C["txt"]),
    ], gold=True)
    f.box(850, Y+36, 220, 130, "重命名 / 发射", [
        "重命名 + issue queues",
        "（§2.1 组件图）",
        ("PRF 保护未披露", R, 1),
    ])
    f.box(1100, Y+36, 320, 130, "MPAM（§1.1 Cache features）", [
        "Memory System Resource",
        "Partitioning & Monitoring",
        "缓存/带宽 QoS 硬件分区",
        ("（920 平台级 MPAM 有 ACPI 表；N3 为核内特性）", C["sub"]),
    ], center=False, gold=True)
    f.arr(f"M310,{Y+100} L334,{Y+100}", color=C['ctrl'], marker='arrC')
    f.arr(f"M570,{Y+100} L594,{Y+100}")
    f.arr(f"M820,{Y+100} L844,{Y+100}")

    Y2 = 400
    f.group(30, Y2, 1420, 300, "后端 OoO Execute（§2.1 p31-32）", 260, C['ex_bg'], C['ex_st'], C['ex_tag'],
            "整数执行 + 向量执行（NEON+FP · SVE/SVE2 128b · Crypto 可选含 SHA-3/SM3/SM4）· 平衡性能/低功耗/面积受限定位")
    f.box(50, Y2+36, 290, 150, "整数执行单元", [
        ("· 算术/逻辑数据处理（§2.1）", C["txt"]),
        ("· RNG（§16）· Utility bus（§11）", C["txt"]),
        ("· ALU 数据通路无保护披露", R, 1),
    ], center=False)
    f.box(370, Y2+36, 350, 178, "向量执行：SVE / SVE2（§14）", [
        ("· 向量长度 128-bit · NEON+FP32/FP64", C["txt"]),
        ("· Crypto：AES · SHA-1/2 · SHA-3 · SM3/SM4", C["txt"]),
        ("· EOR3/XAR/BCAX 随 SVE2 免费（免 Crypto 授权）", C["txt"]),
    ], center=False)
    f.box(750, Y2+36, 350, 178, "L2 预取引擎（VA + PC 双源）", [
        ("· §8 L2 内存系统：虚拟地址 + 程序计数器", C["txt"]),
        ("· 各引擎分别向 L2 预取（next-line/stride 类）", C["txt"]),
        ("· N2 为 load VA / store PA 分裂预取，N3 改双源引擎", GOLD, 1),
    ], center=False, gold=True)
    f.box(1130, Y2+36, 290, 150, "观测单元", [
        ("PMU 6 或 20 计数器（可配）", GOLD, 1),
        "SPE（§22 v8.7）· ETE+TRBE",
        "AMU（§21）· ELA 组件化",
    ])
    f.arr(f"M340,{Y2+110} L364,{Y2+110}")
    f.arr(f"M720,{Y2+110} L744,{Y2+110}")

    Y3 = 730
    f.group(30, Y3, 1420, 240, "访存 + MMU（分裂式 L2 TLB）", 250, C['ooo_bg'], C['ooo_st'], C['ooo_tag'],
            "L1D 32/64KB 可配 4-way 64B · tag/data/aux tag 全 SECDED · LSE 原子在 L1 内存系统实现（§7.3）")
    f.box(50, Y3+36, 360, 178, "LSU + L1D（§7 p62-65）", [
        ("· L1D 32/64KB（可配）4-way 64B", C["txt"]),
        ("· tag/data/aux tag 全 SECDED", G, 1),
        ("· LSE 原子在 L1 内存系统实现（§7.3）", C["txt"]),
        ("· 独占监视器（§7.4）· write streaming（§7.2）", C["txt"]),
        ("· 预取（§7.5）", C["sub"]),
    ], center=False)
    f.box(440, Y3+36, 480, 178, "MMU：分裂式 L2 TLB + walk cache（§5.1 p50 Table 5-1）", [
        ("· iTLB 32 项 · dTLB 48 项（全相联）· SPE TLB 1 项 · TRBE TLB 1 项", C["txt"]),
        ("· small-page TLB（4K/16K/64K）：6-way 1536 项（reduced-area 4-way 1024）", GOLD, 1),
        ("· medium-page TLB（2M/32M/512M）：4-way 256 项 + walk cache", GOLD, 1),
        ("· TLB：SED（Table 10-1，措辞从 N2 的 MMUTC 升级为 TLB）", G, 1),
    ], center=False)
    f.box(950, Y3+36, 470, 150, "内存层级补充", [
        ("单核 Direct connect 配置无 L3/SCU/snoop filter（§1 图 1-1）", C["txt"]),
        ("CPU bridge 连 DSU-120", C["txt"]),
        ("48-bit VA/PA（§1.1）", C["txt"]),
    ], center=False)

    Y4 = 1010
    f.group(30, Y4, 1420, 240, "内存层级（L1 → L2 → DSU-120 Direct connect）", 320, C['mem_bg'], C['mem_st'], C['mem_tag'],
            "单核 Direct connect 配置无 L3/SCU/snoop filter · CPU bridge 连 DSU-120")
    f.box(50, Y4+36, 350, 178, "L1-Dcache 32/64KB 4-way", [
        "64B 行（§2.1 · §9.1 编码验证 4-way）",
        ("tag/data: SECDED", G, 1),
        ("aux tag: SECDED（Table 10-1 新增行）", GOLD, 1),
        "UC 双位错=检出并上报/延迟（显式非静默）",
    ])
    f.box(430, Y4+36, 380, 178, "L2 私有 128KB–2MB 8-way 2-bank", [
        "PIPT · 动态偏置替换策略（Table 8-1）",
        ("tag/data: SECDED · TQ 亦 SECDED", G, 1),
        ("ECC granule 可配 128/256 bit（§1.2）", GOLD, 1),
        ("五款唯一可配纠错粒度", GOLD, 1),
    ])
    f.box(840, Y4+36, 300, 178, "DSU-120（Direct connect）", [
        ("CHI Issue E 接口", GOLD, 1),
        ("256-bit 读/写通道宽", GOLD, 1),
        "单核配置：无 L3 / 无 SCU",
        "（L3 保护 = DSU TRM 范围）",
    ], gold=True)
    f.box(1170, Y4+36, 250, 130, "SoC 侧", [
        "48-bit VA/PA（§1.1）",
        "GIC CPU 接口 · RNG",
        "ELA-600 可选（§1.2）",
    ])

    f.banner(1290, "RAS 扩展（TRM §10 p76-80）——含至 Armv9.2-A · 五款中防御矩阵最厚", [
        ("保护矩阵（Table 10-1）", "SECDED = L1D tag / aux tag / data · L2 tag/data · L2 TQ；SED = L1I tag/data · TLB（措辞从 N2 的 MMUTC 升级为 TLB）", G),
        ("错误遏制（§10.2）", "poison 传播 + evict 双错 poison + ESB 隔离不精确异常 · L1D/L2 tag UC 不可遏制声明与 N2 一致", C["txt"]),
        ("错误注入（§10.5）", "CE（L1D 单 ECC）· DE（L1→L2 evict/snoop 双 ECC）· UC（L1 和 L2 tag evict 后双 ECC——比 N2 的仅 L1 tag 扩展）", G),
        ("寄存器风格", "带 _EL1 后缀（ER1PFGCDN_EL1，RASv1.1 风格）· FHI/ERI · SEA/AEA/ERI · MEMORY_ERROR PMU 事件", GOLD),
        ("Node 0 覆盖", "明确覆盖 L1 + L2 + MMU/TLB（N2 为 L1+L2；N3 把地址翻译部件纳入 RAS 节点）", GOLD),
        ("SDC 视角", "披露范围内相对敏感性最低——TLB/翻译路径在 N3 获 SED；残余弱点：SED 类双位错仍是 corruption 通道；执行单元/PRF/LSQ 依旧无披露", G),
    ], fill="#f0fdf4", stroke=C["green"], tcol=C["green"])


LEGEND = [
    ('flow', '指令/数据流'), ('ctrl', '控制流'), ('gold', '独有/标志性'),
    ('unknown', '未公开/黑盒'), ('sdc', 'SDC 高危/无保护'),
]

SPECS = [
    dict(slug='kunpeng920', w=1480, h=1400,
         title='Kunpeng 920 · TaiShan v110 微架构功能图（ARMv8.2-A · 4 宽乱序 · 2.6GHz 实测）',
         subtitle='布局 = 920 实测结构：前端 4 宽无 uop-cache → 三类统一调度器 → chiplet 三模式 SLC。红=SDC 高危（无架构 RAS）· 数据出处：kunpeng920_microarchitecture.md 本机实测 + 公开资料',
         legend=LEGEND, draw=draw_920),
    dict(slug='920f', w=1480, h=1400,
         title='920f · HiSilicon part 0xd22 微架构功能图（ARMv9 · SVE512+SME2 · 黑盒实测）',
         subtitle='布局 = 黑盒结构：大量未公开（灰虚线）+ SVE512/SME2 宽向量金卡 + 无 LLC 扁平层级 + 64KB 强制页。出处：920f.md NSCC cn23154 实测',
         legend=LEGEND, draw=draw_920f),
    dict(slug='neoverse-n1', w=1480, h=1450,
         title='Arm Neoverse N1 微架构功能图（ARMv8.2-A · 超标量乱序 · DSU）',
         subtitle='布局 = N1 TRM 组件结构（章节号随文标注）：三指令集译码 + ETM + 三级原子 + 两级 TLB（L1 flops）。出处：Neoverse N1 TRM 100616_0401_02',
         legend=LEGEND, draw=draw_n1),
    dict(slug='neoverse-n2', w=1480, h=1450,
         title='Arm Neoverse N2 微架构功能图（Armv9.0-A · 超标量乱序 · DSU-110）',
         subtitle='布局 = N2 增量结构：L0 MOP cache 前端金卡（五款唯一）+ SVE2 首世代 + MMUTC SED 升级。出处：Neoverse N2 TRM 102099_0003_06',
         legend=LEGEND, draw=draw_n2),
    dict(slug='neoverse-n3', w=1480, h=1450,
         title='Arm Neoverse N3 微架构功能图（Armv9.2-A · 平衡性能核 · DSU-120 Direct connect）',
         subtitle='布局 = N3 防御结构：分裂式 L2 TLB（small 1536 + medium 256）+ aux tag + ECC granule 可配 + MPAM。出处：Neoverse N3 TRM 107997_0001_03',
         legend=LEGEND, draw=draw_n3),
]

if __name__ == '__main__':
    import sys
    for s in SPECS:
        out = build_fig(s, f"{s['slug']}_tmp.svg")
        print("built", out)
