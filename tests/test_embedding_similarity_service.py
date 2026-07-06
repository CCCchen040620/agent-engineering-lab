import pytest

from backend.services.embedding_similarity_service import (
    cosine_similarity,
    dot_product,
    vector_length,
)


def test_embedding_dot_product():
    score = dot_product([1, 2, 3], [4, 5, 6])

    assert score == 32


def test_embedding_vector_length():
    length = vector_length([3, 4])

    assert length == 5


def test_embedding_cosine_similarity_same_direction():
    score = cosine_similarity([1, 1], [2, 2])

    assert score == pytest.approx(1)


def test_embedding_cosine_similarity_no_length():
    score = cosine_similarity([], [1, 2])

    assert score == 0