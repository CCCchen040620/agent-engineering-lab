import json

from week02.load_documents import load_documents


def save_documents(file_path, documents):
    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(documents, file, ensure_ascii=False, indent=2)


def build_document(title, file_type, chunk_count, is_indexed):
    if title == "":
        raise ValueError("文档标题不能为空。")

    if chunk_count < 0:
        raise ValueError("切分块数量不能小于0。")

    return {
        "title": title,
        "file_type": file_type,
        "chunk_count": chunk_count,
        "is_indexed": is_indexed,
    }


def parse_is_indexed(text):
    if text == "yes":
        return True

    if text == "no":
        return False

    raise ValueError("是否已索引只能输入 yes 或 no。")


def main():
    file_path = "data/documents.json"

    title = input("请输入文档标题：")
    file_type = input("请输入文件类型：")
    chunk_count = input("请输入切分块数量：")
    is_indexed_text = input("是否已索引？请输入 yes 或 no：")

    try:
        chunk_count_number = int(chunk_count)
        is_indexed = parse_is_indexed(is_indexed_text)

        documents = load_documents(file_path)
        new_document = build_document(title, file_type, chunk_count_number, is_indexed)
        documents.append(new_document)
        save_documents(file_path, documents)

        print("文档已保存：", title)
    except ValueError as error:
        print(error)


if __name__ == "__main__":
    main()