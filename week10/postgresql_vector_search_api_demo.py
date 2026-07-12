import requests

from backend.config import BACKEND_API_BASE_URL


def build_fake_embedding(first_value: float, size: int = 1024) -> list[float]:
    embedding = [0.0] * size
    embedding[0] = first_value

    return embedding


def main() -> None:
    url = f"{BACKEND_API_BASE_URL}/api/v1/postgresql/search/vector"

    response = requests.post(
        url,
        json={
            "embedding": build_fake_embedding(1.0),
            "top_k": 2,
        },
        timeout=30,
    )

    print("状态码：", response.status_code)
    print("返回结果：")
    print(response.json())


if __name__ == "__main__":
    main()