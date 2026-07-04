def search_documents(documents: list, keyword: str) -> list:
    results = []

    for document in documents:
        if keyword in document["title"] and document["is_indexed"]:
            results.append(document)

    return results

def format_document(document: dict) -> str:
    return (
        "- "
        + document["title"]
        + " | 类型: "
        + document["file_type"]
        + " | 切分块: "
        + str(document["chunk_count"])
    )


def main():
    documents = [
        {
            "title": "员工手册",
            "file_type": "md",
            "chunk_count": 12,
            "is_indexed": True,
        },
        {
            "title": "报销制度",
            "file_type": "pdf",
            "chunk_count": 8,
            "is_indexed": False,
        },
        {
            "title": "请假制度",
            "file_type": "md",
            "chunk_count": 5,
            "is_indexed": True,
        },
    ]

    keyword = input("请输入要搜索的关键词：")

    results = search_documents(documents, keyword)

    print("搜索结果：")

    if len(results) == 0:
        print("没有找到相关文档")
    else:
        for document in results:
            print(format_document(document))


if __name__ == "__main__":
    main()