def build_rag_prompt(question: str, snippets: list[dict]) -> str:
    context_lines = []

    for index, snippet in enumerate(snippets, start=1):
        context_lines.append(f"[{index}] {snippet['text']}")

    context = "\n".join(context_lines)

    return f"""你是一个企业知识库助手。

请严格根据【知识库资料】回答用户问题。
如果资料中没有答案，请回答：知识库中没有找到相关资料，暂时无法回答。
回答时请使用中文。

【知识库资料】
{context}

【用户问题】
{question}

【回答】
"""