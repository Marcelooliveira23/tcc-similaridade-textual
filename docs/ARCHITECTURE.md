# ARQUITETURA DO SISTEMA — DIAGRAMA E FLUXO

## 1. Diagrama da Arquitetura em Camadas

```
┌──────────────────────────────────────────────────────────────────────┐
│                    CAMADA DE APRESENTAÇÃO (Frontend)                 │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │  index.html                                                    │  │
│  │  ├─ Formulário de Colagem de Texto                            │  │
│  │  ├─ Upload de Arquivo (.txt)                                 │  │
│  │  └─ Visualização de Resultados (3 algoritmos lado a lado)    │  │
│  └────────────────────────────────────────────────────────────────┘  │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │  app.js - Lógica de Frontend                                  │  │
│  │  ├─ Fetch POST /api/compare (JSON)                           │  │
│  │  ├─ Fetch POST /api/compare/upload (FormData)               │  │
│  │  └─ Renderização de Resultados                              │  │
│  └────────────────────────────────────────────────────────────────┘  │
│                                                                       │
│  app.css - Estilos da Interface                                      │
└──────────────────────────────────────────────────────────────────────┘
                              ↕ HTTP/JSON
┌──────────────────────────────────────────────────────────────────────┐
│                     CAMADA DE API (Flask Routes)                     │
│                                                                       │
│  routes.py                                                           │
│  ├─ GET  /                          → Retorna index.html           │
│  ├─ POST /api/compare              → Compara dois textos (JSON)   │
│  ├─ POST /api/compare/upload       → Upload de dois arquivos      │
│  ├─ POST /api/evaluate             → Avalia contra dataset        │
│  ├─ POST /report/generate          → Gera relatório automático    │
│  ├─ GET  /api/history              → Retorna histórico            │
│  ├─ GET  /api/export/csv           → Exporta em CSV              │
│  └─ GET  /health                   → Health check                 │
└──────────────────────────────────────────────────────────────────────┘
                              ↕ (Orquestração)
┌──────────────────────────────────────────────────────────────────────┐
│                  CAMADA DE SERVIÇO (Business Logic)                  │
│                                                                       │
│  comparison_service.py                                              │
│  ├─ compare(text_a, text_b) → {tfidf, jaccard, levenshtein}       │
│  ├─ evaluate(dataset, algorithm) → {accuracy, precision, recall}   │
│  ├─ generate_report(dataset) → markdown com comparação             │
│  └─ preprocess_text(text) → tokens processados                     │
└──────────────────────────────────────────────────────────────────────┘
                    ↕              ↕              ↕
    ┌───────────────┴──────┬───────┴──────┬──────────────┘
    │                      │              │
┌───▼──────────┐  ┌────────▼──────┐  ┌───▼──────────────┐
│   ALGORITMO  │  │   ALGORITMO   │  │   ALGORITMO      │
│              │  │               │  │                  │
│  TF-IDF +    │  │    JACCARD    │  │   LEVENSHTEIN    │
│  COSSENO     │  │               │  │                  │
│              │  │ jaccard.py    │  │ levenshtein.py   │
│ tfidf_cosine.│  │               │  │                  │
│ py           │  │ • Tokenização │  │ • Distância de   │
│              │  │ • Conjuntos   │  │   edição         │
│ • TF         │  │ • Intersecção │  │ • Normalização   │
│ • IDF        │  │ • Fórmula J   │  │ • [0, 1]         │
│ • Vetor      │  │   = |A∩B| /   │  │                  │
│ • Cosseno    │  │     |A∪B|     │  │ levenshtein.py   │
│   = [0, 1]   │  │               │  │                  │
└───┬──────────┘  └────────┬──────┘  └───┬──────────────┘
    │                      │              │
    └──────────────┬───────┴──────┬───────┘
                   │              │
            common.py (Pré-processamento)
            ├─ normalize_text()
            ├─ tokenize()
            ├─ remove_stopwords()
            ├─ lemmatize()
            └─ stem()
                   │              │
                   ↓              ↓
            ┌──────────────────────────┐
            │  CAMADA DE PERSISTÊNCIA  │
            │    (Repositório)         │
            │                          │
            │  base.py                 │
            │  ├─ Interface (ABC)      │
            │  │                       │
            │  sqlite.py               │
            │  ├─ SQLiteRepository    │
            │  │  ├─ save()           │
            │  │  ├─ get_all()        │
            │  │  ├─ delete()         │
            │  │  └─ close()          │
            │                          │
            │  Banco de Dados         │
            │  data/comparisons.db    │
            │  (SQLite)               │
            └──────────────────────────┘
```

