# Sistema de Comparacao de Similaridade Textual

Projeto base do TCC para comparar textos usando tres abordagens:
- TF-IDF + Similaridade de Cosseno
- Coeficiente de Jaccard
- Similaridade normalizada por Distancia de Levenshtein

Interface web incluida para colagem de textos e upload de arquivos `.txt`.
Pre-processamento com normalizacao, stopwords, lematizacao leve e stemming leve.

## Estrutura

- `src/algorithms`: implementacoes dos algoritmos
- `src/services`: orquestracao da comparacao
- `src/repositories`: camada de persistencia (SQLite)
- `src/api`: endpoints HTTP com Flask
- `tests`: testes unitarios e de API

## Requisitos

- Python 3.11+

## Como executar

```bash
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
python -m flask --app src.main run --debug
```

API disponivel em `http://127.0.0.1:5000`.

Persistencia padrao: `data/comparisons.db`.
Para alterar o caminho do banco, use a variavel `TCC_DB_PATH`.

## Endpoints

- `GET /`: interface web
- `GET /health`: status da aplicacao
- `POST /compare`: compara dois textos
- `POST /compare-files`: compara dois arquivos de texto
- `GET /history`: lista historico das comparacoes
- `GET /history/export.csv`: exporta historico em CSV
- `POST /evaluate`: avalia pares rotulados e calcula metricas (accuracy, precision, recall, f1)
- `POST /report/generate`: gera relatorio comparativo automatico entre os algoritmos

### Exemplo de requisicao

```json
{
  "text_a": "aprendizado de maquina",
  "text_b": "aprendizado de maquina supervisionado"
}
```

## Dataset base de experimento

- `data/datasets/base_pairs.json`: pares rotulados (`is_similar`) para validacao inicial.

## Geracao automatica de relatorio

Gerar relatorio markdown a partir do dataset base:

```bash
python -m scripts.generate_report
```

O arquivo sera salvo em `reports/`.

## Texto oficial do TCC

- `docs/TCC_ARTIGO_OFICIAL_MARCELO.md`: versao textual oficial consolidada do artigo, alinhada com a estrutura e escopo da ferramenta implementada.

## Roadmap tecnico

1. Expandir dataset com cenarios adicionais da area academica e juridica
2. Adicionar painel de analise comparativa com filtros por algoritmo e limiar
3. Incluir visualizacao de matriz de confusao no frontend
