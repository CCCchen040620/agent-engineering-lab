from urllib.parse import urlparse


def parse_database_url(database_url: str) -> dict:
    parsed_url = urlparse(database_url)

    if parsed_url.scheme == "sqlite":
        return {
            "scheme": "sqlite",
            "path": parsed_url.path.lstrip("/"),
        }

    if parsed_url.scheme in ["postgresql", "postgres"]:
        return {
            "scheme": "postgresql",
            "username": parsed_url.username or "",
            "password": parsed_url.password or "",
            "host": parsed_url.hostname or "",
            "port": parsed_url.port,
            "database": parsed_url.path.lstrip("/"),
        }

    raise ValueError(f"Unsupported database scheme: {parsed_url.scheme}")


def is_sqlite_database(database_url: str) -> bool:
    return parse_database_url(database_url)["scheme"] == "sqlite"


def is_postgresql_database(database_url: str) -> bool:
    return parse_database_url(database_url)["scheme"] == "postgresql"
