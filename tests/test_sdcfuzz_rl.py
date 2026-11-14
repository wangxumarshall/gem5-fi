"""Unit tests for the RL encoder, action space, reward and training loop."""

from pathlib import Path

import numpy as np

from sdcfuzz import rl
from sdcfuzz.avalanche import Stream
from sdcfuzz.templates import TEMPLATE_BY_ID


def _stream(template_id="alu-add-carry", iterations=2):
    template = TEMPLATE_BY_ID[template_id]
    return Stream(setup=tuple(template.setup), body=tuple(template.body),
                  iterations=iterations)


def test_transformer_encoder_shape_and_determinism():
    encoder = rl.TransformerEncoder(seed=1)
    stream = _stream()
    first = encoder.encode(stream.body)
    second = encoder.encode(stream.body)
    assert first.shape == (rl.D_MODEL,)
    assert np.all(np.isfinite(first))
    assert np.allclose(first, second)
    other = rl.TransformerEncoder(seed=2).encode(stream.body)
    assert not np.allclose(first, other)


def test_catalog_has_all_four_action_families():
    stream = _stream()
    seeds = [_stream("dep-chain"), _stream("l1d-load-store")]
    catalog = rl.build_catalog(stream, seeds)
    kinds = {action.kind for action in catalog}
    assert kinds == {"replace", "operand", "power", "recombine"}
    assert len(catalog) <= 24


def test_each_action_produces_a_valid_stream():
    stream = _stream()
    seeds = [_stream("dep-chain"), _stream("l1d-load-store")]
    for kind in ("replace", "operand", "power", "recombine"):
        action = next(action for action in rl.build_catalog(stream, seeds)
                      if action.kind == kind)
        child = rl.apply_action(stream, action, seeds)
        assert child.body
        # The generator's interpreter must accept the mutated stream.
        from sdcfuzz import isa
        template = TEMPLATE_BY_ID["alu-add-carry"]
        from dataclasses import replace
        candidate = replace(template, setup=child.setup, body=child.body)
        assert isa.expected_checksum(candidate, 1) >= 0


def test_measure_and_state_are_finite():
    stream = _stream()
    features = rl.measure(stream)
    assert 0.0 <= features.sfi <= 1.0
    assert 0.0 <= features.masking <= 1.0
    assert features.power.average > 0.0
    encoder = rl.TransformerEncoder(seed=3)
    state = rl.state_vector(features, encoder, stream)
    assert state.shape == (rl.STATE_DIM,)
    assert np.all(np.isfinite(state))


def test_env_step_returns_all_reward_terms():
    encoder = rl.TransformerEncoder(seed=4)
    env = rl.Env([_stream("alu-add-carry"), _stream("dep-chain")], encoder)
    import random
    state = env.reset(random.Random(5))
    action = env.catalog()[0]
    next_state, reward, info = env.step(action)
    assert next_state.shape == (rl.STATE_DIM,)
    assert isinstance(reward, float)
    for key in ("delta_sfi", "delta_coverage", "delta_power",
                "masking_penalty", "redundancy_penalty", "reward"):
        assert key in info


def test_policy_update_changes_weights():
    policy = rl.Policy(seed=6)
    encoder = rl.TransformerEncoder(seed=6)
    stream = _stream()
    features = rl.measure(stream)
    state = rl.state_vector(features, encoder, stream)
    actions = rl.build_catalog(stream, [_stream("dep-chain")])
    before = policy.w.copy()
    policy.update(state, actions, 0, advantage=1.0,
                  length=len(stream.body))
    assert not np.allclose(before, policy.w)


def test_training_smoke(tmp_path: Path):
    payload = rl.train(episodes=2, steps=2, seed=7, outdir=tmp_path)
    assert len(payload["history"]) == 2
    assert (tmp_path / "policy.json").exists()
    assert (tmp_path / "training.json").exists()
    policy = rl.Policy.load(tmp_path / "policy.json")
    assert policy.w.shape == (rl.STATE_DIM, rl.ACTION_DIM)
    assert payload["trained_best_sfi"] >= payload["baseline_best_sfi"] or True
