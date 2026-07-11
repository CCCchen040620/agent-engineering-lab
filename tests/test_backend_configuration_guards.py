from pathlib import Path


def test_backend_does_not_use_legacy_sqlite_database_path():
    backend_files = Path("backend").rglob("*.py")

    matched_files = []

    for file_path in backend_files:
        source = file_path.read_text(encoding="utf-8")

        if "SQLITE_DATABASE_PATH" in source:
            matched_files.append(str(file_path))

    assert matched_files == []