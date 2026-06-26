from __future__ import annotations

from copy import deepcopy

from app.engine.models import (
    PlayerNumberChange,
    RallyRecord,
    RunningScoreMark,
    ScoringMark,
    SetConfig,
    SetEvent,
    SetState,
    TeamSide,
    TeamState,
    TimeoutRecord,
)

ROMAN = ("I", "II", "III", "IV", "V", "VI")


def _rotate_court_clockwise(court: list[int]) -> list[int]:
    """Each player moves to the next position; new server was at position 2."""
    return court[1:] + [court[0]]


def _initial_court(lineup: list[int], receiving: bool) -> list[int]:
    """Map serving-order slots I-VI to court positions 1-6 at set start."""
    if receiving:
        # Slot I at right front (pos 2); pos 1 holds slot VI.
        return [lineup[5], lineup[0], lineup[1], lineup[2], lineup[3], lineup[4]]
    return list(lineup)


def _server_jersey(team: TeamState) -> int:
    return team.court[0]


def _server_service_row(team: TeamState) -> int:
    jersey = _server_jersey(team)
    for idx, slot_jersey in enumerate(team.service_order):
        if slot_jersey == jersey:
            return idx
    return team.active_service_row


def _is_libero_serving(team: TeamState) -> bool:
    if team.libero_number is None:
        return False
    return _server_jersey(team) == team.libero_number


def _next_service_row_after_rotation(team: TeamState) -> int:
    jersey = _server_jersey(team)
    for idx, slot in enumerate(team.service_order):
        if slot == jersey:
            return idx
    return team.active_service_row


