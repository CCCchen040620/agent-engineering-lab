from pathlib import Path


def test_docker_compose_defines_postgres_service():
    source = Path("docker-compose.yml").read_text(encoding="utf-8")

    assert "  postgres:" in source
    assert "pgvector/pgvector:pg16" in source
    assert "POSTGRES_USER" in source
    assert "POSTGRES_PASSWORD" in source
    assert "POSTGRES_DB" in source
    assert "postgres_data:/var/lib/postgresql/data" in source


def test_docker_compose_does_not_switch_backend_to_postgres_yet():
    source = Path("docker-compose.yml").read_text(encoding="utf-8")
    backend_section = source.split("  frontend:")[0]

    assert "DATABASE_URL: postgresql://" not in backend_section