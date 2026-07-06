import sys

import time

from backend.services.sqlite_precomputed_embedding_search_service import (
    search_sqlite_chunks_by_precomputed_embedding,
)
from backend.services.ranking_service import rank_chunks
from backend.services.sqlite_document_repository import (
    create_chunks_table,
    create_connection,
    create_documents_table,
    search_chunks_with_document_by_text,
)
from backend.services.sqlite_embedding_search_service import (
    search_sqlite_chunks_by_embedding,
)
from backend.services.sqlite_vector_search_service import (
    search_sqlite_chunks_by_similarity,
)
from week03.keyword_extractor import extract_keyword
from week04.settings import SQLITE_DATABASE_PATH


def measure_time(function):
    start_time = time.perf_counter()

    result = function()

    end_time = time.perf_counter()

    return result, end_time - start_time


def print_result(mode: str, results: list[dict]):
    print("=" * 60)
    print("检索模式：", mode)
    print("=" * 60)

    if results == []:
        print("没有检索到结果")
        return

    for index, result in enumerate(results, start=1):
        print(f"[{index}] 来源：{result['title']}")
        print("片段：", result["text"])

        if "score" in result:
            print("分数：", result["score"])

        print()


def search_by_keyword(question: str, top_k: int = 3) -> list[dict]:
    keyword = extract_keyword(question)

    connection = create_connection(SQLITE_DATABASE_PATH)

    create_documents_table(connection)
    create_chunks_table(connection)

    chunk_results = search_chunks_with_document_by_text(connection, keyword)
    chunk_results = rank_chunks(chunk_results, keyword)

    connection.close()

    results = []

    for chunk in chunk_results[:top_k]:
        results.append(
            {
                "title": chunk["document_title"],
                "text": chunk["text"],
                "score": chunk["score"],
            }
        )

    return results


def compare_retrieval_modes(
    question: str,
    top_k: int = 3,
    min_score: float = 0.0,
):
    keyword_results, keyword_duration = measure_time(
        lambda: search_by_keyword(question, top_k=top_k)
    )

    vector_results, vector_duration = measure_time(
        lambda: search_sqlite_chunks_by_similarity(
            database_path=SQLITE_DATABASE_PATH,
            query=question,
            top_k=top_k,
            min_score=min_score,
        )
    )

    embedding_results, embedding_duration = measure_time(
        lambda: search_sqlite_chunks_by_embedding(
            database_path=SQLITE_DATABASE_PATH,
            query=question,
            top_k=top_k,
        )
    )

    embedding_results = [
        result for result in embedding_results
        if result["score"] >= min_score
    ]

    precomputed_embedding_results, precomputed_embedding_duration = measure_time(
        lambda: search_sqlite_chunks_by_precomputed_embedding(
            database_path=SQLITE_DATABASE_PATH,
            query=question,
            top_k=top_k,
        )
    )

    precomputed_embedding_results = [
        result for result in precomputed_embedding_results
        if result["score"] >= min_score
    ]

    print("问题：", question)
    print("提取关键词：", extract_keyword(question))
    print("最低分数：", min_score)
    print()

    print_result(
        f"keyword ({keyword_duration:.3f}s, {len(keyword_results)} results)",
        keyword_results,
    )
    print_result(
        f"vector ({vector_duration:.3f}s, {len(vector_results)} results)",
        vector_results,
    )
    print_result(
        f"embedding ({embedding_duration:.3f}s, {len(embedding_results)} results)",
        embedding_results,
    )
    print_result(
        f"precomputed_embedding ({precomputed_embedding_duration:.3f}s, {len(precomputed_embedding_results)} results)",
        precomputed_embedding_results,
    )


def main():
    if len(sys.argv) >= 2:
        question = sys.argv[1]
    else:
        question = "主管审批后什么时候生效？"

    if len(sys.argv) >= 3:
        min_score = float(sys.argv[2])
    else:
        min_score = 0.0

    compare_retrieval_modes(
        question,
        top_k=3,
        min_score=min_score,
    )


if __name__ == "__main__":
    main()