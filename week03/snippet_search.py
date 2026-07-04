from week03.load_text_documents import load_text_documents


def split_sentences(content):
    sentences = []

    for line in content.splitlines():
        line = line.strip()

        if line != "":
            sentences.append(line)

    return sentences


def search_snippets(documents, keyword):
    results = []

    for document in documents:
        sentences = split_sentences(document["content"])

        for sentence in sentences:
            if keyword in sentence:
                snippet = {
                    "title": document["title"],
                    "path": document["path"],
                    "text": sentence,
                }
                results.append(snippet)

    return results


def main():
    documents = load_text_documents("data/company_docs")
    keyword = input("请输入要搜索的内容关键词：")

    results = search_snippets(documents, keyword)

    print("搜索片段：")

    if len(results) == 0:
        print("没有找到相关片段")
    else:
        for snippet in results:
            print("-", snippet["title"], ":", snippet["text"])


if __name__ == "__main__":
    main()