from app.engine.models import TeamSide
from app.engine.set_engine import SetEngine


def test_serving_team_wins_includes_serve_circle():
    engine = SetEngine.start_set(
        home_name="Eagles",
        away_name="Hawks",
        home_lineup=[1, 2, 3, 4, 5, 6],
        away_lineup=[7, 8, 9, 10, 11, 12],
        first_server=TeamSide.HOME,
        set_number=1,
    )
    result = engine.record_rally(TeamSide.HOME)
    assert result.home_score_after == 1
    assert result.away_score_after == 0
    kinds = [m.kind for m in result.marks]
    assert "serve_circle" in kinds
    assert any(m.kind == "point_slash" and m.value == 1 for m in result.marks)


def test_side_out_includes_serve_then_dash():
    engine = SetEngine.start_set(
        home_name="Eagles",
        away_name="Hawks",
        home_lineup=[1, 2, 3, 4, 5, 6],
        away_lineup=[7, 8, 9, 10, 11, 12],
        first_server=TeamSide.HOME,
        set_number=1,
    )
    result = engine.record_rally(TeamSide.AWAY)
    kinds = [m.kind for m in result.marks]
    assert "serve_circle" in kinds
    assert "side_out_dash" in kinds
    snap = engine.snapshot()
    assert snap["home"]["score"] == 0
    assert snap["away"]["score"] == 1
    assert snap["serving"] == "away"
    assert snap["away"]["current_server"] == 7


def test_consecutive_points_same_server_get_multiple_circles():
    engine = SetEngine.start_set(
        home_name="Eagles",
        away_name="Hawks",
        home_lineup=[1, 2, 3, 4, 5, 6],
        away_lineup=[7, 8, 9, 10, 11, 12],
        first_server=TeamSide.HOME,
    )
    engine.record_rally(TeamSide.HOME)
    result = engine.record_rally(TeamSide.HOME)
    serve_circles = [m for m in result.marks if m.kind == "serve_circle"]
    assert len(serve_circles) == 1


def test_libero_serve_gets_triangle():
    engine = SetEngine.start_set(
        home_name="Eagles",
        away_name="Hawks",
        home_lineup=[1, 2, 3, 4, 5, 6],
        away_lineup=[7, 8, 9, 10, 11, 12],
        first_server=TeamSide.HOME,
        home_libero=99,
    )
    engine.record_libero_replace(TeamSide.HOME, 0)
    result = engine.record_rally(TeamSide.HOME)
    kinds = [m.kind for m in result.marks]
    assert "serve_triangle" in kinds
    assert "libero_position_marker" in kinds
    assert "point_triangle" in kinds


def test_substitution_updates_service_order():
    engine = SetEngine.start_set(
        home_name="Eagles",
        away_name="Hawks",
        home_lineup=[1, 2, 3, 4, 5, 6],
        away_lineup=[7, 8, 9, 10, 11, 12],
        first_server=TeamSide.HOME,
    )
    engine.record_substitution(TeamSide.HOME, entering=20, leaving=3)
    snap = engine.snapshot()
    numbers = [row["number"] for row in snap["home"]["service_order"]]
    assert 20 in numbers
    assert 3 not in numbers
    assert snap["home"]["subs_used"] == 1


def test_timeout_recorded():
    engine = SetEngine.start_set(
        home_name="Eagles",
        away_name="Hawks",
        home_lineup=[1, 2, 3, 4, 5, 6],
        away_lineup=[7, 8, 9, 10, 11, 12],
        first_server=TeamSide.HOME,
    )
    engine.record_rally(TeamSide.HOME)
    engine.record_timeout(TeamSide.AWAY)
    snap = engine.snapshot()
    assert snap["away"]["timeouts_used"] == 1
    assert len(snap["timeouts"]["away"]) == 1


def test_deciding_set_config():
    engine = SetEngine.start_set(
        home_name="Eagles",
        away_name="Hawks",
        home_lineup=[1, 2, 3, 4, 5, 6],
        away_lineup=[7, 8, 9, 10, 11, 12],
        first_server=TeamSide.HOME,
        set_number=5,
    )
    snap = engine.snapshot()
    assert snap["deciding_set"] is True
    assert snap["target_score"] == 15
    assert snap["court_switch_at"] == 8
