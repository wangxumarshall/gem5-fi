#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""fsu_suite.py — W5 PolyBench-FP 固定 suite 身份、component seed 与门禁。

权威裁决（docs/gem5-fi/fsu/FP04-F0-W5-SUITE-RULING.md）：

  formal suite seed  : FSU-FP04-F0-W5 的正式计数单位，3 个。
  component run      : 一个 suite seed 下跑一个程序的独立运行，5 个。
  component fault    : 一个 component run 内注入的一次故障，1 个。

固定顺序永远为 gemm → 2mm → lu → cholesky → jacobi-2d；3 个 suite seed
= 15 个 component run，但正式计数只 +3，绝不把 component 数当 seed 数。

本模块只做身份/计数/门禁，不运行 gem5。
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

PROGRAM_ORDER = ("gemm", "2mm", "lu", "cholesky", "jacobi-2d")
PROGRAM_COUNT = len(PROGRAM_ORDER)
DEFAULT_SUITE_ID = "polybench-fp-v1"
DEFAULT_SUITE_VERSION = "1"
DEFAULT_COMPONENT_SEED_POLICY = "w5-component-seed-v1"

COMPONENT_STATUSES = ("admitted", "failed", "not_activated", "invalid")
_HEX64 = re.compile(r"^[0-9a-f]{64}$")


class SuiteError(ValueError):
    """Suite/component 身份不成立；调用方必须响亮拒绝，不得降级运行。"""


def canonical_bytes(obj) -> bytes:
    """Canonical JSON：排序键、无多余空白、UTF-8。"""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False).encode("utf-8")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _normalise_cflags(value) -> str:
    if isinstance(value, (list, tuple)):
        return " ".join(str(x) for x in value)
    return str(value or "")


def _check_hash(value, where: str, allow_pending: bool = True):
    text = str(value or "")
    if allow_pending and text == "pending":
        return text
    if not _HEX64.match(text):
        raise SuiteError(f"{where}: expected 64-hex SHA-256"
                         + (" or 'pending'" if allow_pending else "")
                         + f", got {value!r}")
    return text


def _program_map(suite: dict):
    programs = suite.get("programs")
    if not isinstance(programs, list):
        raise SuiteError("suite.programs must be a list")
    by_id = {}
    for p in programs:
        if not isinstance(p, dict):
            raise SuiteError("suite.programs entries must be objects")
        pid = str(p.get("program_id", "")).strip()
        if not pid:
            raise SuiteError("suite.programs entry missing program_id")
        if pid in by_id:
            raise SuiteError(f"duplicate program component: {pid}")
        by_id[pid] = p
    return by_id


def _validate_order_and_count(suite: dict):
    order = suite.get("program_order")
    if not isinstance(order, list):
        raise SuiteError("suite.program_order must be a list")
    if tuple(order) != PROGRAM_ORDER:
        raise SuiteError(
            "program_order is fixed and must not be reordered by results: "
            f"want {list(PROGRAM_ORDER)}, got {order}")
    count = suite.get("program_count")
    try:
        count = int(count)
    except (TypeError, ValueError):
        raise SuiteError(f"suite.program_count must be {PROGRAM_COUNT}")
    if count != PROGRAM_COUNT:
        raise SuiteError(f"suite.program_count must be {PROGRAM_COUNT}, "
                         f"got {count}")


