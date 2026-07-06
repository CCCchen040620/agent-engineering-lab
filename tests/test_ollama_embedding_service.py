from backend.services.ollama_embedding_service import embed_with_ollama


class FakeResponse:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        pass

    def read(self):
        return '{"embeddings": [[0.1, 0.2, 0.3]]}'.encode("utf-8")


def test_embed_with_ollama(monkeypatch):
    def fake_urlopen(http_request, timeout):
        return FakeResponse()

    monkeypatch.setattr(
        "backend.services.ollama_embedding_service.request.urlopen",
        fake_urlopen,
    )

    embedding = embed_with_ollama("员工每周可以申请一天远程办公。")

    assert embedding == [0.1, 0.2, 0.3]