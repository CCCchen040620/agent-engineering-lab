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

for document in documents:
    print("标题：", document["title"])
    print("类型：", document["file_type"])
    print("切分块：", document["chunk_count"])
    print("已索引：", document["is_indexed"])
    print("-----")