def suite_identity_document(suite: dict, allow_pending: bool = True) -> dict:
    """构造参与 suite_hash 的严格身份文档。

    只含身份字段：suite_id/suite_version/program_order、每程序
    program_id/program_index/source_sha256/binary_sha256/固定规模、
    compiler 版本与 cflags、oracle 版本。**绝不包含**运行结果、golden、
    attempt、oracle 结局、组件状态或路径。
    """
    if not isinstance(suite, dict):
        raise SuiteError("suite manifest must be an object")
    suite_id = str(suite.get("suite_id", "")).strip()
    suite_version = str(suite.get("suite_version", "")).strip()
    if not suite_id:
        raise SuiteError("suite.suite_id is required")
    if not suite_version:
        raise SuiteError("suite.suite_version is required")
    _validate_order_and_count(suite)
    by_id = _program_map(suite)
    missing = [p for p in PROGRAM_ORDER if p not in by_id]
    extra = [p for p in by_id if p not in PROGRAM_ORDER]
    if missing:
        raise SuiteError(f"suite missing program component(s): {missing}")
    if extra:
        raise SuiteError(f"suite has unknown program component(s): {extra}")

    programs = []
    for index, pid in enumerate(PROGRAM_ORDER):
        p = by_id[pid]
        declared_index = p.get("program_index")
        if declared_index is not None:
            try:
                declared_index = int(declared_index)
            except (TypeError, ValueError):
                raise SuiteError(f"{pid}.program_index must be an integer")
            if declared_index != index:
                raise SuiteError(
                    f"{pid}.program_index must be {index} in fixed order "
                    f"{list(PROGRAM_ORDER)}, got {declared_index}")
        scale = p.get("scale")
        if not isinstance(scale, dict) or not scale:
            raise SuiteError(f"{pid}.scale must be a non-empty object")
        programs.append({
            "program_id": pid,
            "program_index": index,
            "source_sha256": _check_hash(
                p.get("source_sha256"), f"{pid}.source_sha256", allow_pending),
            "binary_sha256": _check_hash(
                p.get("binary_sha256"), f"{pid}.binary_sha256", allow_pending),
            "scale": scale,
        })

    compiler = suite.get("compiler") or {}
    if not isinstance(compiler, dict):
        raise SuiteError("suite.compiler must be an object")
    compiler_version = str(
        compiler.get("version") or suite.get("compiler_version") or "").strip()
    cflags = _normalise_cflags(
        compiler.get("cflags") if "cflags" in compiler else suite.get("cflags"))
    if not compiler_version:
        raise SuiteError("suite.compiler.version is required")
    if not cflags.strip():
        raise SuiteError("suite.compiler.cflags is required")

    oracle = suite.get("oracle") or {}
    if not isinstance(oracle, dict):
        raise SuiteError("suite.oracle must be an object")
    oracle_version = str(
        oracle.get("version") or suite.get("oracle_version") or "").strip()
    if not oracle_version:
        raise SuiteError("suite.oracle.version is required")

    return {
        "suite_id": suite_id,
        "suite_version": suite_version,
        "program_order": list(PROGRAM_ORDER),
        "program_count": PROGRAM_COUNT,
        "programs": programs,
        "compiler": {
            "version": compiler_version,
            "cflags": cflags,
        },
        "oracle": {
            "version": oracle_version,
        },
    }


def compute_suite_hash(suite: dict) -> str:
    return sha256_bytes(canonical_bytes(suite_identity_document(suite)))


def validate_suite_manifest(suite: dict, require_hashes: bool = False,
                            require_suite_hash: bool = False) -> dict:
    """结构 + 固定顺序 + suite_hash 漂移门禁。

    require_hashes=True：正式运行前要求所有 source/binary SHA 已回填。
    require_suite_hash=True：manifest 必须带 suite_hash，且与重算一致。
    返回 {ok, suite_hash, identity}；任何不成立都抛 SuiteError。
    """
    doc = suite_identity_document(suite, allow_pending=not require_hashes)
    if require_hashes:
        for p in doc["programs"]:
            for key in ("source_sha256", "binary_sha256"):
                _check_hash(p[key], f"{p['program_id']}.{key}",
                            allow_pending=False)
    computed = sha256_bytes(canonical_bytes(doc))
    declared = suite.get("suite_hash")
    if declared is not None:
        declared = str(declared)
        _check_hash(declared, "suite.suite_hash", allow_pending=False)
        if declared != computed:
            raise SuiteError(
                f"suite_hash drift: declared {declared}, recomputed {computed}")
    elif require_suite_hash:
        raise SuiteError("suite.suite_hash is required before a formal run")
    return {"ok": True, "suite_hash": computed, "identity": doc}


