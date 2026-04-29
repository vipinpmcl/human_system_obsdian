from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Literal


@dataclass(frozen=True)
class Observation:
    date: date
    slot: str
    state: str
    raw: str
    value: float | int | bool | None


@dataclass
class StateDef:
    name: str
    type: Literal["ordinal", "gaussian", "boolean", "count", "duration"]
    status: Literal["active", "retired"]
    primary_problem: str | None
    related_problems: list[str]
    schema_version: int
    criteria: dict
    history: list[dict] = field(default_factory=list)


@dataclass
class ProblemDef:
    name: str
    status: Literal["active", "graduated", "revived"]
    state_names: list[str]
    aggregation: str
    graduated: date | None


@dataclass
class SlotDef:
    name: str
    time: str | None
    state_names: list[str]


@dataclass
class Signal:
    state: str
    status: Literal["good_enough", "not_yet", "insufficient_data"]
    observation_count: int
    window_days: int
    reasons: list[str]
