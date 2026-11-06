"""F0/F5/F6 fault-injection state machine (platform side, unit-testable)."""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum

class Mode(str, Enum):
    F0="F0"; F5="F5"; F6="F6"

@dataclass
class FaultManager:
    mode: Mode
    warmup_events: int = 0
    span_events: int = 0
    max_faults: int = 1
    rng: int = 1
    eligible: int = 0
    injected: int = 0
    attempted: int = 0
    armed: bool = False
    spent: bool = False
    next_fire: int = 0
    f6_triggered: bool = False

    def _lcg(self) -> int:
        self.rng = (self.rng * 6364136223846793005 + 1442695040888963407) & ((1<<64)-1)
        return self.rng

    def on_eligible(self, is_target: bool = True) -> bool:
        """Register an eligible event; return True iff this event gets a fault."""
        if not is_target:
            return False
        self.attempted += 1
        self.eligible += 1
        if self.mode == Mode.F5:
            if self.eligible <= self.warmup_events:
                return False
            if self.max_faults and self.injected >= self.max_faults:
                return False
            self.injected += 1
            return True
        if self.mode == Mode.F0:
            if self.spent:
                return False
            if not self.armed:
                self.armed = True
                span = self.span_events or 1
                self.next_fire = self.warmup_events + (self._lcg() % span)
            if self.eligible >= self.next_fire:
                if self.max_faults and self.injected >= self.max_faults:
                    self.spent = True
                    return False
                self.spent = True
                self.injected += 1
                return True
            return False
        if self.mode == Mode.F6:
            return False  # F6 fires on a specific event, not the eligible stream
        raise ValueError(self.mode)

    def on_f6_event(self, is_target: bool = True) -> bool:
        if self.mode != Mode.F6 or not is_target or self.f6_triggered:
            return False
        if self.max_faults and self.injected >= self.max_faults:
            return False
        self.f6_triggered = True
        self.attempted += 1
        self.eligible += 1
        self.injected += 1
        return True

    def summary(self) -> dict:
        return {"mode":self.mode.value,"attempted":self.attempted,"eligible":self.eligible,
                "injected":self.injected,"warmup":self.warmup_events,"span":self.span_events}
