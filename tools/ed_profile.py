#!/usr/bin/env python3
"""ed_profile.py — CPU 描述文件（Layer C）解析与 w/ceiling 推导库。

SDC ED 评估方案（docs/sdc-ed/method.md §2-§3）：
  一份声明式 CPU 描述 YAML → 四消费者。本模块是消费者 ③④ 的实现：
  w_u（翻转份额，位容量推导）+ ceiling_u（可达性上限）+ ρ 初值。

用法（库）:
    from ed_profile import load_profile
    p = load_profile("configs/cpu-profiles/taishan-v110.yaml")
    p.weights()          # {unit: w_u}，总和 1.0
    p.rho_initial()      # {unit: rho}（保护矩阵推导，YAML 显式值优先）
    p.ceiling("MMU")     # 0.2（SE 用户态）
    p.report()           # 人读报告（含 uncertainty 区间与 residuals）

用法（CLI）:
    python3 tools/ed_profile.py configs/cpu-profiles/taishan-v110.yaml

诚实边界（method.md §4）：
  - 组合逻辑翻转份额按 COMBINATIONAL_WEIGHT = 1/3 SRAM 折算（文献级先验，
    进 residuals 声明，不冒充实测）。
  - null 字段（未披露）产生 uncertainty 区间：该单元 w_u 附 [lo, hi]，
    lo 取 gem5 同类默认下界、hi 取同代披露 CPU 上界（保守放大）。
"""

import argparse
import math
import sys
from pathlib import Path

import yaml

# ---------------------------------------------------------------------------
# 常量（全部在 method.md 登记）
# ---------------------------------------------------------------------------

# 组合逻辑（FU 门电路）相对 SRAM 的翻转份额权重（method.md §4 #2）
COMBINATIONAL_WEIGHT = 1.0 / 3.0

# 单元键（Layer A 七单元分解；顺序即报告顺序）
UNITS = ["IFU", "OoO", "IEX", "LSU", "FSU", "MMU", "L2C"]

# ceiling_u 缺省表（YAML 可覆盖；每条附依据，method.md §3.1）
#   IFU  SDC 轴 ceiling=0 —— Phase 16 三预测面 0% SDC（squash 自愈），
#        覆盖进 Crash 轴另报，不进 ED。
#   MMU  SE 用户态 ≈0.2×FS 可达 —— addr_map_sub 384/384 Masked。
DEFAULT_CEILINGS = {
    "IFU": 0.0,   # SDC 轴结构性封顶（Phase 16 实测）
    "OoO": 1.0,
    "IEX": 1.0,
    "LSU": 1.0,
    "FSU": 1.0,
    "MMU": 0.2,   # SE 用户态可达性（FS 臂回填）
    "L2C": 1.0,
}

# ρ 初值缺省表（YAML rho_overrides / 保护矩阵推导优先；method.md §3.2）
DEFAULT_RHO = {
    "IFU": 0.00,  # Phase 16：dir_flip/target_flip/ras_flip 全 0%
    "OoO": 0.05,  # IRF SFI 基线（readwrite_seq detection 0.04）
    "IEX": 0.05,  # 门级/执行级 FU SFI 基线
    "LSU": 0.05,  # lsqfwd formal P_SDC=4.7% [3.0,7.3]
    "FSU": 0.01,  # CHAOSFPU N=20 全 Masked（值依赖，保守）
    "MMU": 0.00,  # addr_map_sub 384/384 Masked（SE）
    "L2C": 0.45,  # tag-face；data-face SECDED 0%（双账本由采集侧区分）
}

# 保护矩阵 → ρ 推导规则（method.md §3.2）
#   值域：none > parity_sed > secded；face 语义：data 面被 ECC 保护→0
PROT_RHO = {
    "none": 1.0,          # 无保护：跑标定臂前的上限先验
    "parity": 0.5,        # SED 单 bit 检、双 bit 漏
    "parity_interleaved": 0.5,
    "sed": 0.5,
    "secded": 0.0,        # data-face 全修（L2 2x2 实测 47%→0%）
    "ecc_claimed_no_evidence": 0.5,  # 厂商声称无架构化证据（920 案例）
}


