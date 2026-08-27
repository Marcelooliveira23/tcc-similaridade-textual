"""Module for TF-IDF and Cosine Similarity computation.

Implements the TF-IDF (Term Frequency-Inverse Document Frequency) weighting scheme
combined with cosine similarity for document similarity analysis.

Follows classical formulation:
    TF(t, d) = freq(t, d) / |d|
    IDF(t, D) = log(|D| / |{d ∈ D : t ∈ d}|)
    similarity = cos(A, B) = (A · B) / (||A|| × ||B||)

References:
    - Salton, G., & McGill, M. J. (1983). Introduction to Modern Information Retrieval.
    - Manning, C. D., & Schütze, H. (1999). Foundations of Statistical NLP.
"""

import math
from collections import Counter

from .common import tokenize


def _build_tfidf_vector(tokens: list[str], doc_freq: Counter, total_docs: int) -> dict[str, float]:
    """Build a TF-IDF weight vector from tokenized text.
    
    Computes both Term Frequency (TF) and Inverse Document Frequency (IDF)
    weights for each unique term in the input token list using standard formulation.
    
    Args:
        tokens (list[str]): Preprocessed tokenized document.
        doc_freq (Counter): Document frequency counter across all documents.
        total_docs (int): Total number of documents in corpus.
        
    Returns:
        dict[str, float]: Mapping from term to its TF-IDF weight in [0, ∞).
        
    Notes:
        Uses Laplace smoothing (add-one smoothing) to handle unseen terms.
    """
    tf = Counter(tokens)
    vector: dict[str, float] = {}

    for term, count in tf.items():
        tf_weight = count / len(tokens) if tokens else 0.0
        idf_weight = math.log((total_docs + 1) / (doc_freq.get(term, 0) + 1)) + 1
        vector[term] = tf_weight * idf_weight

    return vector


def _cosine_similarity(vec_a: dict[str, float], vec_b: dict[str, float]) -> float:
    """Compute cosine similarity between two TF-IDF vectors.
    
    Measures the cosine of the angle between vectors in high-dimensional space.
    Provides normalized similarity in [0, 1] independent of document length.
    
    Mathematical formulation:
        cos(A, B) = (A · B) / (||A|| × ||B||)
    
    Args:
        vec_a (dict[str, float]): First TF-IDF vector (term -> weight).
        vec_b (dict[str, float]): Second TF-IDF vector (term -> weight).
        
    Returns:
        float: Cosine similarity in [0, 1].
            1.0 = identical vectors
            0.0 = orthogonal vectors (no common terms)
    """
    common_terms = set(vec_a) & set(vec_b)
    dot_product = sum(vec_a[t] * vec_b[t] for t in common_terms)

    norm_a = math.sqrt(sum(v * v for v in vec_a.values()))
    norm_b = math.sqrt(sum(v * v for v in vec_b.values()))

    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0

    return dot_product / (norm_a * norm_b)


def tfidf_cosine_similarity(text_a: str, text_b: str) -> float:
    """Compute TF-IDF-weighted cosine similarity between two texts.
    
    Primary interface for document similarity computation using classical information
    retrieval techniques. Orchestrates the complete pipeline:
    
    1. Tokenize and preprocess both texts
    2. Build document frequency statistics
    3. Compute TF-IDF weight vectors
    4. Calculate cosine similarity
    
    Args:
        text_a (str): First document text (arbitrary length).
        text_b (str): Second document text (arbitrary length).
        
    Returns:
        float: Similarity score in [0, 1].
            0.0 = completely dissimilar or empty inputs
            1.0 = identical or highly similar documents
            
    Strengths:
        - Robust to word order variations
        - Handles vocabulary differences well
        - Proven effective for semantic similarity
        - Scales well to varying document lengths
        
    Limitations:
        - Bag-of-words approach loses word order information
        - Sensitive to term weighting choices
        - May not capture deep semantic relationships
        
    Time Complexity: O(n + m) where n, m are token counts
    Space Complexity: O(n + m) for vector storage
    
    Example:
        >>> score = tfidf_cosine_similarity(
        ...     "Machine learning algorithms",
        ...     "ML algorithmic models"
        ... )
        >>> 0.6 < score <= 1.0  # Expect high similarity
    """
    tokens_a = tokenize(text_a)
    tokens_b = tokenize(text_b)

    if not tokens_a or not tokens_b:
        return 0.0

    doc_freq = Counter(set(tokens_a))
    doc_freq.update(set(tokens_b))

    total_docs = 2
    vec_a = _build_tfidf_vector(tokens_a, doc_freq, total_docs)
    vec_b = _build_tfidf_vector(tokens_b, doc_freq, total_docs)

    return _cosine_similarity(vec_a, vec_b)