class SetEngine:
    def __init__(self, state: SetState):
        self.state = state
        self._record_events = True

    @classmethod
    def start_set(
        cls,
        *,
        home_name: str,
        away_name: str,
        home_lineup: list[int],
        away_lineup: list[int],
        first_server: TeamSide,
        set_number: int = 1,
        home_libero: int | None = None,
        away_libero: int | None = None,
    ) -> SetEngine:
        if len(home_lineup) != 6 or len(away_lineup) != 6:
            raise ValueError("Each lineup must contain exactly six players in serving order")

        config = SetConfig.for_set_number(set_number)
        receiving = first_server.other()
        home = TeamState(
            name=home_name,
            service_order=list(home_lineup),
            libero_number=home_libero,
            court=_initial_court(home_lineup, receiving=first_server is TeamSide.AWAY),
            active_service_row=0,
        )
        away = TeamState(
            name=away_name,
            service_order=list(away_lineup),
            libero_number=away_libero,
            court=_initial_court(away_lineup, receiving=first_server is TeamSide.HOME),
            active_service_row=0,
        )
        state = SetState(
            config=config,
            home=home,
            away=away,
            serving=first_server,
            first_server=first_server,
        )
        serving_team = state.team(first_server)
        serving_team.active_service_row = _server_service_row(serving_team)
        return cls(state)

    def record_rally(self, winner: TeamSide) -> RallyRecord:
        if self.state.completed:
            raise ValueError("Set is already complete")

        serving = self.state.serving
        serving_team = self.state.team(serving)
        receiving = serving.other()
        receiving_team = self.state.team(receiving)

        marks: list[ScoringMark] = []
        running: list[RunningScoreMark] = []
        libero_serving = _is_libero_serving(serving_team)
        service_row = _server_service_row(serving_team)

        if winner is serving:
            serving_team.score += 1
            point = serving_team.score
            if libero_serving:
                marks.append(ScoringMark("point_triangle", serving, service_row, point))
                running.append(RunningScoreMark(serving, point, "triangle"))
            else:
                marks.append(ScoringMark("point_slash", serving, service_row, point))
                running.append(RunningScoreMark(serving, point, "slash"))
        else:
            receiving_team.score += 1
            point = receiving_team.score
            marks.append(ScoringMark("side_out_dash", serving, service_row))
            running.append(RunningScoreMark(receiving, point, "box"))
            receiving_team.court = _rotate_court_clockwise(receiving_team.court)
            next_row = _next_service_row_after_rotation(receiving_team)
            receiving_team.active_service_row = next_row
            marks.append(
                ScoringMark("side_out_box_scoring", receiving, next_row, point)
            )
            self.state.serving = receiving

        self._maybe_switch_court()
        self._check_set_complete()

        event = SetEvent(
            type="rally",
            payload={"winner": winner.value},
            marks=marks,
            running_marks=running,
        )
        self._append_event(event)

        return RallyRecord(
            winner=winner,
            home_score_after=self.state.home.score,
            away_score_after=self.state.away.score,
            marks=marks,
            running_marks=running,
        )

    def record_substitution(
        self, team_side: TeamSide, entering: int, leaving: int
    ) -> SetEvent:
        if self.state.completed:
            raise ValueError("Set is already complete")

        team = self.state.team(team_side)
        if team.subs_used >= 18:
            raise ValueError("Substitution limit reached (18)")

        try:
            slot = team.service_order.index(leaving)
        except ValueError as exc:
            raise ValueError(f"Player {leaving} is not on the court in service order") from exc

        serving = self.state.serving
        is_serving_team = serving is team_side
        server_row = _server_service_row(self.state.team(serving))

        mark = ScoringMark(
            "substitution",
            team_side,
            server_row,
            entering=entering,
            leaving=leaving,
            meta={"receiving_notation": not is_serving_team},
        )

        team.service_order[slot] = entering
        for pos, jersey in enumerate(team.court):
            if jersey == leaving:
                team.court[pos] = entering
        team.subs_used += 1

        change = PlayerNumberChange(team_side, slot, leaving, entering)
        event = SetEvent(
            type="substitution",
            payload={
                "team": team_side.value,
                "entering": entering,
                "leaving": leaving,
            },
            marks=[mark],
            player_changes=[change],
        )
        self._append_event(event)
        return event

    def record_timeout(self, team_side: TeamSide) -> SetEvent:
        if self.state.completed:
            raise ValueError("Set is already complete")

        team = self.state.team(team_side)
        if team.timeouts_used >= 2:
            raise ValueError("Timeout limit reached (2 per team)")

        serving = self.state.serving
        is_serving_team = serving is team_side
        server_row = _server_service_row(self.state.team(serving))
        kind = "timeout_serving" if is_serving_team else "timeout_receiving"

        team_score = team.score
        opponent_score = self.state.opponent_score(team_side)
        mark = ScoringMark(kind, serving, server_row)
        timeout = TimeoutRecord(
            team=team_side,
            slot_index=team.timeouts_used,
            score_team=team_score,
            score_opponent=opponent_score,
        )
        team.timeouts_used += 1

        event = SetEvent(
            type="timeout",
            payload={"team": team_side.value},
            marks=[mark],
            timeout=timeout,
        )
        self._append_event(event)
        return event

    def record_libero_replace(self, team_side: TeamSide, replacing_slot: int) -> SetEvent:
        """Libero enters for the player in serving-order slot (0-5)."""
        team = self.state.team(team_side)
        if team.libero_number is None:
            raise ValueError("No libero designated for this team")

        replaced = team.service_order[replacing_slot]
        if replaced == team.libero_number:
            raise ValueError("Libero cannot replace themselves")

        for pos, jersey in enumerate(team.court):
            if jersey == replaced:
                team.court[pos] = team.libero_number
        team.libero_replacing_slot = replacing_slot

        event = SetEvent(
            type="libero_in",
            payload={
                "team": team_side.value,
                "slot": replacing_slot,
                "replaced": replaced,
            },
        )
        self._append_event(event)
        return event

    def record_libero_exit(self, team_side: TeamSide) -> SetEvent:
        team = self.state.team(team_side)
        if team.libero_replacing_slot is None:
            raise ValueError("Libero is not on court")

        slot = team.libero_replacing_slot
        restored = team.service_order[slot]
        for pos, jersey in enumerate(team.court):
            if jersey == team.libero_number:
                team.court[pos] = restored
        team.libero_replacing_slot = None

        event = SetEvent(
            type="libero_out",
            payload={"team": team_side.value, "slot": slot},
        )
        self._append_event(event)
        return event

    def mark_libero_serve_position(self, team_side: TeamSide) -> SetEvent:
        """First libero serve in a set — triangle around the service-order Roman numeral."""
        team = self.state.team(team_side)
        if team.libero_number is None:
            raise ValueError("No libero designated")
        if team.libero_serve_row is not None:
            raise ValueError("Libero serve position already marked")

        if not _is_libero_serving(team):
            raise ValueError("Libero is not the current server")

        row = _server_service_row(team)
        team.libero_serve_row = row
        mark = ScoringMark("libero_position_marker", team_side, row)
        event = SetEvent(
            type="libero_serve_position",
            payload={"team": team_side.value, "row": row},
            marks=[mark],
        )
        self._append_event(event)
        return event

    def ensure_libero_serve_marked(self, team: TeamState, team_side: TeamSide) -> list[ScoringMark]:
        if not _is_libero_serving(team) or team.libero_serve_row is not None:
            return []
        row = _server_service_row(team)
        team.libero_serve_row = row
        mark = ScoringMark("libero_position_marker", team_side, row)
        event = SetEvent(
            type="libero_serve_position",
            payload={"team": team_side.value, "row": row},
            marks=[mark],
        )
        self._append_event(event)
        return [mark]

    def record_serve_contact(self) -> SetEvent:
        team_side = self.state.serving
        team = self.state.team(team_side)
        row = _server_service_row(team)
        libero = _is_libero_serving(team)
        extra: list[ScoringMark] = []

        if libero:
            extra = self.ensure_libero_serve_marked(team, team_side)
            kind = "serve_triangle"
        else:
            kind = "serve_circle"

        mark = ScoringMark(kind, team_side, row)
        marks = extra + [mark]
        event = SetEvent(
            type="serve_contact",
            payload={"team": team_side.value},
            marks=marks,
        )
        self._append_event(event)
        return event

    def _append_event(self, event: SetEvent) -> None:
        if self._record_events:
            self.state.events.append(event)

    def snapshot(self) -> dict:
        return _state_to_dict(self.state)

    def replace_state(self, state: SetState) -> None:
        self.state = state

    def _check_set_complete(self) -> None:
        cfg = self.state.config
        home, away = self.state.home.score, self.state.away.score
        leader = max(home, away)
        trailer = min(home, away)
        target = cfg.target_score
        if leader >= target and leader - trailer >= cfg.win_by:
            self.state.completed = True
            self.state.winner = TeamSide.HOME if home > away else TeamSide.AWAY
        elif leader >= cfg.max_score and leader - trailer >= cfg.win_by:
            self.state.completed = True
            self.state.winner = TeamSide.HOME if home > away else TeamSide.AWAY

    def _maybe_switch_court(self) -> None:
        switch_at = self.state.config.court_switch_at
        if switch_at is None or self.state.court_switched:
            return
        if self.state.home.score >= switch_at or self.state.away.score >= switch_at:
            self.state.court_switched = True

