import logging

from fastapi.testclient import TestClient

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