def component_seed_from_digest(digest: bytes) -> int:
    """取摘要前 8 字节（大端），0 映射为 1。"""
    if len(digest) < 8:
        raise SuiteError("digest must contain at least 8 bytes")
    value = int.from_bytes(digest[:8], "big")
    return value if value else 1


def derive_component_seed(suite_seed: int, program_id: str,
                          policy_version: str = DEFAULT_COMPONENT_SEED_POLICY,
                          suite_id: str = DEFAULT_SUITE_ID,
                          suite_version: str = DEFAULT_SUITE_VERSION) -> int:
    """SHA-256(suite_id|suite_version|suite_seed|program_id|policy_version)。

    确定性：同一 suite seed + program 永远得到同一 component seed。
    5 个程序必须互不相同；调用方应使用 derive_component_seeds() 做强校验。
    """
    if program_id not in PROGRAM_ORDER:
        raise SuiteError(f"unknown program_id {program_id!r}")
    try:
        seed_int = int(suite_seed)
    except (TypeError, ValueError):
        raise SuiteError(f"suite_seed must be an integer, got {suite_seed!r}")
    if seed_int < 0:
        raise SuiteError("suite_seed must be >= 0")
    if not str(policy_version).strip():
        raise SuiteError("policy_version is required")
    material = "|".join([
        str(suite_id), str(suite_version), str(seed_int),
        str(program_id), str(policy_version),
    ]).encode("utf-8")
    return component_seed_from_digest(hashlib.sha256(material).digest())


def derive_component_seeds(suite_seed: int,
                           policy_version: str = DEFAULT_COMPONENT_SEED_POLICY,
                           suite_id: str = DEFAULT_SUITE_ID,
                           suite_version: str = DEFAULT_SUITE_VERSION):
    """按固定顺序返回 5 个 component seed，并拒绝任何碰撞。"""
    seeds = {pid: derive_component_seed(suite_seed, pid, policy_version,
                                        suite_id, suite_version)
             for pid in PROGRAM_ORDER}
    if len(set(seeds.values())) != PROGRAM_COUNT:
        raise SuiteError(f"component seed collision: {seeds}")
    if any(v == 0 for v in seeds.values()):
        raise SuiteError("component seed 0 must be mapped to 1")
    return seeds


def component_golden_sha256(program: dict) -> tuple:
    """返回 (sha256, scheme)；不伪造 golden artifact 哈希。

    优先级：
      1. `golden_array_sha256` —— 预注册 golden 数组的 canonical 字节 SHA-256
         （W5 逐元素 oracle 的正确绑定；gate 生成 golden 后回填）；
      2. 显式 64-hex `golden_sha256`；
      3. suite config 中 golden token 的 UTF-8 SHA-256（legacy fallback，显式
         记录 scheme，绝不冒充数组哈希）。
    """
    array_sha = program.get("golden_array_sha256")
    if array_sha:
        return _check_hash(array_sha, "golden_array_sha256",
                           allow_pending=False), \
            "sha256-of-canonical-golden-array-v1"
    explicit = program.get("golden_sha256")
    if explicit:
        text = str(explicit)
        if text == "pending":
            raise SuiteError(
                f"{program.get('program_id')}: golden_sha256 is still pending")
        return _check_hash(text, "golden_sha256", allow_pending=False), \
            "explicit-golden-sha256-v1"
    golden = program.get("golden")
    if golden is None or str(golden).strip() == "":
        raise SuiteError(
            f"{program.get('program_id')}: golden token is required for a "
            "certified component")
    token = str(golden).strip()
    return sha256_bytes(token.encode("utf-8")), \
        "sha256-utf8-of-golden-token-v1"


