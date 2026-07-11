from fastapi.testclient import TestClient

from backend.main import app
from backend.request_id_middleware import REQUEST_ID_HEADER


client = TestClient(app)


def test_http_error_response_has_unified_shape():
    response = client.get(
        "/api/v1/documents/不存在的文档",
        headers={REQUEST_ID_HEADER: "not-found-request"},
    )

    data = response.json()

    assert response.status_code == 404
    assert data["detail"] == "文档不存在。"
    assert data["error"] == {
        "code": "not_found",
        "message": "文档不存在。",
        "status_code": 404,
    }
    assert data["request_id"] == "not-found-request"
    assert response.headers[REQUEST_ID_HEADER] == "not-found-request"


def test_validation_error_response_has_unified_shape():
    response = client.post(
        "/api/v1/chat",
        json={"question": ""},
        headers={REQUEST_ID_HEADER: "validation-request"},
    )

    data = response.json()

    assert response.status_code == 422
    assert isinstance(data["detail"], list)
    assert data["error"] == {
        "code": "validation_error",
        "message": "请求参数校验失败。",
        "status_code": 422,
    }
    assert data["request_id"] == "validation-request"
