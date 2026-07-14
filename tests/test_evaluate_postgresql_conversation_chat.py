from week10.evaluate_postgresql_conversation_chat import (
    evaluate_postgresql_conversation_chat_flow,
    has_postgresql_citation,
    response_uses_conversation_context,
)


class FakeResponse:
    def __init__(self, status_code, data):
        self.status_code = status_code
        self.data = data

    def json(self):
        return self.data


class FakeHttpClient:
    def __init__(self, post_responses, get_responses):
        self.post_responses = list(post_responses)
        self.get_responses = list(get_responses)
        self.posts = []
        self.gets = []

    def post(self, url, **kwargs):
        self.posts.append(
            {
                "url": url,
                **kwargs,
            }
        )

        return self.post_responses.pop(0)

    def get(self, url, **kwargs):
        self.gets.append(
            {
                "url": url,
                **kwargs,
            }
        )

        return self.get_responses.pop(0)


def build_chat_response(
    question: str,
    contextual_question: str,
    context_document_title: str,
    citations: list[dict],
) -> dict:
    return {
        "question": question,
        "intent": "answer_question",
        "keyword": question,
        "contextual_question": contextual_question,
        "context_document_title": context_document_title,
        "snippets": [],
        "has_valid_context": True,
        "answer": "员工每天需要完成 8 小时工作。",
        "citations": citations,
        "retriever_backend": "postgresql",
    }


def test_has_postgresql_citation():
    response = {
        "citations": [
            {
                "title": "员工手册",
                "text": "员工每天需要完成 8 小时工作。",
                "path": "postgresql://chunk/2",
            }
        ]
    }

    assert has_postgresql_citation(response) is True


def test_response_uses_conversation_context_from_title():
    response = {
        "context_document_title": "员工手册",
        "contextual_question": "员工手册 这份文档里员工每天需要工作多久？",
    }

    assert response_uses_conversation_context(response, "员工手册") is True


def test_evaluate_postgresql_conversation_chat_flow():
    citation = {
        "title": "员工手册",
        "text": "员工每天需要完成 8 小时工作。",
        "path": "postgresql://chunk/2",
    }
    fake_client = FakeHttpClient(
        post_responses=[
            FakeResponse(
                201,
                {
                    "id": 7,
                    "title": "PostgreSQL 会话检索验收",
                    "summary": "",
                },
            ),
            FakeResponse(
                200,
                build_chat_response(
                    question="员工每天需要工作多久？",
                    contextual_question="员工每天需要工作多久？",
                    context_document_title="",
                    citations=[citation],
                ),
            ),
            FakeResponse(
                200,
                build_chat_response(
                    question="这份文档里员工每天需要工作多久？",
                    contextual_question="员工手册 这份文档里员工每天需要工作多久？",
                    context_document_title="员工手册",
                    citations=[citation],
                ),
            ),
        ],
        get_responses=[
            FakeResponse(
                200,
                [
                    {
                        "id": 1,
                        "conversation_id": 7,
                        "role": "user",
                        "content": "员工每天需要工作多久？",
                    },
                    {
                        "id": 2,
                        "conversation_id": 7,
                        "role": "assistant",
                        "content": "员工每天需要完成 8 小时工作。",
                    },
                ],
            ),
            FakeResponse(
                200,
                [
                    {
                        "id": 1,
                        "conversation_id": 7,
                        "role": "user",
                        "content": "员工每天需要工作多久？",
                    },
                    {
                        "id": 2,
                        "conversation_id": 7,
                        "role": "assistant",
                        "content": "员工每天需要完成 8 小时工作。",
                    },
                    {
                        "id": 3,
                        "conversation_id": 7,
                        "role": "user",
                        "content": "这份文档里员工每天需要工作多久？",
                    },
                    {
                        "id": 4,
                        "conversation_id": 7,
                        "role": "assistant",
                        "content": "员工每天需要完成 8 小时工作。",
                    },
                ],
            ),
        ],
    )

    result = evaluate_postgresql_conversation_chat_flow(
        http_client=fake_client,
        base_url="http://127.0.0.1:8000/",
    )

    assert result["passed"] is True
    assert result["conversation_id"] == 7
    assert result["retriever_backend"] == "postgresql"
    assert result["expected_context_title"] == "员工手册"
    assert result["first_has_postgresql_citation"] is True
    assert result["first_messages_saved"] is True
    assert result["messages_after_first_count"] == 2
    assert result["second_used_conversation_context"] is True
    assert result["second_messages_saved"] is True
    assert result["messages_after_second_count"] == 4

    assert fake_client.posts[0]["url"] == "http://127.0.0.1:8000/api/v1/conversations"
    assert fake_client.posts[1]["params"]["retriever_backend"] == "postgresql"
    assert fake_client.posts[1]["params"]["mode"] == "precomputed_embedding"
    assert fake_client.posts[1]["params"]["min_score"] == 0.6
    assert fake_client.posts[2]["params"]["retriever_backend"] == "postgresql"
    assert fake_client.gets[0]["url"] == (
        "http://127.0.0.1:8000/api/v1/conversations/7/messages"
    )


def test_evaluate_postgresql_conversation_chat_flow_fails_without_pg_citation():
    fake_client = FakeHttpClient(
        post_responses=[
            FakeResponse(
                201,
                {
                    "id": 7,
                    "title": "PostgreSQL 会话检索验收",
                    "summary": "",
                },
            ),
            FakeResponse(
                200,
                build_chat_response(
                    question="员工每天需要工作多久？",
                    contextual_question="员工每天需要工作多久？",
                    context_document_title="",
                    citations=[],
                ),
            ),
            FakeResponse(
                200,
                build_chat_response(
                    question="这份文档里员工每天需要工作多久？",
                    contextual_question="这份文档里员工每天需要工作多久？",
                    context_document_title="",
                    citations=[],
                ),
            ),
        ],
        get_responses=[
            FakeResponse(
                200,
                [
                    {
                        "id": 1,
                        "conversation_id": 7,
                        "role": "user",
                        "content": "员工每天需要工作多久？",
                    },
                    {
                        "id": 2,
                        "conversation_id": 7,
                        "role": "assistant",
                        "content": "知识库中没有找到相关资料，暂时无法回答。",
                    },
                ],
            ),
            FakeResponse(
                200,
                [
                    {
                        "id": 1,
                        "conversation_id": 7,
                        "role": "user",
                        "content": "员工每天需要工作多久？",
                    },
                    {
                        "id": 2,
                        "conversation_id": 7,
                        "role": "assistant",
                        "content": "知识库中没有找到相关资料，暂时无法回答。",
                    },
                    {
                        "id": 3,
                        "conversation_id": 7,
                        "role": "user",
                        "content": "这份文档里员工每天需要工作多久？",
                    },
                    {
                        "id": 4,
                        "conversation_id": 7,
                        "role": "assistant",
                        "content": "知识库中没有找到相关资料，暂时无法回答。",
                    },
                ],
            ),
        ],
    )

    result = evaluate_postgresql_conversation_chat_flow(
        http_client=fake_client,
        base_url="http://127.0.0.1:8000",
    )

    assert result["passed"] is False
    assert result["failure_reason"] == "postgresql_conversation_chat_flow_failed"
    assert result["first_has_postgresql_citation"] is False
    assert result["second_used_conversation_context"] is False
