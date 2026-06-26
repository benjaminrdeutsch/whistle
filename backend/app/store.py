from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4

from app.engine.models import SetEvent, TeamSide
from app.engine.set_engine import SetEngine, replay_set


@dataclass
class SetSeed:
    home_name: str
    away_name: str
    home_lineup: list[int]
    away_lineup: list[int]
    first_server: TeamSide
    set_number: int
    home_libero: int | None = None
    away_libero: int | None = None


@dataclass
class SetSession:
    id: str
    seed: SetSeed
    events: list[SetEvent] = field(default_factory=list)

    def engine(self) -> SetEngine:
        if not self.events:
            return SetEngine.start_set(
                home_name=self.seed.home_name,
                away_name=self.seed.away_name,
                home_lineup=self.seed.home_lineup,
                away_lineup=self.seed.away_lineup,
                first_server=self.seed.first_server,
                set_number=self.seed.set_number,
                home_libero=self.seed.home_libero,
                away_libero=self.seed.away_libero,
            )
        return replay_set(
            home_name=self.seed.home_name,
            away_name=self.seed.away_name,
            home_lineup=self.seed.home_lineup,
            away_lineup=self.seed.away_lineup,
            first_server=self.seed.first_server,
            set_number=self.seed.set_number,
            home_libero=self.seed.home_libero,
            away_libero=self.seed.away_libero,
            events=self.events,
        )

    def sync_events(self, engine: SetEngine) -> None:
        self.events = engine.state.events


class SessionStore:
    def __init__(self) -> None:
        self._sets: dict[str, SetSession] = {}

    def create_set(self, seed: SetSeed) -> SetSession:
        session_id = str(uuid4())
        session = SetSession(id=session_id, seed=seed)
        self._sets[session_id] = session
        return session

    def get(self, session_id: str) -> SetSession:
        if session_id not in self._sets:
            raise KeyError(f"Set session {session_id} not found")
        return self._sets[session_id]

    def undo(self, session_id: str) -> SetSession:
        session = self.get(session_id)
        if not session.events:
            raise ValueError("Nothing to undo")
        session.events = session.events[:-1]
        return session


store = SessionStore()