---

## 2. Fluxo de Execução — Caso de Uso: "Comparar Dois Textos"

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. USUÁRIO INSERE TEXTOS NA INTERFACE                          │
│    - Colagem manual em textarea                                │
│    - OU Upload de dois arquivos .txt                          │
└─────────────────────┬───────────────────────────────────────────┘
                      │
                      ↓
┌─────────────────────────────────────────────────────────────────┐
│ 2. app.js DETECTA SUBMISSÃO                                    │
│    - Coleta text_a e text_b                                   │
│    - Faz POST /api/compare (JSON) ou /api/compare/upload      │
└─────────────────────┬───────────────────────────────────────────┘
                      │
                      ↓
┌─────────────────────────────────────────────────────────────────┐
│ 3. Flask RECEBE REQUISIÇÃO                                    │
│    - Validação de entrada (comprimento, encoding)             │
│    - Chamada a comparison_service.compare(text_a, text_b)     │
└─────────────────────┬───────────────────────────────────────────┘
                      │
                      ↓
┌─────────────────────────────────────────────────────────────────┐
│ 4. COMPARISON_SERVICE ORQUESTRA                                │
│    - Chama preprocess(text_a) → tokens_a                      │
│    - Chama preprocess(text_b) → tokens_b                      │
│    - Para cada algoritmo:                                     │
│      ├─ result_tfidf = tfidf_cosine.compare(tokens_a, tokens_b) │
│      ├─ result_jaccard = jaccard.compare(tokens_a, tokens_b)    │
│      └─ result_levenshtein = levenshtein.compare(text_a, text_b)│
│    - Salva comparação no banco (via repository.save())         │
└─────────────────────┬───────────────────────────────────────────┘
                      │
         ┌────────────┼────────────┐
         ↓            ↓            ↓
    ┌─────────┐  ┌─────────┐  ┌─────────────┐
    │ TF-IDF  │  │ JACCARD │  │ LEVENSHTEIN │
    │ 1. Norm │  │ 1. Tok  │  │ 1. Compara  │
    │ 2. TF   │  │ 2. Set  │  │    caractere│
    │ 3. IDF  │  │ 3. |∩|  │  │ 2. Dist Min │
    │ 4. Vec  │  │ 4. |∪|  │  │ 3. Norma   │
    │ 5. Cos  │  │ 5. J=   │  │    [0,1]   │
    │ Score   │  │    ratio│  │ Score      │
    └────┬────┘  └────┬────┘  └────┬────────┘
         │            │            │
         └────────────┼────────────┘
                      │
                      ↓
┌─────────────────────────────────────────────────────────────────┐
│ 5. RESULTADO AGREGADO RETORNA AO FLASK                         │
│    {                                                            │
│      "text_a": "...",                                          │
│      "text_b": "...",                                          │
│      "results": {                                              │
│        "tfidf_cosine": 0.85,                                  │
│        "jaccard": 0.72,                                       │
│        "levenshtein": 0.68                                    │
│      },                                                         │
│      "timestamp": "2026-07-20T12:00:00Z",                    │
│      "comparison_id": "abc123"                               │
│    }                                                            │
└─────────────────────┬───────────────────────────────────────────┘
                      │
                      ↓
┌─────────────────────────────────────────────────────────────────┐
│ 6. BANCO SQLite PERSISTE RESULTADO                             │
│    INSERT INTO comparisons (text_a, text_b, results, ...)      │
└─────────────────────┬───────────────────────────────────────────┘
                      │
                      ↓
