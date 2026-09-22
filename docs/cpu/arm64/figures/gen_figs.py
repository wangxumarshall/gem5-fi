#!/usr/bin/env python3
"""统一模板五款 CPU 微架构功能图生成器。

风格 token 严格取自 sdc-fig-arm64.html（通用模板）：
  - 组背景: Fetch #eaf2fb / OoO #eaf6ee / Execute #fdf2e5 / Memory #f1edfb
  - 组标题签: 深色圆角小条 + 白字
  - 模块盒: 白底 #7c93a8 描边 1.4, rx=6
  - 箭头: #5a6b7c, 1.6
  - 子区(IEX/LSU/FSU): #fff8ef 底 #e0b98a 描边
语义扩展（SDC 用途，模板基础上的三种状态样式）：
  - ★ 金粗框 #b45309 3px  = 该芯片独有/标志性部件
  - 灰虚线盒             = 未公开/无该部件（黑盒或结构性缺失）
  - 绿色小字 ✓/✗         = 保护状态标注（RAS 横幅内为主）
"""

FONT = "system-ui,'PingFang SC','Noto Sans CJK SC','Microsoft YaHei',sans-serif"
C = dict(
    fetch_bg="#eaf2fb", fetch_st="#a9c9ec", fetch_tag="#4a5f78",
    ooo_bg="#eaf6ee", ooo_st="#a9d9bc", ooo_tag="#3f7a58",
    ex_bg="#fdf2e5", ex_st="#edcba0", ex_tag="#a05a2c",
    mem_bg="#f1edfb", mem_st="#cfc0ef", mem_tag="#6d5aa0",
    box_st="#7c93a8", sub_bg="#fff8ef", sub_st="#e0b98a",
    arrow="#5a6b7c", txt="#1f2937", sub="#6b7280",
    gold="#b45309", unknown_st="#9ca3af", green="#047857", red="#b91c1c",
)

def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

