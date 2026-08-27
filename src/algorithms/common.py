"""Common preprocessing utilities for text similarity algorithms.

This module provides a unified preprocessing pipeline applied consistently
across all similarity algorithms (TF-IDF, Jaccard, Levenshtein).

Pipeline stages:
    1. Normalize: decompose accents, lowercase, trim whitespace
    2. Tokenize: split into words using Unicode-aware regex
    3. Remove stopwords: filter common Portuguese/English words
    4. Lemmatize: reduce words to canonical forms
    5. Stem: apply suffix stripping rules

The preprocessing pipeline ensures that all algorithms work with consistently
prepared text, improving comparability of results across different methods.

References:
    - Unicode normalization: https://unicode.org/reports/tr15/
    - NLTK stopwords: https://www.nltk.org/
"""

import re
import unicodedata
from collections import Counter

TOKEN_PATTERN = re.compile(r"\w+", re.UNICODE)
STOPWORDS = {
    "a",
    "as",
    "ao",
    "aos",
    "de",
    "da",
    "das",
    "do",
    "dos",
    "e",
    "em",
    "na",
    "nas",
    "no",
    "nos",
    "o",
    "os",
    "para",
    "por",
    "que",
    "se",
    "um",
    "uma",
    "the",
    "and",
    "or",
    "of",
    "in",
    "to",
    "for",
    "with",
}

LEMMATIZATION_RULES = {
    "oes": "ao",
    "aes": "ao",
    "is": "il",
}

STEM_SUFFIXES = (
    "mente",
    "coes",
    "cao",
    "sao",
    "idades",
    "idade",
    "amentos",
    "imento",
    "adora",
    "ador",
    "logias",
    "logia",
    "istas",
    "ista",
    "icoes",
    "icao",
    "ing",
    "ed",
    "ly",
    "es",
    "s",
)


def normalize_text(text: str) -> str:
    """Normalize text by decomposing accents and converting to lowercase.
    
    Applies Unicode NFKD normalization to decompose combined characters
    (e.g., é → e + ´), removes combining marks, converts to lowercase,
    and strips leading/trailing whitespace.
    
    Args:
        text (str): Raw input text.
        
    Returns:
        str: Normalized text with no accents, lowercase, trimmed.
        
    Example:
        >>> normalize_text("  Café BRASIL  ")
        'cafe brasil'
    """
    normalized = unicodedata.normalize("NFKD", text)
    normalized = "".join(ch for ch in normalized if not unicodedata.combining(ch))
    return normalized.lower().strip()


def lemmatize_token(token: str) -> str:
    """Apply rule-based lemmatization to reduce word to base form.
    
    Uses simple suffix replacement rules for Portuguese word forms.
    Checks for minimum word length to avoid over-reducing short words.
    
    Args:
        token (str): Single word token (already normalized).
        
    Returns:
        str: Lemmatized form, or original token if no rule applies.
        
    Example:
        >>> lemmatize_token("casaroes")  # plural possessive
        'casarao'  # (not a real word, just demonstrates suffix replacement)
    """
    for suffix, replacement in LEMMATIZATION_RULES.items():
        if token.endswith(suffix) and len(token) > len(suffix) + 2:
            return token[: -len(suffix)] + replacement

    if token.endswith("s") and len(token) > 4:
        return token[:-1]

    return token


def stem_token(token: str) -> str:
    """Apply suffix-stripping stemming to reduce token to root form.
    
    Removes common Portuguese and English suffixes to normalize word forms.
    Checks minimum word length to prevent over-stemming.
    
    Suffix removal order matters: longer, more specific suffixes checked first.
    
    Args:
        token (str): Input token (already normalized).
        
    Returns:
        str: Stemmed form or original if no suffix matches.
        
    Example:
        >>> stem_token("computationally")
        'computional'
    """
    for suffix in STEM_SUFFIXES:
        if token.endswith(suffix) and len(token) > len(suffix) + 2:
            return token[: -len(suffix)]

    return token


def tokenize(
    text: str,
    remove_stopwords: bool = True,
    apply_lemmatization: bool = True,
    apply_stemming: bool = True,
) -> list[str]:
    """Complete preprocessing pipeline: normalize → tokenize → lemmatize → stem.
    
    Orchestrates full text preprocessing for use by similarity algorithms.
    Applies stages sequentially with optional flags for lemmatization and stemming.
    
    Pipeline stages:
        1. Normalize: accent decomposition, lowercase
        2. Tokenize: extract words via Unicode-aware regex
        3. Lemmatize: optional suffix-replacement rules (Portuguese)
        4. Stem: optional aggressive suffix stripping
        5. Stopword filter: remove common words
    
    Args:
        text (str): Raw input text.
        remove_stopwords (bool): Filter common words if True. Default True.
        apply_lemmatization (bool): Apply lemmatization rules. Default True.
        apply_stemming (bool): Apply stemming. Default True.
        
    Returns:
        list[str]: List of preprocessed tokens.
        
    Example:
        >>> tokenize("O machine learning é computacional")
        ['machine', 'learning', 'computacion']
        
    Note:
        The order of lemmatization before stemming is intentional:
        lemmatization uses minimal rules, then stemming handles edge cases.
    """
    tokens = TOKEN_PATTERN.findall(normalize_text(text))

    if apply_lemmatization:
        tokens = [lemmatize_token(token) for token in tokens]

    if apply_stemming:
        tokens = [stem_token(token) for token in tokens]

    if not remove_stopwords:
        return tokens

    return [token for token in tokens if token not in STOPWORDS]


def term_frequency(tokens: list[str]) -> Counter:
    """Compute term frequency counter from token list.
    
    Creates dictionary-like object mapping tokens to their occurrence counts.
    
    Args:
        tokens (list[str]): List of preprocessed tokens.
        
    Returns:
        Counter: Dictionary where keys are tokens, values are counts.
        
    Example:
        >>> tf = term_frequency(['cat', 'dog', 'cat'])
        >>> tf['cat']
        2
    """
    return Counter(tokens)
