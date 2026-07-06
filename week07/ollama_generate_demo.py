from backend.services.ollama_service import generate_with_ollama


def main():
    answer = generate_with_ollama("请用一句中文解释什么是 RAG。")

    print(answer)


if __name__ == "__main__":
    main()