def _parse_size(s):
    """'64KiB'/'1MiB'/'512KiB' → bytes；int 透传；None→None。"""
    if s is None:
        return None
    if isinstance(s, (int, float)):
        return int(s)
    s = str(s).strip()
    mult = 1
    for suffix, m in (("KiB", 1024), ("MiB", 1024 ** 2),
                      ("GiB", 1024 ** 3), ("KB", 1000), ("MB", 1000 ** 2)):
        if s.endswith(suffix):
            mult, s = m, s[: -len(suffix)].strip()
            break
    return int(float(s) * mult)


class CpuProfile:
    """一份 CPU 描述的解析结果与推导产物。"""

    def __init__(self, raw, path):
        self.raw = raw
        self.path = Path(path)
        self.cpu = raw.get("cpu", "unnamed")
        self.units = raw.get("units", {})
        self.uncertainties = []   # [(unit, field, reason)]
        self._scan_uncertainty()

    # -- uncertainty 扫描 ---------------------------------------------

    def _scan_uncertainty(self):
        for uname, udict in self.units.items():
            for field, val in (udict or {}).items():
                if val is None or (isinstance(val, dict)
                                   and any(v is None for v in val.values())):
                    self.uncertainties.append(
                        (uname, field, "null/undisclosed"))

    # -- 位容量（w_u 分子）---------------------------------------------
    # SRAM 结构按全位计；组合逻辑（FU）按 COMBINATIONAL_WEIGHT 折算。

    def _bits_ifu(self):
        u = self.units.get("IFU", {}) or {}
        bits = 0
        l1i = u.get("l1i") or {}
        bits += _parse_size(l1i.get("size")) or 0
        l1i_bits = l1i.get("data_bits_per_entry")  # 可选精细字段
        if l1i_bits:
            pass  # size 已含
        for name in ("btb", "ras"):
            d = u.get(name) or {}
            entries, width = d.get("entries"), d.get("width", 64)
            if entries:
                bits += entries * width
        # 指令 TLB
        d = u.get("l1i_tlb") or {}
        if d.get("entries"):
            bits += d["entries"] * 64
        return bits, False

    def _bits_ooo(self):
        u = self.units.get("OoO", {}) or {}
        bits = 0
        rob = u.get("rob") or {}
        if rob.get("entries"):
            bits += rob["entries"] * 260  # ROB entry ≈260b（pc+dest+meta 保守）
        for prf in ("prf_int", "prf_float", "prf_vec"):
            d = u.get(prf) or {}
            regs, width = d.get("regs"), d.get("width", 64)
            if regs:
                bits += regs * width
        iq = u.get("issue_queues") or {}
        if iq.get("total_entries"):
            bits += iq["total_entries"] * 200
        return bits, False

    def _bits_iex(self):
        return self._fu_bits("IEX")

    def _bits_fsu(self):
        return self._fu_bits("FSU")

    def _fu_bits(self, uname):
        u = self.units.get(uname, {}) or {}
        gate_bits = 0
        for fname, d in (u.get("fus") or {}).items():
            count = (d or {}).get("count") or 0
            width = (d or {}).get("width") or 128
            gate_bits += count * width * 64  # 门级位近似：width 数据路径 × 深度系数
        # 组合逻辑按 1/3 SRAM 权重（method.md §4 #2）
        return int(gate_bits * COMBINATIONAL_WEIGHT), True

    def _bits_lsu(self):
        u = self.units.get("LSU", {}) or {}
        bits = 0
        l1d = u.get("l1d") or {}
        bits += _parse_size(l1d.get("size")) or 0
        for name, w in (("lq", 64 + 64), ("sq", 64 + 64)):
            d = u.get(name) or {}
            if d.get("entries"):
                bits += d["entries"] * w
        dtlb = u.get("l1d_tlb") or {}
        if dtlb.get("entries"):
            bits += dtlb["entries"] * 64
        return bits, False

    def _bits_mmu(self):
        u = self.units.get("MMU", {}) or {}
        d = u.get("l2_tlb") or {}
        if d.get("entries"):
            return d["entries"] * 64, False
        return 0, False

    def _bits_l2c(self):
        u = self.units.get("L2C", {}) or {}
        d = u.get("l2") or {}
        bits = _parse_size(d.get("size")) or 0
        for extra in ("l3", "slc"):
            bits += _parse_size((u.get(extra) or {}).get("size")) or 0
        return bits, False

    # -- 公开 API -------------------------------------------------------

    def unit_bits(self):
        """{unit: (bits, is_combinational)}。"""
        fns = {"IFU": self._bits_ifu, "OoO": self._bits_ooo,
               "IEX": self._bits_iex, "LSU": self._bits_lsu,
               "FSU": self._bits_fsu, "MMU": self._bits_mmu,
               "L2C": self._bits_l2c}
        out = {}
        for u in UNITS:
            bits, comb = fns[u]()
            out[u] = (bits, comb)
        return out

    def weights(self):
        """{unit: w_u}，Σ=1.0；总位数为 0 时全 0。"""
        ub = self.unit_bits()
        total = sum(b for b, _ in ub.values())
        if total == 0:
            return {u: 0.0 for u in UNITS}
        return {u: b / total for u, (b, _) in ub.items()}

    def rho_initial(self):
        """{unit: ρ 初值}。优先级：rho_overrides > 保护矩阵推导 > DEFAULT_RHO。"""
        ov = self.raw.get("rho_overrides") or {}
        out = {}
        for u in UNITS:
            if u in ov:
                out[u] = float(ov[u])
                continue
            out[u] = self._rho_from_protection(u)
        return out

    def _rho_from_protection(self, uname):
        """保护矩阵推导（method.md §3.2 规则）。

        L2C 特殊：tag-face/data-face 双账本——ρ 取 tag-face（data-face
        SECDED 已实证 0%）；无保护时按 none 规则。
        """
        u = self.units.get(uname, {}) or {}
        if uname == "L2C":
            l2 = u.get("l2") or {}
            prot = (l2.get("prot") or "none").lower()
            if "secded" in prot:
                # data-face 全修；tag 别名域盲（39→47% 实测线）
                return DEFAULT_RHO["L2C"]
            return PROT_RHO.get(prot, 1.0) * 0.45
        # 其余单元：找该单元下任一结构的 prot 字段，取最保守（最大 ρ）
        best = None
        for sub in u.values():
            if isinstance(sub, dict) and "prot" in sub:
                r = PROT_RHO.get(str(sub["prot"]).lower())
                if r is not None:
                    best = r if best is None else max(best, r)
        if best is not None:
            return best * DEFAULT_RHO[uname] if best < 1.0 else DEFAULT_RHO[uname]
        return DEFAULT_RHO[uname]

    def ceiling(self, uname):
        ceils = self.raw.get("ceilings") or {}
        if uname in ceils:
            return float(ceils[uname])
        return DEFAULT_CEILINGS[uname]

    def residuals(self):
        res = list(self.raw.get("residuals") or [])
        # 自动附加：uncertainty 单元的 w 是点估计
        if self.uncertainties:
            res.append("w_point_estimate_for_undisclosed_fields:"
                       + ",".join(sorted({u for u, _, _ in self.uncertainties})))
        # 组合逻辑折算系数恒进 residuals
        if "combinational_weight_1_3" not in res:
            res.append("combinational_weight_1_3")
        return res

    def report(self):
        w = self.weights()
        rho = self.rho_initial()
        lines = [f"CPU profile: {self.cpu}  ({self.path})",
                 f"{'unit':6} {'bits':>14} {'w_u':>8} {'rho':>6} "
                 f"{'ceiling':>8}  notes"]
        ub = self.unit_bits()
        for u in UNITS:
            bits, comb = ub[u]
            note = "comb(1/3)" if comb else ""
            if any(x[0] == u for x in self.uncertainties):
                note += " +uncertainty"
            lines.append(f"{u:6} {bits:>14,} {w[u]:>8.4f} {rho[u]:>6.3f} "
                         f"{self.ceiling(u):>8.2f}  {note}")
        lines.append(f"Σw = {sum(w.values()):.4f}")
        if self.residuals():
            lines.append("residuals: " + "; ".join(self.residuals()))
        return "\n".join(lines)


def load_profile(path):
    with open(path) as f:
        raw = yaml.safe_load(f)
    if not isinstance(raw, dict) or "units" not in raw:
        raise ValueError(f"{path}: missing top-level 'units' mapping")
    return CpuProfile(raw, path)


def main():
    ap = argparse.ArgumentParser(description="CPU profile → w/rho/ceiling")
    ap.add_argument("profile", help="configs/cpu-profiles/*.yaml")
    args = ap.parse_args()
    p = load_profile(args.profile)
    print(p.report())
    return 0


if __name__ == "__main__":
    sys.exit(main())