┌─────────────────────────────────────────────────────────────────┐
│ 7. JSON RESPONSE RETORNA AO FRONTEND (app.js)                 │
│    HTTP 200 OK + JSON acima                                   │
└─────────────────────┬───────────────────────────────────────────┘
                      │
                      ↓
┌─────────────────────────────────────────────────────────────────┐
│ 8. app.js RENDERIZA RESULTADOS NA INTERFACE                    │
│    - Exibe score de cada algoritmo                            │
│    - Código de cores (vermelho/amarelo/verde)                 │
│    - Interpretação (similar/moderado/dissimilar)              │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. Caso de Uso: "Gerar Relatório de Avaliação"

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. USUÁRIO CLICA "GERAR RELATÓRIO" OU                          │
│    EXECUTA: python scripts/generate_report.py                 │
└─────────────────────┬───────────────────────────────────────────┘
                      │
                      ↓
┌─────────────────────────────────────────────────────────────────┐
│ 2. SCRIPT CARREGA DATASET                                      │
│    data/datasets/base_pairs.json                               │
│    ├─ Lê 20+ pares com labels (similar/dissimilar)            │
│    └─ Estrutura: [{text_a, text_b, is_similar}, ...]          │
└─────────────────────┬───────────────────────────────────────────┘
                      │
                      ↓
┌─────────────────────────────────────────────────────────────────┐
│ 3. PARA CADA PAR + CADA ALGORITMO                              │
│    comparison_service.evaluate(dataset, algorithm)             │
│    ├─ Computa score de similaridade                           │
│    ├─ Aplica threshold (0.5)                                  │
│    ├─ Classifica como similar/dissimilar                      │
│    └─ Compara com label esperado                              │
│       ├─ TP (True Positive)                                   │
│       ├─ TN (True Negative)                                   │
│       ├─ FP (False Positive)                                  │
│       └─ FN (False Negative)                                  │
└─────────────────────┬───────────────────────────────────────────┘
                      │
                      ↓
┌─────────────────────────────────────────────────────────────────┐
│ 4. CALCULA MÉTRICAS PARA CADA ALGORITMO                        │
│                                                                 │
│    ┌─────────────────┐  ┌──────────────┐  ┌─────────────────┐ │
│    │  TF-IDF+Cosine  │  │   Jaccard    │  │  Levenshtein    │ │
│    ├─────────────────┤  ├──────────────┤  ├─────────────────┤ │
│    │ Accuracy: 0.85  │  │ Accuracy:0.72│  │ Accuracy: 0.68  │ │
│    │ Precision: 0.88 │  │ Precision:0.75│ │ Precision: 0.72 │ │
│    │ Recall: 0.82    │  │ Recall: 0.68 │  │ Recall: 0.64    │ │
│    │ F1: 0.85        │  │ F1: 0.71     │  │ F1: 0.68        │ │
│    └─────────────────┘  └──────────────┘  └─────────────────┘ │
│                                                                 │
│    Ranking por F1:                                             │
│    1. TF-IDF+Cosine (0.85) ⭐ Melhor para semântica            │
│    2. Jaccard (0.71) — Bom para conjuntos                      │
│    3. Levenshtein (0.68) — Melhor para typos                   │
└─────────────────────┬───────────────────────────────────────────┘
                      │
                      ↓
┌─────────────────────────────────────────────────────────────────┐
│ 5. GERA RELATÓRIO EM MARKDOWN                                  │
│    reports/similarity_report_<timestamp>.md                    │
│    ├─ Cabeçalho com data e configuração                       │
│    ├─ Tabela de Métricas (Acc, Prec, Rec, F1)                │
│    ├─ Análise por Cenário                                     │
│    │  ├─ Textos idênticos                                     │
│    │  ├─ Typos leves                                          │
│    │  ├─ Paráfrase                                            │
│    │  └─ Completamente diferentes                             │
│    ├─ Recomendações                                           │
│    │  ├─ Quando usar TF-IDF                                   │
│    │  ├─ Quando usar Jaccard                                  │
│    │  └─ Quando usar Levenshtein                              │
│    └─ Conclusão                                               │
└─────────────────────┬───────────────────────────────────────────┘
                      │
                      ↓