class Fig:
    def __init__(self, slug, title, subtitle, w=1520, h=980):
        self.w, self.h = w, h
        self.buf = []
        self.slug = slug
        self.title = title
        self.subtitle = subtitle
        self._hdr()

    def _hdr(self):
        w, h = self.w, self.h
        self.buf.append(
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" font-family="{FONT}">'
        )
        self.buf.append(f'  <defs>'
                        f'<marker id="arr" markerWidth="11" markerHeight="9" refX="9.5" refY="4.5" orient="auto" markerUnits="userSpaceOnUse"><path d="M0,0 L11,4.5 L0,9 Z" fill="{C["arrow"]}"/></marker>'
                        f'<marker id="arrR" markerWidth="11" markerHeight="9" refX="1.5" refY="4.5" orient="auto-start-reverse" markerUnits="userSpaceOnUse"><path d="M11,0 L0,4.5 L11,9 Z" fill="{C["arrow"]}"/></marker>'
                        f'</defs>')
        self.buf.append(f'  <rect x="0" y="0" width="{w}" height="{h}" fill="#ffffff"/>')
        self.buf.append(f'  <text x="30" y="32" font-size="20" font-weight="700" fill="{C["txt"]}">{esc(self.title)}</text>')
        self.buf.append(f'  <text x="30" y="54" font-size="12.5" fill="{C["sub"]}">{esc(self.subtitle)}</text>')
        # legend (arm64 风格延伸)
        self.buf.append(f'  <g font-size="11.5">')
        self.buf.append(f'    <rect x="30" y="66" width="760" height="40" rx="6" fill="#f7f9fb" stroke="#c6d2dd"/>')
        self.buf.append(f'    <line x1="44" y1="86" x2="72" y2="86" stroke="{C["arrow"]}" stroke-width="1.8" marker-end="url(#arr)"/><text x="78" y="90" fill="{C["txt"]}">指令/数据流</text>')
        self.buf.append(f'    <rect x="196" y="79" width="14" height="14" fill="#fffbeb" stroke="{C["gold"]}" stroke-width="2.6"/><text x="216" y="90" fill="{C["gold"]}" font-weight="600">★ 独有/标志性</text>')
        self.buf.append(f'    <rect x="330" y="79" width="14" height="14" fill="#f7f9fb" stroke="{C["unknown_st"]}" stroke-width="1.3" stroke-dasharray="4,3"/><text x="350" y="90" fill="{C["sub"]}">未公开/黑盒/无</text>')
        self.buf.append(f'    <text x="490" y="90" fill="{C["green"]}">✓=有保护披露</text>')
        self.buf.append(f'    <text x="590" y="90" fill="{C["red"]}">✗=无保护/未知（SDC 暴露）</text>')
        self.buf.append(f'  </g>')

    # ---------- 基元 ----------
    def group(self, x, y, w, h, tag, tag_w, bg, st, tag_fill, sub=None):
        self.buf.append(f'  <rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10" fill="{bg}" stroke="{st}" stroke-width="1.4"/>')
        self.buf.append(f'  <rect x="{x}" y="{y-22}" width="{tag_w}" height="22" rx="5" fill="{tag_fill}"/>')
        self.buf.append(f'  <text x="{x+10}" y="{y-6.5}" font-size="14" fill="#ffffff" font-weight="600">{esc(tag)}</text>')
        if sub:
            self.buf.append(f'  <text x="{x+tag_w+14}" y="{y-7}" font-size="13" fill="{tag_fill}" font-style="italic">{esc(sub)}</text>')

    def box(self, x, y, w, h, lines, gold=False, unknown=False, fs=13.5, green=None):
        """白盒模块; lines=[主行, 副行...]; gold=★独有; unknown=灰虚线; green='✓ SECDED' 之类尾注"""
        sw = '3' if gold else '1.4'
        st = C["gold"] if gold else (C["unknown_st"] if unknown else C["box_st"])
        dash = ' stroke-dasharray="5,4"' if unknown else ''
        self.buf.append(f'  <rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" fill="{"#f7f9fb" if unknown else "#ffffff"}" stroke="{st}" stroke-width="{sw}"{dash}/>')
        cx = x + w / 2
        n = len(lines) + (1 if green else 0)
        line_h = 17 if n > 2 else 19
        total = line_h * n
        y0 = y + h / 2 - total / 2 + line_h * 0.72
        for i, ln in enumerate(lines):
            fill = C["sub"] if i > 0 else C["txt"]
            size = fs if i == 0 else fs - 1.5
            weight = ' font-weight="600"' if (i == 0 and len(lines) > 1) else ''
            self.buf.append(f'  <text x="{cx}" y="{y0 + i * line_h}" font-size="{size}" fill="{fill}" text-anchor="middle"{weight}>{esc(ln)}</text>')
        if green:
            self.buf.append(f'  <text x="{cx}" y="{y0 + len(lines) * line_h}" font-size="{fs-1.5}" fill="{C["green"] if green.startswith("✓") else C["red"]}" text-anchor="middle">{esc(green)}</text>')

    def text(self, x, y, s, fs=13, fill=None, anchor="middle", bold=False, italic=False):
        fill = fill or C["txt"]
        extra = ''
        if bold: extra += ' font-weight="600"'
        if italic: extra += ' font-style="italic"'
        self.buf.append(f'  <text x="{x}" y="{y}" font-size="{fs}" fill="{fill}" text-anchor="{anchor}"{extra}>{esc(s)}</text>')

    def arr(self, d, dashed=False):
        dash = ' stroke-dasharray="5,4"' if dashed else ''
        self.buf.append(f'  <path d="{d}" fill="none" stroke="{C["arrow"]}" stroke-width="1.6"{dash} marker-end="url(#arr)"/>')

    def arr2(self, d):  # 双向
        self.buf.append(f'  <path d="{d}" fill="none" stroke="{C["arrow"]}" stroke-width="1.6" marker-start="url(#arrR)" marker-end="url(#arr)"/>')

    def save(self, path):
        self.buf.append('</svg>')
        open(path, 'w').write('\n'.join(self.buf) + '\n')
        return path

# ============================================================
# 五款芯片数据（全部来自已核验的 findings：TRM 原文 / 本机实测）
# 字段: fetch/ooo/iex/lsu/fsu/mmu/l2 各组 box 列表
# box 元组: (lines[], gold, unknown, green_note)
# ============================================================

