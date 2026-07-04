from pathlib import Path

from week03.read_text_file import read_text_file


def load_text_documents(folder_path):
    documents = []

    folder = Path(folder_path)

    for file_path in folder.glob("*.txt"):
        content = read_text_file(file_path)

        document = {
            "title": file_path.stem,
            "path": str(file_path),
            "content": content,
        }

        documents.append(document)

    return documents


def main():
    documents = load_text_documents("data/company_docs")

    print("读取到", len(documents), "份文本文件")

    for document in documents:
        print("-", document["title"], document["path"])


if __name__ == "__main__":
    main()