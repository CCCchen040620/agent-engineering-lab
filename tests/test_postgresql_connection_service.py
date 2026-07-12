from backend.services.postgresql_connection_service import check_postgresql_connection


class FakeCursor:
    def execute(self, sql: str):
        self.sql = sql

    def fetchone(self):
        return (1,)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        pass


class FakeConnection:
    def cursor(self):
        return FakeCursor()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        pass


def test_check_postgresql_connection_returns_ok(monkeypatch):
    def fake_connect(database_url: str):
        return FakeConnection()

    monkeypatch.setattr(
        "backend.services.postgresql_connection_service.psycopg.connect",
        fake_connect,
    )

    result = check_postgresql_connection(
        "postgresql://agent:secret@localhost:5432/agent_db"
    )

    assert result["status"] == "ok"


def test_check_postgresql_connection_returns_error(monkeypatch):
    def fake_connect(database_url: str):
        raise RuntimeError("connection failed")

    monkeypatch.setattr(
        "backend.services.postgresql_connection_service.psycopg.connect",
        fake_connect,
    )

    result = check_postgresql_connection(
        "postgresql://agent:secret@localhost:5432/agent_db"
    )

    assert result["status"] == "error"
    assert "connection failed" in result["message"]