def build_fig(spec, out_path):
    f = Fig(spec['slug'], spec['title'], spec['subtitle'])
    Y0 = 120  # 内容起始 y（避开 legend）

    # ---------- 组背景（arm64 模板布局） ----------
    f.group(40,  Y0+2,   515, 345, "取指与前段 Fetch", 210, C['fetch_bg'], C['fetch_st'], C['fetch_tag'], spec['fetch_note'])
    f.group(570, Y0+180, 470, 300, "OoO 译码 · 重命名 · 分发", 225, C['ooo_bg'], C['ooo_st'], C['ooo_tag'], spec['ooo_note'])
    f.group(1080, Y0+2,  400, 640, "执行单元 Execute", 160, C['ex_bg'], C['ex_st'], C['ex_tag'], spec['ex_note'])
    f.group(40,  Y0+700, 1440, 128, "访存与一致性 Memory", 230, C['mem_bg'], C['mem_st'], C['mem_tag'])

    # ---------- Fetch 组（模板坐标） ----------
    x, y = 40, Y0
    f.box(105+x-40, 70+y-40, 170, 44, spec['ifu'])
    f.box(65,  160+y-40, 115, 42, spec['bre'])
    f.box(210, 160+y-40, 100, 42, spec['bp'])
    f.box(85,  250+y-40, 210, 44, spec['itlb'])
    f.box(60,  330+y-40, 260, 50, spec['l1i'])
    # 指令队列
    f.text(465, 144+y-40, spec['iq'][0], 14, C['sub'])
    f.text(465, 164+y-40, "Instr", 15)
    f.text(465, 184+y-40, "queue", 15)

    # ---------- OoO 组 ----------
    ox, oy = 570, Y0+180
    f.box(590-570+ox, 210-200+oy-180+180, 130, 46, spec['idec'])      # 590,210
    f.box(745, 210-200+oy, 130, 46, spec['iren'])
    f.box(900, 210-200+oy, 120, 46, spec['idisp'])
    f.box(745, 275-200+oy, 130, 70, spec['sync'])
    f.box(590, 370-200+oy, 130, 46, spec['fdec'])
    f.box(745, 370-200+oy, 130, 46, spec['fren'])
    f.box(900, 370-200+oy, 120, 46, spec['fdisp'])

    # ---------- Execute 组: IEX / LSU / FSU 子区 ----------
    ex, ey = 1080, Y0+2
    # IEX
    f.buf.append(f'  <rect x="1090" y="{70+ey-42}" width="380" height="250" rx="8" fill="{C["sub_bg"]}" stroke="{C["sub_st"]}" stroke-width="1.3"/>')
    f.text(1102, 92+ey-42+30, "IEX", 16, C['ex_tag'], "start", bold=True)
    f.box(1102, 100+ey-42, 120, 36, spec['iq_a1'])
    f.box(1102, 150+ey-42, 120, 36, spec['iq_a2'])
    f.box(1102, 200+ey-42, 120, 36, spec['iq_a3'])
    f.box(1260, 140+ey-42, 105, 72, spec['int_prf'])
    f.box(1380,  95+ey-42, 90, 34, spec['alu1'])
    f.box(1380, 140+ey-42, 90, 34, spec['alu2'])
    f.box(1380, 185+ey-42, 90, 34, spec['alu3'])
    f.box(1380, 230+ey-42, 90, 34, spec['mdu'])
    f.box(1380, 275+ey-42, 90, 34, spec['msr'])
    # LSU
    f.buf.append(f'  <rect x="1090" y="{340+ey-42}" width="380" height="205" rx="8" fill="{C["sub_bg"]}" stroke="{C["sub_st"]}" stroke-width="1.3"/>')
    f.text(1102, 362+ey-42+30, "LSU", 16, C['ex_tag'], "start", bold=True)
    f.box(1102, 365+ey-42, 130, 58, spec['iq_lsu'])
    f.box(1270, 360+ey-42, 80, 34, spec['ls1'])
    f.box(1270, 408+ey-42, 80, 34, spec['ls2'])
    f.box(1270, 456+ey-42, 80, 34, spec['std1'])
    f.box(1270, 500+ey-42, 80, 34, spec['std2'])
    f.box(1380, 370+ey-42, 100, 40, spec['dtlb'])
    f.box(1380, 440+ey-42, 100, 50, spec['l1d'])
    f.box(1380, 505+ey-42, 100, 32, spec['lsu_ctl'])
    # FSU
    f.buf.append(f'  <rect x="1090" y="{565+ey-42}" width="380" height="120" rx="8" fill="{C["sub_bg"]}" stroke="{C["sub_st"]}" stroke-width="1.3"/>')
    f.text(1102, 587+ey-42+30, "FSU", 16, C['ex_tag'], "start", bold=True)
    f.box(1102, 590+ey-42, 130, 30, spec['iq_fsu'])
    f.box(1102, 635+ey-42, 95, 32, spec['fsu_ctl'])
    f.box(1260, 580+ey-42, 115, 62, spec['fp_prf'])
    f.box(1385, 575+ey-42, 95, 36, spec['fpu1'])
    f.box(1385, 625+ey-42, 95, 36, spec['fpu2'])

    # ---------- Memory 组 ----------
    my = Y0+700
    f.box(80, 765-760+my, 130, 46, spec['mmu_box'])
    f.box(270, 760-760+my, 380, 56, spec['l2_box'])
    f.box(710, 765-760+my, 110, 46, spec['chi'])
    f.box(880, 765-760+my, 200, 46, spec['memif'])
    f.text(1470, 300, spec['llc_corner'], 13, C['gold'], "end", bold=True)

    # ---------- 箭头（与模板同拓扑） ----------
    Y = Y0 - 40
    f.arr(f"M190,{114+Y} L190,{140+Y} L122,{140+Y} L122,{158+Y}")
    f.arr(f"M190,{114+Y} L190,{140+Y} L260,{140+Y} L260,{158+Y}")
    f.arr(f"M122,{202+Y} L122,{224+Y} L190,{224+Y} L190,{248+Y}")
    f.arr(f"M190,{294+Y} L190,{328+Y}")
    f.arr(f"M320,{355+Y} L360,{355+Y} L360,{160+Y} L378,{160+Y}")
    f.arr(f"M505,{200+Y} L505,{225+Y} L655,{225+Y} L655,{208+Y}")
    f.arr(f"M505,{200+Y} L505,{250+Y} L655,{250+Y} L655,{368+Y-180+180}")
    f.arr(f"M720,{233+Y} L743,{233+Y}")
    f.arr(f"M875,{233+Y} L898,{233+Y}")
    f.arr(f"M720,{393+Y} L743,{393+Y}")
    f.arr(f"M875,{393+Y} L898,{393+Y}")
    f.arr2(f"M810,{256+Y} L810,{273+Y}")
    f.arr2(f"M810,{347+Y} L810,{368+Y}")
    f.arr(f"M1020,{233+Y} L1060,{233+Y} L1060,{118+Y} L1100,{118+Y}")
    f.arr(f"M1020,{233+Y} L1060,{233+Y} L1060,{168+Y} L1100,{168+Y}")
    f.arr(f"M1020,{233+Y} L1060,{233+Y} L1060,{218+Y} L1100,{218+Y}")
    f.arr(f"M1020,{393+Y} L1098,{393+Y}")
    f.arr(f"M1020,{393+Y} L1020,{600+Y} L1096,{600+Y}")
    for dy in (142, 160, 178):
        f.arr(f"M1222,{118+dy-100+Y} L1258,{dy+Y}")
    for ty in (114, 159, 204, 249, 294):
        f.arr(f"M1365,{152+Y} L1378,{ty+Y}")
    for ty in (377, 425, 473, 517):
        f.arr(f"M1232,{394+Y} L1268,{ty+Y}")
    for ty in (390, 402, 465, 478):
        f.arr(f"M1350,{ty+Y} L1378,{ty+Y}")
    f.arr(f"M1430,{490+Y} L1430,{503+Y}")
    f.arr(f"M1167,{625+Y} L1167,{633+Y}")
    f.arr(f"M1197,{651+Y} L1258,{622+Y}")
    f.arr2(f"M1375,{601+Y} L1383,{594+Y}")
    f.arr2(f"M1375,{619+Y} L1383,{632+Y}")
    f.arr2(f"M210,{788+Y} L268,{788+Y}")
    f.arr(f"M650,{788+Y} L708,{788+Y}")
    f.arr(f"M820,{788+Y} L878,{788+Y}")
    f.arr(f"M1280,{680+Y} L1280,{740+Y} L650,{740+Y} L650,{758+Y}", dashed=True)
    f.text(1290, 712+Y, "访存请求", 13, C['sub'], "start")

    # ---------- RAS 横幅（五图底部, SDC 语义） ----------
    ry = Y0 + 845
    f.buf.append(f'  <rect x="40" y="{ry}" width="1440" height="115" rx="10" fill="#fef2f2" stroke="{C["red"]}" stroke-width="2"/>')
    f.text(58, ry+26, "RAS / 保护状态（SDC 视角）", 14.5, C['red'], "start", bold=True)
    for i, (label, val, color) in enumerate(spec['ras_rows']):
        yy = ry + 48 + i * 20
        f.text(58, yy, label, 12.5, C['txt'], "start")
        f.text(300, yy, val, 12.5, color, "start")
    return f.save(out_path)

