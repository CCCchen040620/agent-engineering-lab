from week03.load_text_documents import load_text_documents


def search_by_content(documents, keyword):
    results = []

    for document in documents:
        if keyword in document["content"]:
            results.append(document)

    return results


def main():
    documents = load_text_documents("data/company_docs")
    keyword = input("请输入要搜索的内容关键词：")

    results = search_by_content(documents, keyword)

    print("搜索结果：")

    if len(results) == 0:
        print("没有找到相关文档")
    else:
        for document in results:
            print("-", document["title"])


if __name__ == "__main__":
    main()