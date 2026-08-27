"""Module for Jaccard Index (Jaccard Similarity Coefficient) computation.

Implements the Jaccard similarity coefficient, a fundamental set-based similarity
measure widely used in text comparison, document clustering, and near-duplicate
detection.

The Jaccard index is defined as:
    J(A, B) = |A ∩ B| / |A ∪ B|

References:
    - Jaccard, P. (1901). Étude comparative de la distribution florale.
    - Wikipedia: https://en.wikipedia.org/wiki/Jaccard_index
    - Tan, P. N., Steinbach, M., & Kumar, V. (2005). Introduction to Data Mining.
"""

from .common import tokenize


def jaccard_similarity(text_a: str, text_b: str) -> float:
    """Compute Jaccard similarity coefficient between two texts.
    
    Measures set similarity as the ratio of intersection to union of token sets.
    Provides symmetric, intuitive similarity metric in [0, 1].
    
    Algorithm:
        J(A, B) = |A ∩ B| / |A ∪ B|
        
    Args:
        text_a (str): First document text.
        text_b (str): Second document text.
        
    Returns:
        float: Jaccard coefficient in [0, 1].
            1.0 = identical token sets
            0.5 = 50% vocabulary overlap
            0.0 = completely disjoint token sets
            
    Properties:
        - Symmetric: J(A, B) = J(B, A)
        - Normalized: always in [0, 1]
        - Independent of token frequency (uses sets, not counters)
        - Sensitive only to vocabulary presence/absence
        
    Strengths:
        - Intuitive interpretation
        - Efficient for near-duplicate detection
        - Good for deduplication tasks
        - Works well with short texts
        
    Limitations:
        - Ignores token frequency (rare and common words weighted equally)
        - Loses word order completely
        - Poor for semantic similarity (no IDF weighting)
        
    Example:
        >>> score = jaccard_similarity("cat dog", "cat dog bird")
        >>> score == 2/3  # {cat, dog} ∩ {cat, dog, bird} = {cat, dog}
        True
        
    Time Complexity: O(n + m) where n, m are token counts
    Space Complexity: O(n + m) for set storage
    """
    tokens_a = set(tokenize(text_a))
    tokens_b = set(tokenize(text_b))

    if not tokens_a and not tokens_b:
        return 1.0

    union = tokens_a | tokens_b
    if not union:
        return 0.0

    intersection = tokens_a & tokens_b
    return len(intersection) / len(union)