SPECS = []
def spec(**kw):
    kw.setdefault('slug', 'x'); SPECS.append(kw)

G = "#047857"; R = "#b91c1c"

# ============ 1. Kunpeng 920 (TaiShan v110) ============
spec(
  slug='kunpeng920',
  title='Kunpeng 920 · TaiShan v110 微架构功能图（ARMv8.2-A · 4 宽乱序 · 实测口径）',
  subtitle='统一模板布局。★=独有：L3/SLC 三模式+128B 行+簇侧 tag、无 µop cache、RAS=0；红字=无保护披露。出处：kunpeng920_microarchitecture.md 本机实测 + 公开资料',
  fetch_note='无 µop cache → 取指带宽悬崖',
  ooo_note='ROB ~128（实测有效 108–110）',
  ex_note='3×ALU + 1×MDU；FP 双管线',
  ifu=['IFU', '4 条/周期'],
  bre=['BRE', '两级动态'],
  bp=['BP', '≈A73 水平'],
  itlb=['L1-I-TLB', '32 项 全相联'],
  l1i=['L1-I-cache', '64KB 4-way', '✗ 保护未披露'],
  iq=['40 entry(估)'],
  idec=['Int Decode', '4 宽'],
  iren=['Int rename', 'PRF ~128'],
  idisp=['Int Dispatch'],
  sync=['Sync', 'mail Box'],
  fdec=['FP/SIMD decode'],
  fren=['FP/SIMD rename'],
  fdisp=['FP/SIMD Dispatch'],
  iq_a1=['ALU1 Issue Queue', '~33 项'],
  iq_a2=['ALU2 Queue', '~33 项'],
  iq_a3=['ALU3 Queue', '~33 项'],
  int_prf=['Int PRF', '~128 项', '✗ 无保护'],
  alu1=['ALU1'], alu2=['ALU2'], alu3=['ALU3'],
  mdu=['MDU', '乘4/除19'],
  msr=['MSR/CP15'],
  iq_lsu=['LSU MDU/SYS', 'Issue Queue', '~33 项'],
  ls1=['LS1'], ls2=['LS2'], std1=['STD1'], std2=['STD2'],
  dtlb=['L1 DTLB', '32 项', '✗ 无保护'],
  l1d=['L1-Dcache', '64K 4-way', '✗ ECC 声称无证据'],
  lsu_ctl=['LSU'],
  iq_fsu=['FSU Issue Queue', '~33 项'],
  fsu_ctl=['FSU'],
  fp_prf=['FP/SIMD PRF', '偏小', '✗ 无保护'],
  fpu1=['FP Pipe 1', 'FP32 FMA'],
  fpu2=['FP Pipe 2', 'FP64 1/4 rate'],
  mmu_box=['mmu', 'L2 TLB 1024'],
  l2_box=['L2 and Coherent Control', '512KB 8-way 私有 · 10cyc', '✗ ECC 声称无证据'],
  chi=['Hydra/HHA', '(替代 CHI-E)'],
  memif=['memory interface', 'DDR4-2933 ×8ch'],
  llc_corner='★ L3/SLC 32MB/die 15-way 128B 行 tag 在簇侧 三模式',
  ras_rows=[
    ('架构化 RAS (ERR*/ESB/poison)', '✗ 无 —— ID_AA64PFR0_EL1.RAS = 0（EL0 实测）', R),
    ('核内 RAM 保护', '✗ 未知：厂商宣称 I$/D$ ECC，但无架构化接口可验证', R),
    ('平台 RAS', '✓ ACPI HEST/EINJ/BERT/ERST + ghes_edac DDR SECDED', G),
    ('SDC 判定', '核内翻转无任何架构级可见信号 —— 五款中敏感性最高', R),
  ],
)

