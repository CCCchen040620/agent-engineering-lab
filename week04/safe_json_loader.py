import json
from pathlib import Path


def safe_load_json_list(file_path: str) -> list[dict]:
    path = Path(file_path)

    if not path.exists():
        return []

    try:
        with open(path, "r", encoding="utf-8") as file:
            data = json.load(file)

        if isinstance(data, list):
            return data

        return []
    except json.JSONDecodeError:
        return []


def main():
    documents = safe_load_json_list("data/documents.json")

    print("读取到", len(documents), "条数据")


if __name__ == "__main__":
    main()