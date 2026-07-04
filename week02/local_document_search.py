from week02.load_documents import load_documents
from week02.search_service import format_document, search_documents


def main():
    documents = load_documents("data/documents.json")
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