# ============ 2. 920f (HiSilicon 0xd22) ============
spec(
  slug='920f',
  title='920f · HiSilicon part 0xd22 微架构功能图（ARMv9 · SVE512+SME2 · 黑盒实测）',
  subtitle='统一模板布局。灰虚线=规格未公开（黑盒，不臆造）；★=独有：SVE512/SME2、768KB 12-way L2、无 LLC、64KB 强制页。出处：920f.md NSCC cn23154 实测',
  fetch_note='BPU 容量未测（bpbench 未完成）',
  ooo_note='宽度/ROB/PRF 全部未公开',
  ex_note='标量 FMA 2/cyc 实证',
  ifu=['IFU', '宽度未公开'],
  bre=['BRE', '未测'], bp=['BP', '未测'],
  itlb=['L1-I-TLB', '容量未公开'],
  l1i=['L1-I-cache', '32KB 4-way', '✗ 保护未披露'],
  iq=['40 entry(?)'],
  idec=['Int Decode', '未公开'],
  iren=['Int rename', '未公开'],
  idisp=['Int Dispatch'],
  sync=['Sync', 'mail Box'],
  fdec=['FP/SIMD decode', 'SVE512'],
  fren=['FP/SIMD rename'],
  fdisp=['FP/SIMD Dispatch'],
  iq_a1=['ALU1 Issue Queue', '未公开'],
  iq_a2=['ALU2 Queue', '未公开'],
  iq_a3=['ALU3 Queue', '未公开'],
  int_prf=['Int PRF', '未公开', '✗ 未知'],
  alu1=['ALU1'], alu2=['ALU2'], alu3=['ALU3'],
  mdu=['MDU'],
  msr=['MSR/CP15'],
  iq_lsu=['LSU MDU/SYS', 'Issue Queue', '未公开'],
  ls1=['LS1'], ls2=['LS2'], std1=['STD1'], std2=['STD2'],
  dtlb=['L1 DTLB', '未测', '✗ 64KB 页放大 ×16'],
  l1d=['L1-Dcache', '32K 8-way', '✗ 保护未披露'],
  lsu_ctl=['LSU'],
  iq_fsu=['FSU Issue Queue', '未公开'],
  fsu_ctl=['FSU'],
  fp_prf=['FP/SIMD PRF', 'Z0–Z31 ×512b', '✗ 未知（新数据面）'],
  fpu1=['FSU Pipe 1', 'SVE512 FMA'],
  fpu2=['FSU Pipe 2', 'SVE512 FMA'],
  mmu_box=['mmu', 'L2 TLB 未测'],
  l2_box=['L2 and Coherent Control', '★ 768KB 12-way 私有 · 17cyc', '✗ 保护未披露'],
  chi=['HCCS', '(类 CHI-E)'],
  memif=['memory interface', '565GB · 16+16 NUMA'],
  llc_corner='★ 无 L3/LLC（少一级暴露面）',
  ras_rows=[
    ('架构化 RAS', '✓ ID_AA64PFR0_EL1.RAS = 1（实测）—— 架构扩展存在', G),
    ('防御矩阵', '✗ 黑盒：无厂商 TRM，注入寄存器/保护矩阵未知', R),
    ('SDC 判定', '有防御潜力但强度未知；SVE512 巨型寄存器 = 新增大面积无保护数据面', R),
  ],
)

