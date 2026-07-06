import math


def dot_product(first_vector: list[float], second_vector: list[float]) -> float:
    score = 0.0

    for first_value, second_value in zip(first_vector, second_vector):
        score = score + first_value * second_value

    return score


def vector_length(vector: list[float]) -> float:
    total = 0.0

    for value in vector:
        total = total + value * value

    return math.sqrt(total)


def cosine_similarity(first_vector: list[float], second_vector: list[float]) -> float:
    first_length = vector_length(first_vector)
    second_length = vector_length(second_vector)

    if first_length == 0 or second_length == 0:
        return 0

    return dot_product(first_vector, second_vector) / (first_length * second_length)