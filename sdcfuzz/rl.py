"""RL-guided SDC mutation: Transformer state, four actions, five-term reward.

This is the Phase-2 prototype for sdcfuzz-v1.2 §5.2.  It is deliberately
dependency-light (NumPy only): the state contains a compact one-layer
Transformer embedding of the instruction stream, the coverage vector, the power
features and the avalanche masking indicator; the policy is a linear
contextual bandit trained with REINFORCE.  The Transformer encoder is a fixed,
seeded feature extractor (as in a frozen state encoder); the policy heads are
learned.  A full end-to-end Transformer policy is future work and is called out
in the verification document.

Action space (all four §5.2 families):
  replace    same-class instruction substitution, operands unchanged
  operand    D13-style directed mutation (xor mask, +1, rotate, complement)
  power      insert a Type-II low/high power-stress segment
  recombine  splice a body segment from another seed stream

Reward (maximised):
  R = a1*dSFI + a2*dCoverage + a3*dPower - b1*masking_penalty
      - b2*redundancy_penalty
with a1=2.0, a2=0.5, a3=0.5, b1=1.0, b2=0.3.  ``dSFI`` is the change in the
avalanche word-flip ratio (the cheap SFI surrogate); the final policy is
validated with real gem5 fault injection in ``sdcfuzz.phase2``.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import random
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Iterable, Sequence

import numpy as np

from . import isa
from .avalanche import Stream, avalanche
from . import power
from .templates import TEMPLATES

COVERAGE_MATRIX = Path("m5out/phase1-gate-final/coverage/coverage_matrix.json")
_COVERAGE_CACHE = None

# ---------------------------------------------------------------------------
# Instruction features / coverage
# ---------------------------------------------------------------------------

CLASSES = ("mov", "alu", "mult", "div", "fpadd", "fpmul", "mem", "branch",
           "other")
CLASS_INDEX = {name: index for index, name in enumerate(CLASSES)}
STRUCTURES = ("rf", "vec", "l1i", "l1d", "alu", "mult", "div", "fpadd",
              "fpmul")
STRUCT_INDEX = {name: index for index, name in enumerate(STRUCTURES)}
FEATURE_DIM = len(CLASSES) + 8
D_MODEL = 16
N_HEADS = 2


def op_class(op: isa.Op) -> str:
    kind = op.kind
    if kind == "mov":
        return "mov"
    if kind in ("add", "sub", "and", "orr", "eor", "add_imm", "add_lsl"):
        return "alu"
    if kind in ("mul", "madd"):
        return "mult"
    if kind == "udiv":
        return "div"
    if kind in ("fadd", "fsub"):
        return "fpadd"
    if kind in ("fmul", "fdiv"):
        return "fpmul"
    if kind in ("ldr", "str", "ldrf"):
        return "mem"
    if kind == "busy_loop":
        return "branch"
    return "other"


def op_structures(op: isa.Op) -> dict:
    kind = op.kind
    if kind in ("add", "sub", "and", "orr", "eor", "add_imm", "add_lsl",
                "busy_loop"):
        return {"alu": 1.0, "rf": 0.5}
    if kind in ("mul", "madd"):
        return {"mult": 1.0, "rf": 0.5}
    if kind == "udiv":
        return {"div": 1.0, "rf": 0.5}
    if kind in ("fadd", "fsub"):
        return {"fpadd": 1.0, "vec": 0.5}
    if kind in ("fmul", "fdiv"):
        return {"fpmul": 1.0, "vec": 0.5}
    if kind in ("ldr", "str", "ldrf"):
        return {"l1d": 1.0, "rf": 0.5}
    if kind == "mov":
        return {"rf": 1.0}
    return {"rf": 0.2}


def measured_coverage(template_id: str):
    """Phase-1 gem5 ACE/IBR/SAD vector for a seed template, if recorded."""
    global _COVERAGE_CACHE
    if _COVERAGE_CACHE is None:
        path = Path(os.environ.get("SDCFUZZ_COVERAGE_MATRIX", COVERAGE_MATRIX))
        try:
            _COVERAGE_CACHE = json.loads(path.read_text()).get("templates", {})
        except (OSError, json.JSONDecodeError):
            _COVERAGE_CACHE = {}
    row = _COVERAGE_CACHE.get(template_id)
    if not row:
        return None
    cov = row.get("coverage", {})
    return np.array([float(cov.get(name, 0.0)) for name in STRUCTURES])


def coverage(stream: Stream) -> np.ndarray:
    if stream.template_id:
        measured = measured_coverage(stream.template_id)
        if measured is not None:
            return measured
    vector = np.zeros(len(STRUCTURES), dtype=np.float64)
    for _ in range(stream.reps * stream.iterations):
        for op in stream.body:
            for name, weight in op_structures(op).items():
                vector[STRUCT_INDEX[name]] += weight
    total = vector.sum()
    return vector / total if total else vector


def _token_features(op: isa.Op, position: int, length: int) -> np.ndarray:
    cls = op_class(op)
    one_hot = np.zeros(len(CLASSES), dtype=np.float64)
    one_hot[CLASS_INDEX[cls]] = 1.0
    imm = op.imm or 0
    pop = bin(imm & ((1 << 64) - 1)).count("1") / 64.0
    from .operand_heuristic import carry_chain
    carry = carry_chain(imm & ((1 << 64) - 1), 0) / 64.0
    width = (op.width or 64) / 64.0
    is_mem = 1.0 if cls == "mem" else 0.0
    is_fp = 1.0 if cls in ("fpadd", "fpmul") else 0.0
    weight = power.POWER_WEIGHTS.get(op.kind, 0.0) / 6.0
    pos = position / max(1, length - 1)
    off = (op.off or 0) / 1024.0
    return np.concatenate([one_hot, [pop, carry, width, is_mem, is_fp,
                                     weight, pos, off]])


class TransformerEncoder:
    """One-layer, two-head self-attention encoder with fixed seeded weights."""

    def __init__(self, seed: int = 20260825, d_model: int = D_MODEL,
                 n_heads: int = N_HEADS):
        rng = np.random.default_rng(seed)
        self.d_model = d_model
        self.n_heads = n_heads
        self.d_head = d_model // n_heads
        scale = 0.35
        self.w_in = rng.normal(0, scale, (FEATURE_DIM, d_model))
        self.w_q = rng.normal(0, scale, (d_model, d_model))
        self.w_k = rng.normal(0, scale, (d_model, d_model))
        self.w_v = rng.normal(0, scale, (d_model, d_model))
        self.w_o = rng.normal(0, scale, (d_model, d_model))
        self.w_1 = rng.normal(0, scale, (d_model, d_model * 2))
        self.w_2 = rng.normal(0, scale, (d_model * 2, d_model))
        self.gamma1 = np.ones(d_model)
        self.beta1 = np.zeros(d_model)
        self.gamma2 = np.ones(d_model)
        self.beta2 = np.zeros(d_model)

    @staticmethod
    def _softmax(x: np.ndarray, axis: int = -1) -> np.ndarray:
        shifted = x - x.max(axis=axis, keepdims=True)
        exp = np.exp(shifted)
        return exp / exp.sum(axis=axis, keepdims=True)

    @staticmethod
    def _layer_norm(x: np.ndarray, gamma: np.ndarray,
                    beta: np.ndarray, eps: float = 1e-5) -> np.ndarray:
        mean = x.mean(axis=-1, keepdims=True)
        var = x.var(axis=-1, keepdims=True)
        return gamma * (x - mean) / np.sqrt(var + eps) + beta

    def _attention(self, x: np.ndarray) -> np.ndarray:
        n = x.shape[0]
        q = x @ self.w_q
        k = x @ self.w_k
        v = x @ self.w_v
        # (n, heads, d_head) -> (heads, n, d_head)
        q = q.reshape(n, self.n_heads, self.d_head).transpose(1, 0, 2)
        k = k.reshape(n, self.n_heads, self.d_head).transpose(1, 0, 2)
        v = v.reshape(n, self.n_heads, self.d_head).transpose(1, 0, 2)
        scores = q @ k.transpose(0, 2, 1) / math.sqrt(self.d_head)
        att = self._softmax(scores, axis=-1)
        out = att @ v
        out = out.transpose(1, 0, 2).reshape(n, self.d_model)
        return out @ self.w_o

    def encode(self, ops: Sequence[isa.Op]) -> np.ndarray:
        if not ops:
            return np.zeros(self.d_model)
        features = np.stack([_token_features(op, index, len(ops))
                             for index, op in enumerate(ops)])
        x = features @ self.w_in
        positions = np.arange(len(ops))[:, None]
        dims = np.arange(self.d_model)[None, :]
        angle = positions / np.power(10000.0, (2 * (dims // 2)) / self.d_model)
        x = x + np.where(dims % 2 == 0, np.sin(angle), np.cos(angle))
        x = self._layer_norm(x + self._attention(x), self.gamma1, self.beta1)
        ff = np.tanh(x @ self.w_1) @ self.w_2
        x = self._layer_norm(x + ff, self.gamma2, self.beta2)
        return x.mean(axis=0)


# ---------------------------------------------------------------------------
# Actions
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Action:
    kind: str          # replace / operand / power / recombine
    position: int
    param: int
    donor: int = -1

    def features(self, length: int) -> np.ndarray:
        kinds = ("replace", "operand", "power", "recombine")
        one_hot = np.zeros(4)
        one_hot[kinds.index(self.kind)] = 1.0
        return np.concatenate([
            one_hot,
            [self.position / max(1, length - 1), (self.param % 16) / 16.0],
            [1.0 if self.donor >= 0 else 0.0, self.donor / 32.0,
             (self.param // 16) / 4.0, 0.0],
        ])


ACTION_DIM = 10


def _same_class_alternatives(op: isa.Op):
    cls = op_class(op)
    if cls in ("alu", "mult", "div", "fpadd", "fpmul") and (
            op.a is None or op.b is None):
        return []
    if cls == "alu":
        kinds = ("add", "sub", "and", "orr", "eor")
        return [isa.Op(kind, dst=op.dst, a=op.a, b=op.b)
                for kind in kinds if kind != op.kind]
    if cls == "mult":
        return [isa.Op("mul", dst=op.dst, a=op.a, b=op.b, width=op.width)]
    if cls == "div":
        return [isa.Op("udiv", dst=op.dst, a=op.a, b=op.b, width=op.width)]
    if cls == "fpadd":
        other = "fsub" if op.kind == "fadd" else "fadd"
        return [isa.Op(other, dst=op.dst, a=op.a, b=op.b)]
    if cls == "fpmul":
        other = "fdiv" if op.kind == "fmul" else "fmul"
        return [isa.Op(other, dst=op.dst, a=op.a, b=op.b)]
    if cls == "mem":
        if op.kind == "ldrf":
            return []
        other = "str" if op.kind == "ldr" else "ldr"
        return [isa.Op(other, dst=op.dst, off=op.off)]
    return []


def _operand_variants(value: int):
    mask = (1 << 64) - 1
    variants = []
    for bit in (0, 7, 15, 23, 31, 39, 47, 55):
        variants.append((value ^ (1 << bit)) & mask)
    variants.append((value + 1) & mask)
    variants.append(((value << 1) | (value >> 63)) & mask)
    variants.append((~value) & mask)
    return variants


def build_catalog(stream: Stream, seeds: Sequence[Stream],
                  max_actions: int = 24) -> list[Action]:
    actions = []
    for index, op in enumerate(stream.body):
        for alt_index, alt in enumerate(_same_class_alternatives(op)):
            actions.append(Action("replace", index, alt_index))
    for index, op in enumerate(stream.setup):
        if op.kind == "mov" and op.imm is not None:
            for variant in range(11):
                actions.append(Action("operand", index, variant))
    for index in range(len(stream.body) + 1):
        for pattern in range(3):
            actions.append(Action("power", index, pattern))
    for donor in range(len(seeds)):
        if len(seeds[donor].body) >= 2:
            actions.append(Action("recombine", 0, 0, donor))
    # Deduplicate while preserving order, then cap deterministically.
    unique, seen = [], set()
    for action in actions:
        key = (action.kind, action.position, action.param, action.donor)
        if key not in seen:
            seen.add(key)
            unique.append(action)
    if len(unique) > max_actions:
        stride = len(unique) / max_actions
        unique = [unique[int(index * stride)] for index in range(max_actions)]
    return unique


def apply_action(stream: Stream, action: Action,
                 seeds: Sequence[Stream]) -> Stream:
    body = list(stream.body)
    setup = list(stream.setup)
    if action.kind == "replace" and body:
        index = action.position % len(body)
        alternatives = _same_class_alternatives(body[index])
        if alternatives:
            body[index] = alternatives[action.param % len(alternatives)]
    elif action.kind == "operand" and setup:
        index = action.position % len(setup)
        op = setup[index]
        if op.kind == "mov" and op.imm is not None:
            variants = _operand_variants(op.imm)
            setup[index] = replace(op, imm=variants[action.param % len(variants)])
    elif action.kind == "power":
        pattern = action.param % 3
        structure = ("div", "fpadd", "fpmul")[pattern]
        segment = list(power.type2_oscillation(structure, period=8,
                                               iterations=1).body)
        index = min(action.position, len(body))
        body[index:index] = segment
    elif action.kind == "recombine" and seeds:
        donor = seeds[action.donor % len(seeds)]
        if len(donor.body) >= 2 and len(body) >= 2:
            cut = max(1, len(body) // 2)
            take = max(1, len(donor.body) // 2)
            body[cut:cut] = list(donor.body[:take])
    return Stream(setup=tuple(setup), body=tuple(body),
                  iterations=stream.iterations, reps=stream.reps,
                  template_id=None)


# ---------------------------------------------------------------------------
# Environment
# ---------------------------------------------------------------------------

@dataclass
class Features:
    sfi: float
    masking: float
    coverage: np.ndarray
    power: power.PowerFeatures
    length: int
    entropy: float

    def as_dict(self):
        return {
            "sfi_proxy": round(self.sfi, 6),
            "masking_penalty": round(self.masking, 6),
            "coverage": [round(float(value), 6) for value in self.coverage],
            "power": self.power.as_dict(),
            "body_length": self.length,
            "entropy": round(self.entropy, 6),
        }


FAST_BITS = (0, 7, 15, 23, 31, 39, 47, 55)


def measure(stream: Stream) -> Features:
    result = avalanche(stream, bits=FAST_BITS, transient=True,
                       positions=(0, max(0, len(stream.body) // 2),
                                  max(0, len(stream.body) - 1)),
                       pre_roll=100)
    cov = coverage(stream)
    classes = [op_class(op) for op in stream.body]
    counts = np.array([classes.count(name) for name in CLASSES], dtype=float)
    probs = counts / counts.sum() if counts.sum() else counts
    entropy = float(-sum(p * math.log(p) for p in probs if p > 0))
    return Features(sfi=result.word_flip_ratio,
                    masking=result.masking_penalty,
                    coverage=cov, power=power.power_features(stream),
                    length=len(stream.body), entropy=entropy)


def state_vector(features: Features, encoder: TransformerEncoder,
                 stream: Stream) -> np.ndarray:
    embedding = encoder.encode(stream.body)
    return np.concatenate([
        embedding,
        features.coverage,
        [features.power.average / 6.0, features.power.peak / 6.0,
         features.power.variance / 4.0, features.power.slope],
        [features.masking, min(1.0, features.length / 32.0),
         features.entropy / math.log(len(CLASSES))],
    ])


STATE_DIM = D_MODEL + len(STRUCTURES) + 4 + 3


class Env:
    def __init__(self, seeds: Sequence[Stream], encoder: TransformerEncoder):
        self.seeds = list(seeds)
        self.encoder = encoder
        self.current = None
        self.current_features = None
        self.parent_features = None
        self.step_index = 0

    def reset(self, rng: random.Random) -> np.ndarray:
        self.current = rng.choice(self.seeds)
        self.current_features = measure(self.current)
        self.parent_features = self.current_features
        self.step_index = 0
        return state_vector(self.current_features, self.encoder, self.current)

    def catalog(self):
        return build_catalog(self.current, self.seeds)

    def step(self, action: Action):
        parent_features = self.current_features
        child = apply_action(self.current, action, self.seeds)
        child_features = measure(child)
        # Reward terms.
        delta_sfi = child_features.sfi - parent_features.sfi
        delta_cov = 0.5 * float(np.abs(child_features.coverage
                                       - parent_features.coverage).sum())
        delta_power = child_features.power.stress - parent_features.power.stress
        masking = child_features.masking
        overlap = len(set(op_class(op) for op in child.body)
                      & set(op_class(op) for op in self.current.body))
        union = len(set(op_class(op) for op in child.body)
                    | set(op_class(op) for op in self.current.body)) or 1
        redundancy = 1.0 - overlap / union
        reward = (2.0 * delta_sfi + 0.5 * delta_cov + 0.5 * delta_power
                  - 1.0 * masking - 0.3 * redundancy)
        self.current = child
        self.current_features = child_features
        self.step_index += 1
        state = state_vector(child_features, self.encoder, child)
        info = {
            "delta_sfi": delta_sfi, "delta_coverage": delta_cov,
            "delta_power": delta_power, "masking_penalty": masking,
            "redundancy_penalty": redundancy, "reward": reward,
            **child_features.as_dict(),
        }
        return state, reward, info


# ---------------------------------------------------------------------------
# Policy
# ---------------------------------------------------------------------------

class Policy:
    def __init__(self, seed: int = 20260825, lr: float = 0.02,
                 state_dim: int = STATE_DIM, action_dim: int = ACTION_DIM):
        rng = np.random.default_rng(seed)
        self.w = rng.normal(0, 0.01, (state_dim, action_dim))
        self.b = np.zeros(action_dim)
        self.baseline = 0.0
        self.lr = lr
        self.rng = rng
        self.updates = 0

    def scores(self, state: np.ndarray, actions: Sequence[Action],
               length: int) -> np.ndarray:
        feats = np.stack([action.features(length) for action in actions])
        return feats @ (self.w.T @ state) + feats @ self.b

    @staticmethod
    def _softmax(x: np.ndarray) -> np.ndarray:
        shifted = x - x.max()
        exp = np.exp(shifted)
        return exp / exp.sum()

    def sample(self, state, actions, length):
        probs = self._softmax(self.scores(state, actions, length))
        index = int(self.rng.choice(len(actions), p=probs))
        return actions[index], math.log(max(1e-12, probs[index])), probs

    def update(self, state, actions, chosen, advantage, length):
        feats = np.stack([action.features(length) for action in actions])
        probs = self._softmax(self.scores(state, actions, length))
        expected = probs @ feats
        grad_w = np.outer(state, feats[chosen] - expected) * advantage
        grad_b = (np.eye(len(actions))[chosen] - probs) @ feats
        # grad_b has shape (action_dim,); scale by advantage.
        self.w += self.lr * grad_w
        self.b += self.lr * advantage * grad_b
        self.baseline += 0.05 * (advantage - self.baseline)
        self.updates += 1

    def save(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({
            "schema": "sdcfuzz.rl.policy.v1",
            "state_dim": int(self.w.shape[0]),
            "action_dim": int(self.w.shape[1]),
            "w": self.w.tolist(), "b": self.b.tolist(),
            "baseline": self.baseline, "lr": self.lr,
            "updates": self.updates,
        }, indent=2) + "\n")

    @classmethod
    def load(cls, path: Path):
        payload = json.loads(Path(path).read_text())
        policy = cls()
        policy.w = np.array(payload["w"], dtype=float)
        policy.b = np.array(payload["b"], dtype=float)
        policy.baseline = payload.get("baseline", 0.0)
        policy.lr = payload.get("lr", 0.02)
        policy.updates = payload.get("updates", 0)
        return policy


class RandomPolicy:
    def __init__(self, seed: int = 20260825):
        self.rng = np.random.default_rng(seed)

    def sample(self, state, actions, length):
        probs = np.ones(len(actions)) / len(actions)
        index = int(self.rng.choice(len(actions), p=probs))
        return actions[index], math.log(probs[index]), probs

    def update(self, *args, **kwargs):
        return


# ---------------------------------------------------------------------------
# Training
# ---------------------------------------------------------------------------

def seed_streams(iterations: int = 10):
    streams = []
    for template in TEMPLATES:
        streams.append(Stream(setup=tuple(template.setup),
                              body=tuple(template.body),
                              iterations=iterations, reps=16,
                              template_id=template.id))
    for structure in ("div", "fpadd", "fpmul", "l1d"):
        stream = power.type1_continuous(structure, iterations=iterations)
        streams.append(Stream(setup=stream.setup, body=stream.body,
                              iterations=iterations, reps=16))
    return streams


def serialize_stream(stream: Stream):
    return {
        "setup": [op.__dict__ for op in stream.setup],
        "body": [op.__dict__ for op in stream.body],
        "iterations": stream.iterations, "reps": stream.reps,
    }


def train(episodes: int = 200, steps: int = 6, seed: int = 20260825,
          gamma: float = 0.9, outdir: Path = Path("m5out/phase2-rl")):
    rng = random.Random(seed)
    encoder = TransformerEncoder(seed=seed)
    seeds = seed_streams()
    env = Env(seeds, encoder)
    policy = Policy(seed=seed)
    random_policy = RandomPolicy(seed=seed + 1)

    def run_episode(active_policy, learn: bool):
        state = env.reset(rng)
        trajectory = []
        total = 0.0
        best = None
        best_fp = None
        action_counts = {"replace": 0, "operand": 0, "power": 0,
                         "recombine": 0}
        for _ in range(steps):
            catalog = env.catalog()
            if not catalog:
                break
            action, logp, probs = active_policy.sample(
                state, catalog, len(env.current.body))
            next_state, reward, info = env.step(action)
            trajectory.append((state, catalog, catalog.index(action), reward,
                               len(env.current.body)))
            action_counts[action.kind] += 1
            total += reward
            if best is None or info["sfi_proxy"] > best[0]:
                best = (info["sfi_proxy"], env.current)
            fp_ops = {"fadd", "fsub", "fmul", "fdiv"}
            if any(op.kind in fp_ops for op in env.current.body):
                if best_fp is None or info["sfi_proxy"] > best_fp[0]:
                    best_fp = (info["sfi_proxy"], env.current)
            state = next_state
        if learn and trajectory:
            returns, running = [], 0.0
            for _, _, _, reward, _ in reversed(trajectory):
                running = reward + gamma * running
                returns.append(running)
            returns.reverse()
            mean = sum(returns) / len(returns)
            std = (sum((value - mean) ** 2 for value in returns)
                   / len(returns)) ** 0.5 or 1.0
            for (state, catalog, index, _, length), value in zip(trajectory,
                                                                  returns):
                advantage = (value - mean) / std
                policy.update(state, catalog, index, advantage, length)
        return total, best, best_fp, action_counts

    history = []
    best_overall = None
    best_fp_overall = None
    aggregate_actions = {"replace": 0, "operand": 0, "power": 0,
                         "recombine": 0}
    for episode in range(episodes):
        total, best, best_fp, counts = run_episode(policy, learn=True)
        for key, value in counts.items():
            aggregate_actions[key] += value
        history.append({"episode": episode, "reward": total,
                        "best_sfi": best[0] if best else 0.0})
        if best and (best_overall is None or best[0] > best_overall[0]):
            best_overall = best
        if best_fp and (best_fp_overall is None
                        or best_fp[0] > best_fp_overall[0]):
            best_fp_overall = best_fp
        if (episode + 1) % 20 == 0:
            recent = history[-20:]
            print(f"  episode {episode + 1}: "
                  f"reward={sum(r['reward'] for r in recent) / len(recent):+.3f} "
                  f"best_sfi={max(r['best_sfi'] for r in recent):.3f}",
                  flush=True)

    # Random-policy baseline, same seeds and budget.
    baseline_rewards = []
    baseline_best = 0.0
    for _ in range(max(10, episodes // 10)):
        total, best, _, _ = run_episode(random_policy, learn=False)
        baseline_rewards.append(total)
        if best:
            baseline_best = max(baseline_best, best[0])

    outdir.mkdir(parents=True, exist_ok=True)
    policy.save(outdir / "policy.json")
    payload = {
        "schema": "sdcfuzz.rl.training.v1",
        "seed": seed, "episodes": episodes, "steps": steps, "gamma": gamma,
        "state_dim": STATE_DIM, "action_dim": ACTION_DIM,
        "seed_streams": len(seeds),
        "history": history,
        "trained_mean_reward": sum(row["reward"] for row in history)
        / len(history),
        "baseline_mean_reward": sum(baseline_rewards) / len(baseline_rewards)
        if baseline_rewards else 0.0,
        "trained_best_sfi": best_overall[0] if best_overall else 0.0,
        "baseline_best_sfi": baseline_best,
        "action_counts": aggregate_actions,
        "trained_best_fp_sfi": best_fp_overall[0] if best_fp_overall else None,
    }
    (outdir / "training.json").write_text(json.dumps(payload, indent=2) + "\n")
    if best_overall:
        (outdir / "best_stream.json").write_text(
            json.dumps(serialize_stream(best_overall[1]), indent=2) + "\n")
    if best_fp_overall:
        (outdir / "best_fp_stream.json").write_text(
            json.dumps(serialize_stream(best_fp_overall[1]), indent=2) + "\n")
    return payload


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--episodes", type=int, default=200)
    parser.add_argument("--steps", type=int, default=6)
    parser.add_argument("--seed", type=int, default=20260825)
    parser.add_argument("--outdir", type=Path, default=Path("m5out/phase2-rl"))
    args = parser.parse_args(argv)
    payload = train(args.episodes, args.steps, args.seed, outdir=args.outdir)
    print(json.dumps({key: payload[key] for key in
                      ("episodes", "seed_streams", "trained_mean_reward",
                       "baseline_mean_reward", "trained_best_sfi",
                       "baseline_best_sfi")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
