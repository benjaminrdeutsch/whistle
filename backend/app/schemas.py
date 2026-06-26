from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator


class StartSetRequest(BaseModel):
    home_name: str = Field(min_length=1, max_length=80)
    away_name: str = Field(min_length=1, max_length=80)
    home_lineup: list[int] = Field(min_length=6, max_length=6)
    away_lineup: list[int] = Field(min_length=6, max_length=6)
    first_server: Literal["home", "away"]
    set_number: int = Field(ge=1, le=5)
    home_libero: int | None = None
    away_libero: int | None = None

    @field_validator("home_lineup", "away_lineup")
    @classmethod
    def validate_lineup(cls, value: list[int]) -> list[int]:
        if len(set(value)) != 6:
            raise ValueError("Lineup numbers must be unique")
        return value


class RallyRequest(BaseModel):
    winner: Literal["home", "away"]


class SubstitutionRequest(BaseModel):
    team: Literal["home", "away"]
    entering: int
    leaving: int


class TimeoutRequest(BaseModel):
    team: Literal["home", "away"]


class LiberoReplaceRequest(BaseModel):
    team: Literal["home", "away"]
    slot: int = Field(ge=0, le=5)


class LiberoExitRequest(BaseModel):
    team: Literal["home", "away"]


class SetCreatedResponse(BaseModel):
    set_id: str
    state: dict


class SetStateResponse(BaseModel):
    set_id: str
    state: dict
