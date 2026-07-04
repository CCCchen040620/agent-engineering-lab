import json


def load_documents(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        documents = json.load(file)

    return documents


def main():
    documents = load_documents("data/documents.json")

    print("读取到", len(documents), "份文档")

    for document in documents:
        print("-", document["title"])


if __name__ == "__main__":
    main()