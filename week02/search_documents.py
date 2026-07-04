from turtle import Turtle


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

print("搜索结果：")

found = False

for document in documents:
    if keyword in document["title"]:
        print("-", document["title"])
        found = True

if found == False:
    print("没有找到相关文档")