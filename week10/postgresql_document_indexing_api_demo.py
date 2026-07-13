import requests


API_BASE_URL = "http://127.0.0.1:8001"


def main():
    create_response = requests.post(
        f"{API_BASE_URL}/api/v1/postgresql/documents/with-content",
        json={
            "title": "PostgreSQL API 入库验收文档",
            "file_type": "md",
            "content": (
                "员工参加外部培训需要提前提交申请。"
                "培训结束后需要提交学习总结。"
            ),
        },
        timeout=60,
    )

    print("创建状态码：", create_response.status_code)
    print("创建返回：")
    print(create_response.json())

    search_response = requests.post(
        f"{API_BASE_URL}/api/v1/postgresql/search/question",
        json={
            "question": "员工参加外部培训需要做什么？",
            "top_k": 3,
        },
        timeout=60,
    )

    print("检索状态码：", search_response.status_code)
    print("检索返回：")
    print(search_response.json())


if __name__ == "__main__":
    main()