from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Literal


class TeamSide(str, Enum):
    HOME = "home"
    AWAY = "away"

    def other(self) -> TeamSide:
        return TeamSide.AWAY if self is TeamSide.HOME else TeamSide.HOME


MarkKind = Literal[
    "serve_circle",
    "serve_triangle",
    "point_slash",
    "point_triangle",
    "side_out_dash",
    "side_out_box_scoring",
    "side_out_box_running",
    "substitution",
    "timeout_serving",
    "timeout_receiving",
    "replay",
    "reservice",
    "libero_position_marker",
]


@dataclass
class ScoringMark:
    kind: MarkKind
    team: TeamSide
    service_row: int  # 0-5 → Roman I-VI
    value: int | str | None = None
    entering: int | None = None
    leaving: int | None = None
    meta: dict[str, Any] = field(default_factory=dict)


@dataclass
class RunningScoreMark:
    team: TeamSide
    point_number: int
    kind: Literal["slash", "box", "triangle"]


@dataclass
class PlayerNumberChange:
    team: TeamSide
    service_row: int
    old_number: int
    new_number: int


@dataclass
class TimeoutRecord:
    team: TeamSide
    slot_index: int  # 0 or 1
    score_team: int
    score_opponent: int


@dataclass
class SetConfig:
    set_number: int = 1
    deciding_set: bool = False
    target_score: int = 25
    win_by: int = 2
    max_score: int = 30
    court_switch_at: int | None = None

    @classmethod
    def for_set_number(cls, set_number: int) -> SetConfig:
        if set_number == 5:
            return cls(
                set_number=5,
                deciding_set=True,
                target_score=15,
                max_score=17,
                court_switch_at=8,
            )
        return cls(set_number=set_number)


@dataclass
class TeamState:
    name: str
    service_order: list[int]  # jersey numbers slots I-VI
    libero_number: int | None = None
    libero_serve_row: int | None = None
    court: list[int] = field(default_factory=list)  # positions 1-6
    score: int = 0
    subs_used: int = 0
    timeouts_used: int = 0
    active_service_row: int = 0
    libero_replacing_slot: int | None = None


@dataclass
class RallyRecord:
    winner: TeamSide
    home_score_after: int
    away_score_after: int
    marks: list[ScoringMark]
    running_marks: list[RunningScoreMark]


@dataclass
class SetEvent:
    type: str
    payload: dict[str, Any]
    marks: list[ScoringMark] = field(default_factory=list)
    running_marks: list[RunningScoreMark] = field(default_factory=list)
    player_changes: list[PlayerNumberChange] = field(default_factory=list)
    timeout: TimeoutRecord | None = None


@dataclass
class SetState:
    config: SetConfig
    home: TeamState
    away: TeamState
    serving: TeamSide
    first_server: TeamSide
    events: list[SetEvent] = field(default_factory=list)
    completed: bool = False
    winner: TeamSide | None = None
    court_switched: bool = False

    def team(self, side: TeamSide) -> TeamState:
        return self.home if side is TeamSide.HOME else self.away

    def opponent_score(self, side: TeamSide) -> int:
        return self.team(side.other()).score
