from week05.models import ChatResponse, Citation
from week07.evaluate_llm_rag import build_markdown_report, save_markdown_report


def test_build_markdown_report():
    responses = [
        ChatResponse(
            question="新员工什么时候完成安全培训？",
            keyword="安全培训",
            answer="新员工需要在 30 天内完成安全培训。",
            citations=[
                Citation(
                    title="员工手册",
                    text="新员工入职后需要在 30 天内完成安全培训。",
                    path="sqlite://1",
                )
            ],
        )
    ]

    markdown = build_markdown_report(responses)

    assert "# LLM RAG 自动评测报告" in markdown
    assert "新员工什么时候完成安全培训？" in markdown
    assert "员工手册" in markdown


def test_save_markdown_report(tmp_path):
    file_path = tmp_path / "report.md"

    save_markdown_report("# 测试报告", str(file_path))

    assert file_path.read_text(encoding="utf-8") == "# 测试报告"