┌─────────────────────────────────────────────────────────────────┐
│ 6. RELATÓRIO SALVO E PRONTO PARA TCC                           │
│    └─ Pode ser incorporado direto na seção "Resultados"       │
└─────────────────────────────────────────────────────────────────┘
```

---

## 4. Mapa de Dependências

```
main.py (entry point)
├─ Flask app
├─ CORS
└─ routes.py
   ├─ comparison_service.py
   │  ├─ algorithms/tfidf_cosine.py
   │  │  └─ common.py (preprocess)
   │  ├─ algorithms/jaccard.py
   │  │  └─ common.py (preprocess)
   │  ├─ algorithms/levenshtein.py
   │  │  └─ common.py (preprocess)
   │  ├─ repositories/sqlite.py
   │  │  ├─ models/comparison.py
   │  │  └─ sqlite3 (stdlib)
   │  └─ json (stdlib)
   ├─ os, json (stdlib)
   └─ werkzeug.utils (secure_filename)

common.py
├─ nltk (stopwords, stemming)
├─ unicodedata
├─ re (regex)
└─ string

tests/test_api.py
├─ pytest
├─ src.main (app)
└─ json

tests/test_algorithms.py
├─ pytest
├─ src.algorithms.*
└─ src.algorithms.common

scripts/generate_report.py
├─ src.services.comparison_service
├─ src.repositories.sqlite
├─ json
├─ datetime
└─ os
```

---

## 5. Padrões de Projeto Utilizados

### 5.1 Repository Pattern
**Objetivo:** Abstrair persistência e permitir trocar banco sem alterar serviço.

```python
# Interface (base.py)
class BaseRepository(ABC):
    @abstractmethod
    def save(self, comparison): pass
    
    @abstractmethod
    def get_all(self): pass

# Implementação SQLite (sqlite.py)
class SQLiteRepository(BaseRepository):
    def save(self, comparison):
        # Insere em BD
        pass
    
    def get_all(self):
        # Retorna da BD
        pass

# Uso no serviço
repo = SQLiteRepository()
repo.save(comparison_result)
```

### 5.2 Strategy Pattern
**Objetivo:** Permitir trocar algoritmo de similaridade sem alterar código chamador.

```python
# Cada algoritmo é uma "strategy"
tfidf_algo = TFIDFCosine()
jaccard_algo = Jaccard()
levenshtein_algo = Levenshtein()

# Interface uniforme
score_tfidf = tfidf_algo.compare(text_a, text_b)
score_jaccard = jaccard_algo.compare(text_a, text_b)

# Adicionar novo algoritmo é só implementar a interface
```

### 5.3 Decorator Pattern
**Objetivo:** Aplicar pré-processamento sem acumular lógica em cada algoritmo.

```python
# Pré-processamento é aplicado uma vez, reutilizado por todos
tokens_a = preprocess_text(text_a)
tokens_b = preprocess_text(text_b)

# Cada algoritmo recebe tokens já processados
score = algorithm.compare(tokens_a, tokens_b)
```

---

## 6. Decisões de Design e Justificativas

| Decisão | Justificativa | Trade-offs |
|---------|--------------|-----------|
| **SQLite ao invés de In-Memory** | Persistência entre execuções; pronto para produção | Overhead de I/O leve |
| **Pré-processamento centralizado** | DRY; consistência; fácil evolução | Menos flexibilidade por algoritmo |
| **Arquitetura em camadas** | Separação de responsabilidades; testabilidade | Mais arquivos, menos concisão |
| **Frontend vanilla (HTML/CSS/JS)** | Sem dependências de build; deploy simples | UI menos polida que React/Vue |
| **Normalização em [0,1]** | Comparabilidade entre algoritmos | Perda de informação da distância bruta |
| **Threshold 0.5 fixo** | Simplicidade; caso médio | Não ótimo para todos os cenários |

---

## Conclusão

A arquitetura em camadas com padrões de design facilita:
- ✅ Extensão futura (novos algoritmos, novos repositórios)
- ✅ Testabilidade (cada camada isolável)
- ✅ Manutenibilidade (responsabilidades claras)
- ✅ Documentação (fluxos explícitos)