# ============ 3. Neoverse N1 ============
spec(
  slug='neoverse-n1',
  title='Arm Neoverse N1 微架构功能图（ARMv8.2-A · 超标量乱序 · DSU）',
  subtitle='统一模板布局。★=独有：ETM、AArch32 EL0、三级原子；✗=TRM 明示无保护。出处：Neoverse N1 TRM 100616_0401_02 §2/§3/§6/§7/§9',
  fetch_note='TRM 未披露 BTB/GHB 容量',
  ooo_note='TRM 未披露宽度/ROB',
  ex_note='NEON 128b · 无 SVE',
  ifu=['IFU', '超标量'],
  bre=['BRE'], bp=['BP', '动态'],
  itlb=['L1-I-TLB', '48 项 全相联', '✗ flops 无保护'],
  l1i=['L1-I-cache', '64KB 4-way', '✓ tag parity+data SED'],
  iq=['40 entry(?)'],
  idec=['Int Decode', 'A32/T32/A64'],
  iren=['Int rename'],
  idisp=['Int Dispatch'],
  sync=['Sync', 'mail Box'],
  fdec=['FP/SIMD decode'],
  fren=['FP/SIMD rename'],
  fdisp=['FP/SIMD Dispatch'],
  iq_a1=['Issue Queue', '容量未披露'],
  iq_a2=['Issue Queue'],
  iq_a3=['Issue Queue'],
  int_prf=['Int PRF', '容量未披露', '✗ 无保护披露'],
  alu1=['ALU1'], alu2=['ALU2'], alu3=['ALU3'],
  mdu=['MDU'],
  msr=['MSR/CP15'],
  iq_lsu=['LSU MDU/SYS', 'Issue Queue'],
  ls1=['LS1'], ls2=['LS2'], std1=['STD1'], std2=['STD2'],
  dtlb=['L1 DTLB', '48 项 全相联', '✗ flops 无保护'],
  l1d=['L1-Dcache', '64K 4-way', '✓ SECDED/32b+poison'],
  lsu_ctl=['LSU'],
  iq_fsu=['FSU Issue Queue'],
  fsu_ctl=['FSU'],
  fp_prf=['FP/SIMD PRF', '128b NEON', '✗ 无保护披露'],
  fpu1=['FSU Pipe 1'],
  fpu2=['FSU Pipe 2'],
  mmu_box=['mmu', 'L2 TLB 1280 5-way'],
  l2_box=['L2 and Coherent Control', '256/512/1024KB · TQ 24/36/48', '✓ tag+data SECDED'],
  chi=['DSU', '(替代 CHI-E)'],
  memif=['memory interface', '48-bit PA · GICv4.1'],
  llc_corner='★ ETM · AArch32 EL0 · near/far/L3 三级原子',
  ras_rows=[
    ('架构化 RAS', '✓ 完整：ERR<n>FR/CTLR/MISC0-1+PFGF · SEA/AEA/ERI · FHI/ERI · ESB · poison(64b, L1D 32b)', G),
    ('明示无保护', '✗ L1 BTB · GHB · BPIQ · PHT · MMU repl/biased-repl · L2 victim · L1 TLB(flops)', R),
    ('错误注入', '✓ CE/DE/UC/RE 四类全可注入（§9.7）', G),
    ('SDC 判定', '披露透明度参照系；执行单元/PRF/LSQ 依旧无披露', R),
  ],
)

