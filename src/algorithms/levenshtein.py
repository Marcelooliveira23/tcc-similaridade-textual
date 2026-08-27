"""Module for Levenshtein Distance (Edit Distance) computation.

Implements the Levenshtein distance algorithm using space-optimized
dynamic programming. Measures minimum single-character edits (insert,
delete, substitute) needed to transform one string into another.

References:
    - Levenshtein, V. I. (1966). Binary codes capable of correcting deletions.
    - Wagner, R. A., & Fischer, M. J. (1974). The string-to-string correction problem.
"""


def levenshtein_distance(text_a: str, text_b: str) -> int:
    """Compute Levenshtein (edit) distance between two strings.
    
    Uses space-optimized Wagner-Fischer algorithm requiring only O(m) space
    instead of O(m×n) by storing only two rows of DP table at a time.
    
    Args:
        text_a (str): First string.
        text_b (str): Second string.
        
    Returns:
        int: Minimum edit distance (number of operations).
            0 = strings identical
            1 = single character difference
            
    Algorithm:
        - Optimal substructure: ED(a,b) = min of:
            * ED(a[:-1], b) + 1 (deletion)
            * ED(a, b[:-1]) + 1 (insertion)
            * ED(a[:-1], b[:-1]) + cost (substitution)
        - Space optimization: keep only previous and current row
        
    Time Complexity: O(m × n) where m = len(text_a), n = len(text_b)
    Space Complexity: O(min(m, n)) - space optimized version
    
    Strengths:
        - Character-level precision for typo detection
        - Proven effectiveness in spell-checking
        - Handles OCR errors well
        
    Limitations:
        - Considers transposition as 2 operations (insert + delete)
        - Character-level only (no semantic awareness)
        - O(n²) time for moderate-length strings
        
    Example:
        >>> levenshtein_distance("kitten", "sitting")
        3  # kitten → sitten → sittin → sitting
    """
    if text_a == text_b:
        return 0

    if not text_a:
        return len(text_b)

    if not text_b:
        return len(text_a)

    previous_row = list(range(len(text_b) + 1))

    for i, char_a in enumerate(text_a, start=1):
        current_row = [i]

        for j, char_b in enumerate(text_b, start=1):
            insertions = previous_row[j] + 1
            deletions = current_row[j - 1] + 1
            substitutions = previous_row[j - 1] + (char_a != char_b)
            current_row.append(min(insertions, deletions, substitutions))

        previous_row = current_row

    return previous_row[-1]


def normalized_levenshtein_similarity(text_a: str, text_b: str) -> float:
    """Compute normalized Levenshtein similarity in [0, 1].
    
    Converts raw Levenshtein distance to similarity metric normalized by
    maximum possible distance (length of longer string).
    
    Formula:
        similarity = 1 - (distance / max(len(a), len(b)))
        
    Args:
        text_a (str): First string.
        text_b (str): Second string.
        
    Returns:
        float: Normalized similarity in [0, 1].
            1.0 = identical strings
            0.5 = strings differ by ~50% of max length
            0.0 = strings completely different
            
    Normalization ensures:
        - Invariance to absolute string length
        - Comparable scores across different string pairs
        - Intuitive interpretation (higher = more similar)
    
    Example:
        >>> normalized_levenshtein_similarity("cat", "cat")
        1.0
        >>> normalized_levenshtein_similarity("cat", "hat")
        0.6667  # distance=1, max_len=3, similarity=1-1/3
    """
    max_len = max(len(text_a), len(text_b))
    if max_len == 0:
        return 1.0

    distance = levenshtein_distance(text_a, text_b)
    return 1 - (distance / max_len)
