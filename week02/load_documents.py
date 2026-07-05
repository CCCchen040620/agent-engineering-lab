from week04.safe_json_loader import safe_load_json_list
from week04.settings import DOCUMENTS_JSON_PATH


def load_documents(file_path: str) -> list[dict]:
    return safe_load_json_list(file_path)


def main():
    documents = load_documents(DOCUMENTS_JSON_PATH)

    print("读取到", len(documents), "份文档")

    for document in documents:
        print("-", document["title"])


if __name__ == "__main__":
    main()