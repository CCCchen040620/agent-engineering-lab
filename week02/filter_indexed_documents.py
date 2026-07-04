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

print("已完成索引的文档：")

for document in documents:
    if document["is_indexed"] == True:
        print("-", document["title"])
    else:
        print("-",document["title"],"还没有完成索引")