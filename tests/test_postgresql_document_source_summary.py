from backend.services.postgresql_document_repository import (
    summarize_document_sources_from_postgresql,
)


class FakeCursor:
    def __init__(self):
        self.sql = ""
        self.rows = []

    def execute(self, sql: str, params=None):
        self.sql = sql

    def fetchall(self):
        return self.rows

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        pass


class FakeConnection:
    def __init__(self):
        self.cursor_instance = FakeCursor()

    def cursor(self):
        return self.cursor_instance


def test_summarize_document_sources_from_postgresql():
    connection = FakeConnection()
    connection.cursor_instance.rows = [
        ("evaluation", 2),
        ("migration", 8),
        ("production", 5),
    ]

    summaries = summarize_document_sources_from_postgresql(connection)

    assert summaries == [
        {
            "source": "evaluation",
            "document_count": 2,
        },
        {
            "source": "migration",
            "document_count": 8,
        },
        {
            "source": "production",
            "document_count": 5,
        },
    ]
    assert "COALESCE(source, 'production')" in connection.cursor_instance.sql
    assert "COUNT(*) AS document_count" in connection.cursor_instance.sql
    assert "GROUP BY COALESCE(source, 'production')" in connection.cursor_instance.sql
    assert "ORDER BY source" in connection.cursor_instance.sql


def test_summarize_document_sources_from_postgresql_returns_empty_list():
    connection = FakeConnection()
    connection.cursor_instance.rows = []

    summaries = summarize_document_sources_from_postgresql(connection)

    assert summaries == []
