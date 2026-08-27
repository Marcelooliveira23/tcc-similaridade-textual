"""Protótipo simples para comparação textual.

Este script oferece uma interface mínima para comparar dois textos com
TF-IDF+cosseno, Jaccard e Levenshtein, retornando percentuais e uma
interpretação qualitativa.
"""

from __future__ import annotations

import argparse
import json

from src.algorithms.jaccard import jaccard_similarity
from src.algorithms.levenshtein import normalized_levenshtein_similarity
from src.algorithms.tfidf_cosine import tfidf_cosine_similarity


def _to_percent(score: float) -> float:
    return round(score * 100.0, 1)


def _interpret(percent: float) -> str:
    if percent >= 70.0:
        return "alta"
    if percent >= 40.0:
        return "moderada"
    return "baixa"


def comparar_textos(texto_a: str, texto_b: str) -> dict:
    """Compara dois textos e retorna métricas em percentual."""
    tfidf = tfidf_cosine_similarity(texto_a, texto_b)
    jaccard = jaccard_similarity(texto_a, texto_b)
    levenshtein = normalized_levenshtein_similarity(texto_a, texto_b)

    resultado = {
        "tfidf_cosseno": _to_percent(tfidf),
        "jaccard": _to_percent(jaccard),
        "levenshtein": _to_percent(levenshtein),
    }

    media = round(sum(resultado.values()) / len(resultado), 1)
    resultado["media"] = media
    resultado["interpretacao"] = _interpret(media)
    return resultado


def main() -> None:
    parser = argparse.ArgumentParser(description="Protótipo de comparação textual")
    parser.add_argument("texto_a", help="Primeiro texto")
    parser.add_argument("texto_b", help="Segundo texto")
    args = parser.parse_args()

    resultado = comparar_textos(args.texto_a, args.texto_b)
    print(json.dumps(resultado, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