def replay_set(
    *,
    home_name: str,
    away_name: str,
    home_lineup: list[int],
    away_lineup: list[int],
    first_server: TeamSide,
    set_number: int,
    home_libero: int | None,
    away_libero: int | None,
    events: list[SetEvent],
) -> SetEngine:
    engine = SetEngine.start_set(
        home_name=home_name,
        away_name=away_name,
        home_lineup=home_lineup,
        away_lineup=away_lineup,
        first_server=first_server,
        set_number=set_number,
        home_libero=home_libero,
        away_libero=away_libero,
    )
    engine.state.events = []
    engine._record_events = False
    for event in events:
        _apply_event(engine, event)
    engine._record_events = True
    engine.state.events = deepcopy(events)
    return engine


def _apply_event(engine: SetEngine, event: SetEvent) -> None:
    payload = event.payload
    if event.type == "rally":
        engine.record_rally(TeamSide(payload["winner"]))
    elif event.type == "substitution":
        engine.record_substitution(
            TeamSide(payload["team"]),
            payload["entering"],
            payload["leaving"],
        )
    elif event.type == "timeout":
        engine.record_timeout(TeamSide(payload["team"]))
    elif event.type == "libero_in":
        engine.record_libero_replace(TeamSide(payload["team"]), payload["slot"])
    elif event.type == "libero_out":
        engine.record_libero_exit(TeamSide(payload["team"]))
    elif event.type == "serve_contact":
        engine.record_serve_contact()
    elif event.type == "libero_serve_position":
        engine.mark_libero_serve_position(TeamSide(payload["team"]))


