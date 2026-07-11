import logging

from fastapi.testclient import TestClient

import backend.request_id_middleware as request_id_middleware
from backend.main import app
from backend.request_id_middleware import REQUEST_ID_HEADER


client = TestClient(app)


def test_request_id_header_is_added_to_response(caplog):
    caplog.set_level(logging.INFO)

    response = client.get("/health")

    request_id = response.headers[REQUEST_ID_HEADER]

    assert response.status_code == 200
    assert request_id
    assert "request_started" in caplog.text
    assert "request_finished" in caplog.text
    assert request_id in caplog.text


def test_existing_request_id_header_is_reused():
    response = client.get(
        "/health",
        headers={REQUEST_ID_HEADER: "test-request-id"},
    )

    assert response.status_code == 200
    assert response.headers[REQUEST_ID_HEADER] == "test-request-id"


def test_slow_request_is_logged(caplog, monkeypatch):
    caplog.set_level(logging.WARNING)
    times = iter([100.0, 100.2])

    monkeypatch.setattr(request_id_middleware, "SLOW_REQUEST_THRESHOLD_MS", 1.0)
    monkeypatch.setattr(request_id_middleware, "get_current_time", lambda: next(times))

    response = client.get(
        "/health",
        headers={REQUEST_ID_HEADER: "slow-request-id"},
    )

    assert response.status_code == 200
    assert "slow_request" in caplog.text
    assert "/health" in caplog.text
    assert "slow-request-id" in caplog.text
    assert "threshold_ms=1.00" in caplog.text
