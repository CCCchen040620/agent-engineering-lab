from urllib.error import URLError

from backend.services.ollama_service import generate_with_ollama, try_generate_with_ollama


class FakeResponse:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        pass

    def read(self):
        return '{"response": "模型回答"}'.encode("utf-8")


def test_try_generate_with_ollama_returns_response(monkeypatch):
    def fake_urlopen(http_request, timeout):
        return FakeResponse()

    monkeypatch.setattr(
        "backend.services.ollama_service.request.urlopen",
        fake_urlopen,
    )

    result = try_generate_with_ollama("你好")

    assert result["ok"] == True
    assert result["response"] == "模型回答"


def test_generate_with_ollama_retries_once_and_returns_response(monkeypatch, caplog):
    call_count = {"value": 0}

    def fake_urlopen(http_request, timeout):
        call_count["value"] = call_count["value"] + 1

        if call_count["value"] == 1:
            raise URLError("temporary http 500")

        return FakeResponse()

    monkeypatch.setattr(
        "backend.services.ollama_service.request.urlopen",
        fake_urlopen,
    )

    result = generate_with_ollama("你好")

    assert result == "模型回答"
    assert call_count["value"] == 2
    assert "ollama_generation_retry" in caplog.text


def test_try_generate_with_ollama_returns_fallback_when_failed(monkeypatch):
    call_count = {"value": 0}

    def fake_urlopen(http_request, timeout):
        call_count["value"] = call_count["value"] + 1
        raise URLError("connection refused")

    monkeypatch.setattr(
        "backend.services.ollama_service.request.urlopen",
        fake_urlopen,
    )

    result = try_generate_with_ollama("你好")

    assert result["ok"] == False
    assert "本地模型暂时不可用" in result["response"]
    assert call_count["value"] == 2


def test_try_generate_with_ollama_logs_warning_when_failed(monkeypatch, caplog):
    def fake_urlopen(http_request, timeout):
        raise URLError("connection refused")

    monkeypatch.setattr(
        "backend.services.ollama_service.request.urlopen",
        fake_urlopen,
    )

    result = try_generate_with_ollama("你好", model="qwen3.6:latest")

    assert result["ok"] == False
    assert "ollama_generation_failed" in caplog.text
    assert "qwen3.6:latest" in caplog.text
