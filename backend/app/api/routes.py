from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.engine.models import TeamSide
from app.schemas import (
    LiberoExitRequest,
    LiberoReplaceRequest,
    RallyRequest,
    SetCreatedResponse,
    SetStateResponse,
    StartSetRequest,
    SubstitutionRequest,
    TimeoutRequest,
)
from app.store import SetSeed, store

router = APIRouter(prefix="/api/sets", tags=["sets"])


def _side(value: str) -> TeamSide:
    return TeamSide.HOME if value == "home" else TeamSide.AWAY


def _response(session_id: str, engine) -> SetStateResponse:
    return SetStateResponse(set_id=session_id, state=engine.snapshot())


@router.post("", response_model=SetCreatedResponse)
def start_set(body: StartSetRequest) -> SetCreatedResponse:
    seed = SetSeed(
        home_name=body.home_name,
        away_name=body.away_name,
        home_lineup=body.home_lineup,
        away_lineup=body.away_lineup,
        first_server=_side(body.first_server),
        set_number=body.set_number,
        home_libero=body.home_libero,
        away_libero=body.away_libero,
    )
    session = store.create_set(seed)
    engine = session.engine()
    return SetCreatedResponse(set_id=session.id, state=engine.snapshot())


@router.get("/{set_id}", response_model=SetStateResponse)
def get_set(set_id: str) -> SetStateResponse:
    try:
        session = store.get(set_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return _response(set_id, session.engine())


@router.post("/{set_id}/serve", response_model=SetStateResponse)
def record_serve(set_id: str) -> SetStateResponse:
    session = _require_session(set_id)
    engine = session.engine()
    try:
        engine.record_serve_contact()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    session.sync_events(engine)
    return _response(set_id, engine)


@router.post("/{set_id}/rally", response_model=SetStateResponse)
def record_rally(set_id: str, body: RallyRequest) -> SetStateResponse:
    session = _require_session(set_id)
    engine = session.engine()
    try:
        engine.record_rally(_side(body.winner))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    session.sync_events(engine)
    return _response(set_id, engine)


@router.post("/{set_id}/substitution", response_model=SetStateResponse)
def record_substitution(set_id: str, body: SubstitutionRequest) -> SetStateResponse:
    session = _require_session(set_id)
    engine = session.engine()
    try:
        engine.record_substitution(_side(body.team), body.entering, body.leaving)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    session.sync_events(engine)
    return _response(set_id, engine)


@router.post("/{set_id}/timeout", response_model=SetStateResponse)
def record_timeout(set_id: str, body: TimeoutRequest) -> SetStateResponse:
    session = _require_session(set_id)
    engine = session.engine()
    try:
        engine.record_timeout(_side(body.team))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    session.sync_events(engine)
    return _response(set_id, engine)


@router.post("/{set_id}/libero/in", response_model=SetStateResponse)
def libero_in(set_id: str, body: LiberoReplaceRequest) -> SetStateResponse:
    session = _require_session(set_id)
    engine = session.engine()
    try:
        engine.record_libero_replace(_side(body.team), body.slot)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    session.sync_events(engine)
    return _response(set_id, engine)


@router.post("/{set_id}/libero/out", response_model=SetStateResponse)
def libero_out(set_id: str, body: LiberoExitRequest) -> SetStateResponse:
    session = _require_session(set_id)
    engine = session.engine()
    try:
        engine.record_libero_exit(_side(body.team))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    session.sync_events(engine)
    return _response(set_id, engine)


@router.post("/{set_id}/undo", response_model=SetStateResponse)
def undo(set_id: str) -> SetStateResponse:
    try:
        session = store.undo(set_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _response(set_id, session.engine())


def _require_session(set_id: str):
    try:
        return store.get(set_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
