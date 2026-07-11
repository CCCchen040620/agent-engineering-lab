from fastapi.testclient import TestClient

from backend.main import app
from backend.routers.db_documents import get_database_path
from backend.routers.rate_limit import get_heavy_request_rate_limiter
from backend.services.rate_limit_service import InMemoryRateLimiter


client = TestClient(app)


def test_heavy_endpoint_returns_429_when_rate_limited(tmp_path, caplog):
    database_path = tmp_path / "test.db"
    limiter = InMemoryRateLimiter(
        max_requests=1,
        window_seconds=60,
        time_provider=lambda: 100.0,
    )

    app.dependency_overrides[get_database_path] = lambda: str(database_path)
    app.dependency_overrides[get_heavy_request_rate_limiter] = lambda: limiter

    first_response = client.post(
        "/api/v1/db/chat/llm",
        json={"question": "公司有没有股票期权？"},
    )

    second_response = client.post(
        "/api/v1/db/chat/llm",
        json={"question": "公司有没有股票期权？"},
    )

    app.dependency_overrides.clear()

    assert first_response.status_code == 200
    assert second_response.status_code == 429
    assert second_response.json()["detail"] == "请求过于频繁，请稍后再试。"
    assert second_response.headers["Retry-After"] == "60"
    assert "rate_limit_exceeded" in caplog.text
    assert "/api/v1/db/chat/llm" in caplog.text
    assert "retry_after=60" in caplog.text
