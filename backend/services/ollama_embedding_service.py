import json
from urllib import request


def embed_with_ollama(
    text: str,
    model: str = "bge-m3:latest",
) -> list[float]:
    url = "http://localhost:11434/api/embed"

    body = {
        "model": model,
        "input": text,
    }

    data = json.dumps(body).encode("utf-8")

    http_request = request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )

    with request.urlopen(http_request, timeout=120) as response:
        response_text = response.read().decode("utf-8")

    result = json.loads(response_text)

    return result["embeddings"][0]