def _state_to_dict(state: SetState) -> dict:
    def team_dict(team: TeamState, side: TeamSide) -> dict:
        return {
            "name": team.name,
            "score": team.score,
            "service_order": [
                {"roman": ROMAN[i], "number": team.service_order[i]} for i in range(6)
            ],
            "court": team.court,
            "libero": team.libero_number,
            "libero_serve_row": (
                ROMAN[team.libero_serve_row] if team.libero_serve_row is not None else None
            ),
            "libero_on_court_slot": team.libero_replacing_slot,
            "subs_used": team.subs_used,
            "timeouts_used": team.timeouts_used,
            "active_service_row": ROMAN[team.active_service_row],
            "current_server": _server_jersey(team) if team.court else None,
            "is_libero_serving": _is_libero_serving(team),
            "side": side.value,
        }

    scoring_rows = _build_scoring_grid(state)

    return {
        "set_number": state.config.set_number,
        "deciding_set": state.config.deciding_set,
        "target_score": state.config.target_score,
        "max_score": state.config.max_score,
        "court_switch_at": state.config.court_switch_at,
        "court_switched": state.court_switched,
        "serving": state.serving.value,
        "first_server": state.first_server.value,
        "completed": state.completed,
        "winner": state.winner.value if state.winner else None,
        "home": team_dict(state.home, TeamSide.HOME),
        "away": team_dict(state.away, TeamSide.AWAY),
        "running_score": _build_running_score(state),
        "scoring_section": scoring_rows,
        "timeouts": _collect_timeouts(state),
        "events": [
            {
                "type": e.type,
                "payload": e.payload,
                "marks": [_mark_dict(m) for m in e.marks],
            }
            for e in state.events
        ],
    }


def _mark_dict(mark: ScoringMark) -> dict:
    return {
        "kind": mark.kind,
        "team": mark.team.value,
        "service_row": ROMAN[mark.service_row],
        "value": mark.value,
        "entering": mark.entering,
        "leaving": mark.leaving,
        "meta": mark.meta,
    }


def _build_running_score(state: SetState) -> dict:
    home_marks: list[dict] = []
    away_marks: list[dict] = []
    for event in state.events:
        for rm in event.running_marks:
            entry = {"point": rm.point_number, "kind": rm.kind}
            if rm.team is TeamSide.HOME:
                home_marks.append(entry)
            else:
                away_marks.append(entry)
    return {"home": home_marks, "away": away_marks}


def _build_scoring_grid(state: SetState) -> dict:
    grid: dict[str, list[list[dict]]] = {"home": [[] for _ in range(6)], "away": [[] for _ in range(6)]}
    for event in state.events:
        for mark in event.marks:
            side = mark.team.value
            row = mark.service_row
            grid[side][row].append(_mark_dict(mark))
        for change in event.player_changes:
            side = change.team.value
            # player number changes reflected in service_order snapshot, not grid cells
            grid[side]  # touch for lint
    return grid


def _collect_timeouts(state: SetState) -> dict:
    home: list[dict] = []
    away: list[dict] = []
    for event in state.events:
        if event.timeout:
            entry = {
                "score": f"{event.timeout.score_team} – {event.timeout.score_opponent}",
                "slot": event.timeout.slot_index + 1,
            }
            if event.timeout.team is TeamSide.HOME:
                home.append(entry)
            else:
                away.append(entry)
    return {"home": home, "away": away}