REQUIRED_COMPONENT_FIELDS = (
    "suite_id", "suite_hash", "suite_seed", "program_id", "program_index",
    "program_count", "component_attempt", "component_manifest_sha256",
    "component_binary_sha256", "component_source_sha256",
    "component_golden_sha256", "component_status", "component_eligible",
    "component_activated", "component_terminal", "component_oracle",
)


def validate_component_manifest(component: dict, suite: dict | None = None) -> dict:
    """校验单个 component manifest；缺字段/顺序/哈希漂移全部抛错。"""
    if not isinstance(component, dict):
        raise SuiteError("component manifest must be an object")
    missing = [k for k in REQUIRED_COMPONENT_FIELDS if k not in component]
    if missing:
        raise SuiteError(f"component manifest missing fields: {missing}")
    pid = str(component.get("program_id", "")).strip()
    if pid not in PROGRAM_ORDER:
        raise SuiteError(f"component program_id {pid!r} not in fixed suite")
    want_index = PROGRAM_ORDER.index(pid)
    try:
        index = int(component.get("program_index"))
    except (TypeError, ValueError):
        raise SuiteError(f"{pid}.program_index must be an integer")
    if index != want_index:
        raise SuiteError(f"{pid}.program_index must be {want_index}, "
                         f"got {index}")
    try:
        count = int(component.get("program_count"))
    except (TypeError, ValueError):
        raise SuiteError(f"{pid}.program_count must be {PROGRAM_COUNT}")
    if count != PROGRAM_COUNT:
        raise SuiteError(f"{pid}.program_count must be {PROGRAM_COUNT}, "
                         f"got {count}")
    try:
        suite_seed = int(component.get("suite_seed"))
    except (TypeError, ValueError):
        raise SuiteError(f"{pid}.suite_seed must be an integer")
    if suite_seed < 0:
        raise SuiteError(f"{pid}.suite_seed must be >= 0")
    try:
        attempt = int(component.get("component_attempt"))
    except (TypeError, ValueError):
        raise SuiteError(f"{pid}.component_attempt must be an integer")
    if attempt < 1:
        raise SuiteError(f"{pid}.component_attempt must be >= 1")
    status = str(component.get("component_status", ""))
    if status not in COMPONENT_STATUSES:
        raise SuiteError(f"{pid}.component_status {status!r} not in "
                         f"{list(COMPONENT_STATUSES)}")
    _check_hash(component.get("suite_hash"), f"{pid}.suite_hash",
                allow_pending=False)
    for key in ("component_manifest_sha256", "component_binary_sha256",
                "component_source_sha256", "component_golden_sha256"):
        _check_hash(component.get(key), f"{pid}.{key}", allow_pending=False)
    for key in ("component_eligible", "component_activated"):
        try:
            value = int(component.get(key))
        except (TypeError, ValueError):
            raise SuiteError(f"{pid}.{key} must be an integer")
        if value < 0:
            raise SuiteError(f"{pid}.{key} must be >= 0")
    terminal = component.get("component_terminal")
    if terminal is not None and not isinstance(terminal, str):
        raise SuiteError(f"{pid}.component_terminal must be string or null")
    if not str(component.get("component_oracle", "")).strip():
        raise SuiteError(f"{pid}.component_oracle is required")

    if suite is not None:
        suite_id = str(suite.get("suite_id", "")).strip()
        if str(component.get("suite_id")) != suite_id:
            raise SuiteError(f"{pid}.suite_id drift: "
                             f"{component.get('suite_id')!r} != {suite_id!r}")
        suite_hash = compute_suite_hash(suite)
        if str(component.get("suite_hash")) != suite_hash:
            raise SuiteError(f"{pid}.suite_hash drift")
        by_id = _program_map(suite)
        sp = by_id.get(pid)
        if sp is None:
            raise SuiteError(f"{pid}: missing from suite")
        if component.get("component_source_sha256") != sp.get("source_sha256"):
            raise SuiteError(f"{pid}.component_source_sha256 drift")
        if component.get("component_binary_sha256") != sp.get("binary_sha256"):
            raise SuiteError(f"{pid}.component_binary_sha256 drift")
        want_golden, _ = component_golden_sha256(sp)
        if component.get("component_golden_sha256") != want_golden:
            raise SuiteError(f"{pid}.component_golden_sha256 drift")
    return {"ok": True, "program_id": pid, "program_index": index}


