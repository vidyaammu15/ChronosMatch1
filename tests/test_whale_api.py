"""test_whale_api.py

API and Integration tests for the Whale Event detection endpoint (/api/whale)
and simulation integration in frontend/app.py.
"""
import json
import pytest

from frontend.app import app, state
from engine.whale_detector import WhaleEvent


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_api_whale_initial_state_empty(client):
    """Initially or after reset, no whale event should be detected."""
    state.reset_state()
    response = client.get("/api/whale")
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data["whale_detected"] is False
    assert data["event"] is None


def test_api_whale_with_detected_event(client):
    """When a WhaleEvent is registered in state, /api/whale returns its details."""
    state.last_whale_event = WhaleEvent(
        order_id=999,
        side="BUY",
        total_quantity=50,
        levels_cleared=3,
        prices_cleared=[65010, 65020, 65030],
        total_matched_qty=30,
        trade_count=3,
        timestamp_ns=123456789,
    )

    response = client.get("/api/whale")
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data["whale_detected"] is True
    assert data["event"]["order_id"] == 999
    assert data["event"]["side"] == "BUY"
    assert data["event"]["levels_cleared"] == 3
    assert data["event"]["prices_cleared"] == [65010, 65020, 65030]
    assert data["event"]["total_matched_qty"] == 30


def test_api_reset_clears_whale_event(client):
    """POST /api/reset should clear the last whale event."""
    state.last_whale_event = WhaleEvent(
        order_id=999,
        side="BUY",
        total_quantity=50,
        levels_cleared=2,
        prices_cleared=[65010, 65020],
        total_matched_qty=20,
        trade_count=2,
        timestamp_ns=123456789,
    )

    reset_res = client.post("/api/reset")
    assert reset_res.status_code == 200

    response = client.get("/api/whale")
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data["whale_detected"] is False
    assert data["event"] is None
