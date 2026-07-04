def filter_documents_by_type(documents, file_type):
    results = []

    for document in documents:
        # TODO: 如果 document 的 file_type 等于传入的 file_type，就加入 results
        if file_type in document["file_type"]:
            results.append(document)
        pass


    return results