"""F0 / F5 / F6 fault-injection state machines.

Semantics (pinned by the v3.2 task):

F0  one eligible event triggers exactly one injection, then the injector is
    spent.  The eligible event is chosen by a seeded uniform draw inside
    ``span_events`` after ``warmup_events`` (or by a fixed 1-based
    ``event_ordinal`` when supplied).
F5  while the fault condition is active, *every* eligible event after warm-up
    receives the same condition.  This is per-event reapplication, not a
    physical latch.  ``injected`` counts condition applications, including
    those where the value already equals the stuck value (``nochange``).
F6  a named trigger condition fires once; the actual injection happens at that
    trigger event.  ``on_eligible`` never fires F6.

The manager is deliberately independent of gem5 so the semantics can be
unit-tested on the host.  The C++ hook is responsible for calling it at the
real hook site and for recording the affected dynamic instruction.
"""
from __future__ import annotations

from dataclasses import dataclass, field

VALID_MODES = ("F0", "F5", "F6")


@dataclass
class FaultManager:
    mode: str
    warmup_events: int = 0
    span_events: int = 1
    max_faults: int = 1
    rng_seed: int = 1
    target_event: str | None = None
    event_ordinal: int = 0

    attempted: int = 0
    eligible: int = 0
    injected: int = 0
    value_changed: int = 0
    nochange: int = 0
    trigger_events: int = 0
    fired: bool = False
    next_fire: int = 0
    _rng: int = field(init=False, repr=False)

    def __post_init__(self) -> None:
        if self.mode not in VALID_MODES:
            raise ValueError(f"mode must be one of {VALID_MODES}, got {self.mode!r}")
        if self.warmup_events < 0 or self.span_events < 1:
            raise ValueError("warmup_events must be >=0 and span_events must be >=1")
        self._rng = (self.rng_seed or 1) & ((1 << 64) - 1)

    def _lcg(self) -> int:
        # Deterministic LCG; the reference implementation only needs
        # reproducibility across host tests, not cryptographic quality.
        self._rng = (self._rng * 6364136223846793005 + 1442695040888963407) & ((1 << 64) - 1)
        return self._rng

    def _record(self, value_changed: bool) -> None:
        self.injected += 1
        if value_changed:
            self.value_changed += 1
        else:
            self.nochange += 1

    def _budget_left(self) -> bool:
        return self.max_faults == 0 or self.injected < self.max_faults

    def on_eligible(self, is_target: bool = True, value_changed: bool = True) -> bool:
        """Register one eligible event; return True iff it receives the fault."""
        if not is_target:
            return False
        self.attempted += 1
        self.eligible += 1

        if self.mode == "F0":
            if self.fired or not self._budget_left():
                return False
            if self.eligible <= self.warmup_events:
                return False
            if self.event_ordinal > 0:
                fire_at = self.warmup_events + self.event_ordinal
            else:
                if self.next_fire == 0:
                    self.next_fire = (self.warmup_events + 1 +
                                      (self._lcg() % self.span_events))
                fire_at = self.next_fire
            if self.eligible < fire_at:
                return False
            self.fired = True
            self._record(value_changed)
            return True

        if self.mode == "F5":
            if self.eligible <= self.warmup_events:
                return False
            if not self._budget_left():
                return False
            self._record(value_changed)
            return True

        # F6 never fires on the generic eligible stream.
        return False

    def on_f6_event(self, event_name: str, is_target: bool = True,
                    value_changed: bool = True) -> bool:
        """Register a named F6 trigger event; return True iff it fires."""
        if not is_target:
            return False
        self.trigger_events += 1
        if self.mode != "F6" or self.fired or not self._budget_left():
            return False
        if self.target_event is not None and event_name != self.target_event:
            return False
        self.fired = True
        self._record(value_changed)
        return True

    def summary(self) -> dict:
        return {
            "mode": self.mode,
            "attempted": self.attempted,
            "eligible": self.eligible,
            "injected": self.injected,
            "value_changed": self.value_changed,
            "nochange": self.nochange,
            "trigger_events": self.trigger_events,
            "fired": self.fired,
            "warmup_events": self.warmup_events,
            "span_events": self.span_events,
            "max_faults": self.max_faults,
            "target_event": self.target_event,
        }
