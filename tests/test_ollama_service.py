from urllib.error import URLError

from backend.services.ollama_service import try_generate_with_ollama


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


def test_try_generate_with_ollama_returns_fallback_when_failed(monkeypatch):
    def fake_urlopen(http_request, timeout):
        raise URLError("connection refused")

    monkeypatch.setattr(
        "backend.services.ollama_service.request.urlopen",
        fake_urlopen,
    )

    result = try_generate_with_ollama("你好")

    assert result["ok"] == False
    assert "本地模型暂时不可用" in result["response"]