# ============ 4. Neoverse N2 ============
spec(
  slug='neoverse-n2',
  title='Arm Neoverse N2 微架构功能图（Armv9.0-A · 超标量乱序 · DSU-110）',
  subtitle='统一模板布局。★=独有：L0 MOP 1536 项、MMUTC SED、AArch32 全保留。出处：Neoverse N2 TRM 102099_0003_06 §3/§6/§7/§8/§9/§11',
  fetch_note='BPU 容量未披露',
  ooo_note='宽度/ROB 未披露',
  ex_note='SVE/SVE2 128b 向量',
  ifu=['IFU', '超标量'],
  bre=['BRE'], bp=['BP', '方向+历史'],
  itlb=['L1-I-TLB', '48 项 全相联', '✓ MMUTC SED'],
  l1i=['L1-I-cache', '64KB 4-way', '✓ tag+data SED'],
  iq=['40 entry(?)'],
  idec=['Int Decode', 'A32/T32/A64'],
  iren=['Int rename'],
  idisp=['Int Dispatch'],
  sync=['Sync', 'mail Box'],
  fdec=['FP/SIMD decode', 'SVE2 128b'],
  fren=['FP/SIMD rename'],
  fdisp=['FP/SIMD Dispatch'],
  iq_a1=['Issue Queue', '容量未披露'],
  iq_a2=['Issue Queue'],
  iq_a3=['Issue Queue'],
  int_prf=['Int PRF', '容量未披露', '✗ 无保护披露'],
  alu1=['ALU1'], alu2=['ALU2'], alu3=['ALU3'],
  mdu=['MDU'],
  msr=['MSR/CP15'],
  iq_lsu=['LSU MDU/SYS', 'Issue Queue'],
  ls1=['LS1'], ls2=['LS2'], std1=['STD1'], std2=['STD2'],
  dtlb=['L1 DTLB', '44 项 全相联', '✓ MMUTC SED'],
  l1d=['L1-Dcache', '64K 4-way', '✓ tag+data SECDED'],
  lsu_ctl=['LSU'],
  iq_fsu=['FSU Issue Queue'],
  fsu_ctl=['FSU'],
  fp_prf=['FP/SIMD PRF', 'SVE 128b', '✗ 无保护披露'],
  fpu1=['FSU Pipe 1', 'SVE2'],
  fpu2=['FSU Pipe 2', 'Crypto'],
  mmu_box=['mmu', 'L2 TLB 1280 5-way'],
  l2_box=['L2 and Coherent Control', '512/1024KB · TQ SECDED', '✓ tag+data+TQ SECDED'],
  chi=['DSU-110', '(替代 CHI-E)'],
  memif=['memory interface', 'CHI-E 256-bit'],
  llc_corner='★ L0 MOP 1536 项 4-way skewed · MMUTC SED',
  ras_rows=[
    ('架构化 RAS', '✓ v9.0 全量：ERR* · FHI/ERI · SEA/AEA/ERI · ESB · poison · MEMORY_ERROR PMU', G),
    ('保护矩阵', 'SECDED=L1D/L2 tag+data+TQ；SED=L1I+★MOP+★MMUTC', G),
    ('TRM 承认', 'SED 双位错不检测→可能数据损坏；L1D/L2 tag UC 不可遏制', R),
    ('SDC 判定', 'MOP = 弱保护×高命中×指令面 三重叠加的独立注入靶点（五款唯一）', R),
  ],
)