def validate_component_manifests(components, suite: dict | None = None) -> dict:
    """5/5、唯一、固定顺序；缺 component / 重复 component 响亮拒绝。"""
    if not isinstance(components, list):
        raise SuiteError("components must be a list")
    if len(components) != PROGRAM_COUNT:
        raise SuiteError(f"suite requires exactly {PROGRAM_COUNT} components, "
                         f"got {len(components)}")
    seen = []
    for c in components:
        info = validate_component_manifest(c, suite)
        seen.append(info["program_id"])
    if len(set(seen)) != len(seen):
        raise SuiteError(f"duplicate component(s): {seen}")
    if seen != list(PROGRAM_ORDER):
        raise SuiteError(
            f"components must be in fixed order {list(PROGRAM_ORDER)}, "
            f"got {seen}")
    return {"ok": True, "program_order": seen}


def suite_seed_state(seed_dir: Path) -> dict:
    """suite seed 的最终状态。

    只有同时满足以下条件才返回 admitted：
      1. seed_dir/suite_manifest.json 存在且身份/suite_hash 自洽；
      2. seed_dir/audit.json.ok is True；
      3. components 恰好 5 个、顺序固定、无缺失/重复；
      4. 每个 component manifest 校验通过，且其 attempt 的 audit.json
         同时 ok=True 与 certified=True，component_status=admitted。
    """
    seed_dir = Path(seed_dir)
    sm_path = seed_dir / "suite_manifest.json"
    if not sm_path.exists():
        attempts = sorted(seed_dir.glob("attempt-*")) if seed_dir.exists() else []
        if any(a.is_dir() for a in attempts) or (seed_dir / ".failed").exists():
            return {"state": "failed", "reason": "no suite_manifest.json"}
        return {"state": "pending", "reason": "no suite_manifest.json"}
    try:
        sm = json.loads(sm_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        return {"state": "invalid", "reason": f"unreadable suite_manifest: {e}"}
    suite = sm.get("suite")
    try:
        v = validate_suite_manifest(suite, require_hashes=True,
                                    require_suite_hash=True)
        suite_hash = v["suite_hash"]
        if str(sm.get("suite_hash")) != suite_hash:
            raise SuiteError("suite_manifest.suite_hash drift")
        suite_seed = int(sm.get("suite_seed"))
        if suite_seed < 0:
            raise SuiteError("suite_manifest.suite_seed must be >= 0")
    except (SuiteError, TypeError, ValueError) as e:
        return {"state": "invalid", "reason": str(e)}

    audit_path = seed_dir / "audit.json"
    suite_audit_ok = False
    if audit_path.exists():
        try:
            suite_audit_ok = json.loads(
                audit_path.read_text(encoding="utf-8")).get("ok") is True
        except (OSError, json.JSONDecodeError):
            suite_audit_ok = False

    components = sm.get("components")
    try:
        validate_component_manifests(components, suite)
    except SuiteError as e:
        return {"state": "invalid", "reason": f"components: {e}",
                "suite_audit_ok": suite_audit_ok, "suite_manifest": str(sm_path)}

    certified = 0
    details = []
    for comp in components:
        pid = comp["program_id"]
        attempt = Path(comp.get("attempt", ""))
        if not attempt.is_absolute():
            attempt = seed_dir / attempt
        detail = {"program_id": pid,
                  "program_index": comp["program_index"],
                  "component_seed": comp.get("component_seed"),
                  "attempt": str(attempt),
                  "status": comp.get("component_status"),
                  "audit_ok": False, "certified": False}
        cm_path = attempt / "component_manifest.json"
        if not attempt.is_dir() or not cm_path.exists():
            detail["reason"] = "component attempt/component_manifest missing"
            details.append(detail)
            continue
        try:
            on_disk = json.loads(cm_path.read_text(encoding="utf-8"))
            validate_component_manifest(on_disk, suite)
        except (OSError, json.JSONDecodeError, SuiteError) as e:
            detail["reason"] = f"component manifest invalid: {e}"
            details.append(detail)
            continue
        # component manifest 必须指向真实 attempt manifest。
        manifest_path = attempt / "manifest.json"
        if not manifest_path.exists():
            detail["reason"] = "attempt manifest.json missing"
            details.append(detail)
            continue
        if sha256_file(manifest_path) != on_disk["component_manifest_sha256"]:
            detail["reason"] = "component_manifest_sha256 drift"
            details.append(detail)
            continue
        # W5 element oracle: the oracle result and the raw fault array must
        # both exist and be covered by the component evidence hashes.
        oracle_path = attempt / "oracle_elements.json"
        array_path = attempt / "inject/array.bin"
        evidence_path = attempt / "evidence_sha256.json"
        oracle_evidence_ok = False
        if (oracle_path.exists() and array_path.exists()
                and evidence_path.exists()):
            try:
                hashes = json.loads(evidence_path.read_text(encoding="utf-8"))
                oracle_evidence_ok = (
                    hashes.get("oracle_elements.json")
                    == sha256_file(oracle_path)
                    and hashes.get("inject/array.bin")
                    == sha256_file(array_path))
            except (OSError, json.JSONDecodeError):
                oracle_evidence_ok = False
        detail["oracle_evidence_ok"] = oracle_evidence_ok
        if not oracle_evidence_ok:
            detail["reason"] = ("element oracle evidence missing or not "
                                "covered by evidence_sha256.json")
            details.append(detail)
            continue
        if on_disk.get("component_oracle") not in ("SDC", "MASKED"):
            detail["reason"] = ("component_oracle is not an element-oracle "
                                f"outcome: {on_disk.get('component_oracle')}")
            details.append(detail)
            continue
        a_path = attempt / "audit.json"
        if not a_path.exists():
            detail["reason"] = "component audit.json missing"
            details.append(detail)
            continue
        try:
            a = json.loads(a_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as e:
            detail["reason"] = f"component audit unreadable: {e}"
            details.append(detail)
            continue
        detail["audit_ok"] = a.get("ok") is True
        detail["certified"] = a.get("certified") is True
        if not detail["audit_ok"]:
            detail["reason"] = "component audit.ok != true"
        elif not detail["certified"]:
            detail["reason"] = "component audit.certified != true"
        elif on_disk.get("component_status") != "admitted":
            detail["reason"] = ("component_status != admitted: "
                                f"{on_disk.get('component_status')}")
        else:
            certified += 1
        details.append(detail)

    admitted = (suite_audit_ok and certified == PROGRAM_COUNT
                and len(components) == PROGRAM_COUNT)
    if admitted:
        state = "admitted"
    elif any(d.get("status") == "failed" for d in details) \
            or any("reason" in d for d in details):
        state = "failed"
    else:
        state = "invalid"
    return {
        "state": state,
        "suite_id": suite.get("suite_id"),
        "suite_version": suite.get("suite_version"),
        "suite_hash": suite_hash,
        "suite_seed": sm.get("suite_seed"),
        "suite_audit_ok": suite_audit_ok,
        "component_runs": len(components),
        "component_certified": certified,
        "components": details,
        "suite_manifest": str(sm_path),
    }
