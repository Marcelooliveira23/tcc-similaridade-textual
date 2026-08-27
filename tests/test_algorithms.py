from src.algorithms.jaccard import jaccard_similarity
from src.algorithms.levenshtein import levenshtein_distance, normalized_levenshtein_similarity
from src.algorithms.tfidf_cosine import tfidf_cosine_similarity


def test_jaccard_similarity_identical_texts():
    assert jaccard_similarity("texto exemplo", "texto exemplo") == 1.0


def test_levenshtein_distance_known_case():
    assert levenshtein_distance("kitten", "sitting") == 3


def test_normalized_levenshtein_similarity_range():
    score = normalized_levenshtein_similarity("casa", "caso")
    assert 0.0 <= score <= 1.0


def test_tfidf_cosine_similarity_identical_texts():
    score = tfidf_cosine_similarity("aprendizado de maquina", "aprendizado de maquina")
    assert score > 0.99


def test_tfidf_cosine_similarity_different_texts():
    score = tfidf_cosine_similarity("banana manga", "carro aviao")
    assert score == 0.0