# ============ 5. Neoverse N3 ============
spec(
  slug='neoverse-n3',
  title='Arm Neoverse N3 微架构功能图（Armv9.2-A · 平衡性能核 · DSU-120 Direct connect）',
  subtitle='统一模板布局。★=独有：分裂式 L2 TLB、TLB SED、L1D aux tag、L2 ECC granule 128/256b、无 MOP。出处：Neoverse N3 TRM 107997_0001_03 §1/§2/§5/§6/§7/§8/§10',
  fetch_note='BPU 容量未披露 · 无 MOP',
  ooo_note='宽度/ROB 未披露',
  ex_note='SVE/SVE2 128b · SHA-3',
  ifu=['IFU', '超标量'],
  bre=['BRE'], bp=['BP', '方向+历史'],
  itlb=['L1-I-TLB', '32 项 全相联', '✓ TLB SED'],
  l1i=['L1-I-cache', '32/64KB 4-way', '✓ tag+data SED'],
  iq=['40 entry(?)'],
  idec=['Int Decode', '仅 A64'],
  iren=['Int rename'],
  idisp=['Int Dispatch'],
  sync=['Sync', 'mail Box'],
  fdec=['FP/SIMD decode', 'SVE2 128b'],
  fren=['FP/SIMD rename'],
  fdisp=['FP/SIMD Dispatch'],
  iq_a1=['Issue Queue', '容量未披露'],
  iq_a2=['Issue Queue'],
  iq_a3=['Issue Queue'],
  int_prf=['Int PRF', '容量未披露', '✗ 无保护披露'],
  alu1=['ALU1'], alu2=['ALU2'], alu3=['ALU3'],
  mdu=['MDU'],
  msr=['MSR/CP15'],
  iq_lsu=['LSU MDU/SYS', 'Issue Queue'],
  ls1=['LS1'], ls2=['LS2'], std1=['STD1'], std2=['STD2'],
  dtlb=['L1 DTLB', '48 项 全相联', '✓ TLB SED'],
  l1d=['L1-Dcache', '32/64K 4-way', '✓ tag+aux+data SECDED'],
  lsu_ctl=['LSU'],
  iq_fsu=['FSU Issue Queue'],
  fsu_ctl=['FSU'],
  fp_prf=['FP/SIMD PRF', 'SVE 128b', '✗ 无保护披露'],
  fpu1=['FSU Pipe 1', 'SVE2'],
  fpu2=['FSU Pipe 2', 'SHA-3/SM'],
  mmu_box=['mmu', '★ 分裂 L2 TLB'],
  l2_box=['L2 and Coherent Control', '128KB–2MB · granule 可配', '✓ SECDED granule 128/256b'],
  chi=['DSU-120', 'CHI-E 256-bit'],
  memif=['memory interface', '48-bit VA/PA · MPAM'],
  llc_corner='★ L2 TLB=small 1536+medium 256+walk cache · 无 MOP',
  ras_rows=[
    ('架构化 RAS', '✓ v9.2 全量（寄存器 _EL1 后缀, RASv1.1）· Node 0 覆盖 MMU/TLB', G),
    ('保护矩阵', 'SECDED=L1D tag/★aux/data+L2 tag/data+TQ；SED=L1I+★TLB（整体）', G),
    ('残余弱点', 'SED 类双位错仍是承认的 corruption 通道；执行单元/PRF/LSQ 无披露', R),
    ('SDC 判定', '披露范围内防御最厚（TLB/aux tag/granule），相对敏感性最低', G),
  ],
)

if __name__ == '__main__':
    import sys
    for s in SPECS:
        out = build_fig(s, f"{s['slug']}_tmp.svg")
        print("built", out)
