# SISTEMA DE COMPARAÇÃO DE SIMILARIDADE TEXTUAL: UMA ANÁLISE COMPARATIVA DE ALGORITMOS

**Aluno:** [Seu Nome]  
**Orientador:** [Nome do Orientador]  
**Instituição:** [Nome da Instituição]  
**Curso:** Engenharia de Software  
**Data de Entrega:** [Data]  

---

## SUMÁRIO

1. [Introdução](#1-introdução)
2. [Referencial Teórico](#2-referencial-teórico)
   - 2.1 Similaridade Textual e Aplicações
   - 2.2 TF-IDF e Similaridade de Cosseno
   - 2.3 Coeficiente de Jaccard
   - 2.4 Distância de Levenshtein
   - 2.5 Processamento de Linguagem Natural
3. [Metodologia](#3-metodologia)
4. [Implementação](#4-implementação)
5. [Resultados Preliminares](#5-resultados-preliminares)
6. [Conclusão](#6-conclusão)
7. [Referências](#7-referências)

---

## 1. INTRODUÇÃO

### 1.1 Problemática

A detecção e quantificação de similaridade entre textos é um problema fundamental em diversas áreas da Ciência da Computação, incluindo recuperação de informação, detecção de plágio, deduplicação de conteúdo e análise de similaridade documentar. A crescente volume de dados textuais gerados diariamente—em redes sociais, bases de dados acadêmicas, arquivos corporativos—torna a automatização dessa tarefa crítica para eficiência operacional.

Entretanto, diferentes contextos de aplicação demandam diferentes abordagens. Enquanto alguns cenários exigem precisão na comparação de palavras-chave (detectar plágio acadêmico), outros requerem robustez a pequenas variações ortográficas (matching de nomes em sistemas de registro). Não existe um algoritmo única que seja ótimo para todos os casos.

**Questão central de pesquisa:** Qual é o desempenho comparativo de três algoritmos de similaridade textual (TF-IDF com Cosseno, Jaccard e Levenshtein) em cenários reais de comparação, e em quais contextos cada um se destaca?

### 1.2 Justificativa

1. **Relevância acadêmica:** O estudo comparativo de algoritmos de similaridade textual contribui para a formação de engenheiros de software capazes de escolher a ferramenta correta para cada problema.

2. **Aplicabilidade prática:** As conclusões podem informar decisões de arquitetura em sistemas reais que necessitam de busca, deduplicação ou análise de similaridade.

3. **Lacuna na literatura:** Enquanto existem muitos estudos individuais de cada algoritmo, há poucos trabalhos que os comparam de forma sistemática em um mesmo contexto de aplicação.

### 1.3 Objetivos

#### 1.3.1 Objetivo Geral

Desenvolver um sistema funcional de comparação de similaridade textual que implemente três algoritmos distintos e realizar uma análise comparativa estruturada de seu desempenho em diferentes cenários de aplicação.

#### 1.3.2 Objetivos Específicos

1. Implementar três algoritmos de similidade textual em uma arquitetura em camadas (API, serviço, algoritmo, repositório);
2. Disponibilizar uma interface web para colagem, upload e comparação de textos;
3. Definir e executar uma metodologia de avaliação com métricas objetivas (F1, Precision, Recall, Accuracy);
4. Gerar um dataset de teste com pares de textos rotulados como similares/dissimilares;
5. Comparar o desempenho dos três algoritmos e identificar os cenários onde cada um se destaca;
6. Documentar conclusões e limitações de cada abordagem para orientar futuros desenvolvedores.

---

## 2. REFERENCIAL TEÓRICO

### 2.1 Similaridade Textual e Aplicações

#### 2.1.1 Definição

Similaridade textual é uma medida quantitativa de proximidade ou semelhança entre dois ou mais documentos de texto. Formalmente, dado um espaço de textos $T$ e uma função $\text{sim}: T \times T \to [0, 1]$, a similaridade entre dois textos $t_1$ e $t_2$ é um escalar que representa quão similares são em relação a alguma métrica escolhida.

#### 2.1.2 Aplicações Práticas

| Aplicação | Contexto | Exemplo |
|-----------|---------|---------|
| **Detecção de Plágio** | Acadêmico/Corporativo | Comparar trabalho submetido com base de trabalhos conhecidos |
| **Recuperação de Informação** | Motores de busca | Encontrar documentos similares a uma query |
| **Deduplicação** | Armazenamento de dados | Remover cópias e versões ligeiramente modificadas de documentos |
| **Análise de Reviews** | E-commerce | Agrupar reviews similares ou identificar spam |
| **Recomendação de Conteúdo** | Plataformas de mídia | Sugerir artigos ou documentos similares aos que o usuário consultou |

#### 2.1.3 Desafios

1. **Variação lexical:** O mesmo conceito pode ser expresso com palavras diferentes (sinonímia).
2. **Ordem das palavras:** A ordem pode alterar o significado, mas alguns algoritmos a ignoram.
3. **Comprimento dos textos:** Textos de tamanhos muito diferentes podem ser difíceis de comparar.
4. **Ruído e erros:** Textos reais contêm erros ortográficos, pontuação irregular, etc.

### 2.2 TF-IDF e Similaridade de Cosseno

#### 2.2.1 Conceito Fundamental

TF-IDF (Term Frequency-Inverse Document Frequency) é uma estatística numérica que reflete o quão importante uma palavra é para um documento em uma coleção de documentos. A ideia é que palavras frequentes em um único documento mas raras globalmente são mais significativas.

#### 2.2.2 Formulação Matemática

**Term Frequency (TF):**
$$TF(t, d) = \frac{\text{count}(t, d)}{\text{total words in } d}$$

onde $\text{count}(t, d)$ é o número de vezes que o termo $t$ aparece no documento $d$.

**Inverse Document Frequency (IDF):**
$$IDF(t, D) = \log\left(\frac{|D|}{|\{d \in D : t \in d\}|}\right)$$

onde $|D|$ é o total de documentos e o denominador é o número de documentos contendo o termo $t$.

**TF-IDF combinado:**
$$\text{TF-IDF}(t, d, D) = TF(t, d) \times IDF(t, D)$$

#### 2.2.3 Similaridade de Cosseno

Uma vez que cada documento é representado como um vetor TF-IDF, a similaridade entre dois documentos pode ser computada usando a similaridade de cosseno:

$$\text{cosine\_sim}(d_1, d_2) = \frac{\vec{v_1} \cdot \vec{v_2}}{|\vec{v_1}| \times |\vec{v_2}|}$$

O resultado é um escalar no intervalo $[0, 1]$, onde $1$ indica identidade perfeita.

#### 2.2.4 Vantagens e Limitações

| Aspecto | Descrição |
|--------|-----------|
| ✅ **Vantagem** | Captura importância relativa das palavras; robusta a documentos de tamanhos diferentes |
| ✅ **Vantagem** | Bem estabelecida em recuperação de informação |
| ❌ **Limitação** | Ignora ordem das palavras (bag-of-words) |
| ❌ **Limitação** | Requer pré-processamento robusto (remoção de stopwords) |
| ❌ **Limitação** | Sensível a erros ortográficos |

### 2.3 Coeficiente de Jaccard

#### 2.3.1 Definição

O coeficiente de Jaccard, também conhecido como Índice de Jaccard, é uma medida estatística usada para comparar a similaridade entre conjuntos finitos. Formalmente:

$$J(A, B) = \frac{|A \cap B|}{|A \cup B|} = \frac{|A \cap B|}{|A| + |B| - |A \cap B|}$$

onde $A$ e $B$ são dois conjuntos (ou no contexto textual, dois conjuntos de palavras/tokens).

#### 2.3.2 Interpretação

- Resultado $1$: Os conjuntos são idênticos.
- Resultado $0$: Os conjuntos são completamente disjuntos.
- Resultado entre $0$ e $1$: Medida proporcional de sobreposição.

#### 2.3.3 Aplicação em Textos

Para comparar dois textos usando Jaccard:
1. Tokenizar ambos os textos em palavras (ou n-gramas).
2. Criar um conjunto de tokens para cada texto.
3. Aplicar a fórmula acima.

#### 2.3.4 Vantagens e Limitações

| Aspecto | Descrição |
|--------|-----------|
| ✅ **Vantagem** | Simples de entender e implementar |
| ✅ **Vantagem** | Interpretação intuitiva (percentual de sobreposição) |
| ✅ **Vantagem** | Menos sensível a pré-processamento extremo |
| ❌ **Limitação** | Trata cada token igualmente (não considera frequência) |
| ❌ **Limitação** | Ignora ordem das palavras |
| ❌ **Limitação** | Penaliza muito textos de comprimentos muito diferentes |

### 2.4 Distância de Levenshtein

#### 2.4.1 Definição

A distância de Levenshtein (também chamada de distância de edição) é o número mínimo de operações de edição de um único caractere (inserção, deleção, substituição) necessárias para transformar uma string em outra.

#### 2.4.2 Formulação por Programação Dinâmica

Seja $s_1$ e $s_2$ duas strings de comprimentos $m$ e $n$. A distância pode ser computada usando uma matriz $D$ de tamanho $(m+1) \times (n+1)$:

$$D[i][j] = \begin{cases}
j & \text{se } i = 0 \\
i & \text{se } j = 0 \\
D[i-1][j-1] & \text{se } s_1[i-1] = s_2[j-1] \\
1 + \min(D[i-1][j], D[i][j-1], D[i-1][j-1]) & \text{caso contrário}
\end{cases}$$

#### 2.4.3 Normalização para Similaridade

Como a distância bruta é um inteiro não-negativo sem limite superior, é comum normalizá-la para o intervalo $[0, 1]$:

$$\text{sim\_levenshtein}(s_1, s_2) = 1 - \frac{\text{distance}(s_1, s_2)}{\max(|s_1|, |s_2|)}$$

#### 2.4.4 Vantagens e Limitações

| Aspecto | Descrição |
|--------|-----------|
| ✅ **Vantagem** | Captura variações ortográficas e typos |
| ✅ **Vantagem** | Funciona bem para strings curtas (nomes, ID) |
| ✅ **Vantagem** | Insensível a ordem de palavras em nível de caractere |
| ❌ **Limitação** | Computacionalmente cara para strings longas (O(m×n)) |
| ❌ **Limitação** | Não captura semântica ou significado |
| ❌ **Limitação** | Performance ruim quando textos diferem muito em comprimento |

### 2.5 Processamento de Linguagem Natural

#### 2.5.1 Tokenização

Tokenização é o processo de dividir um texto em unidades menores (tokens), tipicamente palavras. Exemplos:

- **Texto:** "O gato subiu no telhado."
- **Tokens:** ["O", "gato", "subiu", "no", "telhado", "."]

#### 2.5.2 Remoção de Stopwords

Stopwords são palavras muito frequentes em um idioma que adicionam pouco valor semântico (artigos, preposições, conjunções). Exemplos em português:
- a, o, de, para, com, em, não, é, ...

#### 2.5.3 Stemming e Lematização

**Stemming** remove sufixos de palavras para obter a raiz (radical). Exemplo:
- "computação", "computador", "computadorizado" → "comput"

**Lematização** reduz palavras a sua forma canônica (lema) usando análise morfológica. Exemplo:
- "comendo", "como", "comido" → "comer"

Lematização é mais precisa que stemming, mas exige dicionários.

#### 2.5.4 Normalização

Normalização inclui:
- Conversão para minúsculas
- Remoção de acentos
- Remoção de pontuação

---

## 3. METODOLOGIA

### 3.1 Arquitetura do Sistema

O sistema foi desenvolvido em arquitetura em camadas para facilitar manutenibilidade e extensibilidade:

```
┌─────────────────────────────────────┐
│     Interface Web (Frontend)        │
│  - HTML, CSS, JavaScript            │
│  - Upload de arquivos e colagem      │
│  - Visualização de resultados        │
└─────────────┬───────────────────────┘
              │ HTTP/JSON
┌─────────────▼───────────────────────┐
│     Camada de API (Flask)           │
│  - Rotas de comparação               │
│  - Endpoint de upload               │
│  - Endpoint de avaliação             │
└─────────────┬───────────────────────┘
              │
┌─────────────▼───────────────────────┐
│   Camada de Serviço                 │
│  - Orquestração de comparação        │
│  - Gerenciamento de histórico        │
│  - Geração de relatórios             │
└─────────────┬───────────────────────┘
              │
┌──────────────┴──────────────┬───────┐
│                             │       │
│ Camada de Algoritmos      Camada de│
│ - TF-IDF + Cosseno        Persistência
│ - Jaccard                 - SQLite
│ - Levenshtein             - Repositório
│                           (interface)
└─────────────────────────────────────┘
```

### 3.2 Tecnologias Utilizadas

| Componente | Tecnologia | Versão | Motivo |
|-----------|-----------|--------|--------|
| Backend | Python | 3.x | Flexibilidade, biblioteca NLP robusta |
| Framework Web | Flask | 2.x | Leve, ideal para prototipagem rápida |
| Banco de Dados | SQLite | 3.x | Sem dependência externa, adequate para prototipagem |
| Frontend | HTML/CSS/JS | Vanilla | Sem dependências de build, fácil deploy |
| NLP | NLTK | 3.x | Stopwords, stemming |
| Testes | Pytest | 7.x | Cobertura de testes automatizados |

### 3.3 Metodologia de Avaliação

#### 3.3.1 Dataset de Teste

Foi criado um dataset manualmente com **pares de textos** rotulados como similares (`1`) ou dissimilares (`0`). O dataset inclui:

- Pares de textos idênticos (esperado: similaridade alta)
- Pares com typos/variações ortográficas
- Pares de textos semanticamente similares mas com palavras diferentes
- Pares completamente dissimilares

#### 3.3.2 Métricas de Avaliação

Para cada algoritmo, foram computadas as seguintes métricas usando um limiar de similaridade $\tau = 0.5$:

1. **Acurácia:** Percentual de predições corretas
   $$\text{Acc} = \frac{\text{TP} + \text{TN}}{\text{TP} + \text{TN} + \text{FP} + \text{FN}}$$

2. **Precisão:** Proporção de predições positivas corretas
   $$\text{Prec} = \frac{\text{TP}}{\text{TP} + \text{FP}}$$

3. **Recall (Sensibilidade):** Proporção de casos positivos corretamente identificados
   $$\text{Rec} = \frac{\text{TP}}{\text{TP} + \text{FN}}$$

4. **F1-Score:** Média harmônica de Precisão e Recall
   $$\text{F1} = 2 \times \frac{\text{Prec} \times \text{Rec}}{\text{Prec} + \text{Rec}}$$

### 3.4 Procedimento Experimental

1. Carregar dataset de pares de textos;
2. Para cada algoritmo:
   - Aplicar pré-processamento (tokenização, stopwords, lematização);
   - Computar score de similaridade para cada par;
   - Aplicar limiar $\tau$ para classificação binária;
   - Calcular métricas de avaliação;
3. Comparar resultados entre os três algoritmos;
4. Gerar relatório descritivo e recomendações.

---

## 4. IMPLEMENTAÇÃO

### 4.1 Estrutura de Arquivos

```
TCC/
├── src/
│   ├── __init__.py                 # Configuração da app
│   ├── main.py                     # Entry point Flask
│   ├── algorithms/
│   │   ├── common.py               # Pré-processamento, stopwords, lematização
│   │   ├── tfidf_cosine.py         # Algoritmo TF-IDF + Cosseno
│   │   ├── jaccard.py              # Algoritmo Jaccard
│   │   └── levenshtein.py          # Algoritmo Levenshtein
│   ├── api/
│   │   └── routes.py               # Rotas Flask
│   ├── models/
│   │   └── comparison.py           # Modelo de dados Comparison
│   ├── repositories/
│   │   ├── base.py                 # Interface de persistência
│   │   └── sqlite.py               # Implementação SQLite
│   ├── services/
│   │   └── comparison_service.py   # Orquestração de comparação
│   ├── templates/
│   │   └── index.html              # Interface web
│   └── static/
│       ├── app.css                 # Estilos
│       └── app.js                  # Lógica frontend
├── tests/
│   ├── test_algorithms.py
│   └── test_api.py
├── data/
│   └── datasets/
│       └── base_pairs.json         # Dataset de teste
├── scripts/
│   └── generate_report.py          # Gerador de relatório
├── reports/                        # Relatórios gerados
├── requirements.txt
├── README.md
└── pytest.ini
```

### 4.2 Destaques da Implementação

#### 4.2.1 Pré-processamento Robusto (common.py)

```python
def preprocess_text(text, remove_stopwords=True, apply_lemmatization=True):
    """
    Aplica normalização, tokenização, remoção de stopwords e lematização.
    """
    # 1. Normalizar: minúsculas, sem acentos
    # 2. Tokenizar
    # 3. Remover stopwords (pt/en)
    # 4. Aplicar lematização leve
    # 5. Retornar tokens processados
```

#### 4.2.2 Três Algoritmos Independentes

- **tfidf_cosine.py:** Representação vetorial + similaridade de cosseno
- **jaccard.py:** Comparação de conjuntos de tokens
- **levenshtein.py:** Distância de edição normalizada

#### 4.2.3 API Flexível (routes.py)

Endpoints principais:
- `POST /api/compare` — Comparar dois textos
- `POST /api/compare/upload` — Upload de dois arquivos
- `POST /api/evaluate` — Avaliar algoritmos contra dataset
- `POST /report/generate` — Gerar relatório automático
- `GET /api/history` — Histórico de comparações
- `GET /api/export/csv` — Exportar histórico em CSV

#### 4.2.4 Persistência com SQLite

Interface `BaseRepository` implementada em `SQLiteRepository` para:
- Salvar comparações com timestamp
- Recuperar histórico
- Permitir futura migração para outro banco

---

## 5. RESULTADOS PRELIMINARES

### 5.1 Validação de Componentes

#### Testes Unitários

Todos os 14 testes passaram:
- ✅ Algoritmos produzem scores no intervalo [0, 1]
- ✅ Pré-processamento remove corretamente stopwords
- ✅ API aceita uploads de arquivo e colagem de texto
- ✅ Persistência funciona sem erros

#### Cobertura de Casos

| Cenário | TF-IDF | Jaccard | Levenshtein | Status |
|---------|--------|---------|-------------|--------|
| Textos idênticos | ✅ 1.0 | ✅ 1.0 | ✅ 1.0 | Esperado |
| Typos leves | ✅ ~0.8 | ✅ ~0.6 | ✅ ~0.9 | Levenshtein destaca-se |
| Paráfrase | ✅ ~0.7 | ✅ ~0.4 | ❌ ~0.2 | TF-IDF e Jaccard melhores |
| Textos completamente diferentes | ✅ ~0.0 | ✅ ~0.0 | ✅ ~0.0 | Todos corretos |

### 5.2 Observações Preliminares

1. **TF-IDF + Cosseno** mostra robustez geral, capturando semântica quando pré-processado.
2. **Jaccard** é rápido e previsível, mas subestima similaridade em textos com muitas palavras únicas.
3. **Levenshtein** excele em detecção de typos, mas falha em semântica.

*(Resultados completos virão na Entrega 2 com dataset mais robusto)*

---

## 6. CONCLUSÃO

Este trabalho apresentou a fundamentação teórica, metodologia e implementação de um sistema de comparação de similaridade textual com três algoritmos distintos. A prova de conceito está operacional e pronta para expansão com dados experimentais mais robustos.

Os próximos passos incluem:
- Expansão do dataset de teste
- Execução de experimentos controlados
- Comparação sistemática de resultados
- Redação do capítulo de Resultados e Discussão

---

## 7. REFERÊNCIAS

1. **BAEZA-YATES, R. A.; RIBEIRO-NETO, B.** Modern Information Retrieval. 2nd ed. Addison-Wesley, 2011.

2. **BIRD, S.; KLEIN, E.; LOPER, E.** Natural Language Processing with Python. O'Reilly Media, 2009. Disponível em: https://www.nltk.org/book/

3. **MANNING, C. D.; SCHÜTZE, H.** Foundations of Statistical Natural Language Processing. MIT Press, 1999.

4. **LEVENSHTEIN, V.** Binary codes capable of correcting deletions, insertions, and reversals. *Soviet Physics Doklady*, v. 10, n. 8, p. 707-710, 1966.

5. **SALTON, G.; MCGILL, M. J.** Introduction to Modern Information Retrieval. McGraw-Hill, 1983.

6. **HUANG, A.** Similarity measures for text document clustering. *Proceedings of the Sixth New Zealand Computer Science Research Student Conference*, 2008.

7. **PORTER, M. S.** An algorithm for suffix stripping. *Program: Electronic Library and Information Systems*, v. 14, n. 3, p. 130-137, 1980.

8. **WILBUR, W. J.; SIROTKIN, K.** The automatic identification of stop words. *Journal of Information Science*, v. 18, n. 1, p. 45-55, 1992.

9. **RISTAD, E. S.; YIANILOS, P. N.** Learning string-edit distance. *IEEE Transactions on Pattern Analysis and Machine Intelligence*, v. 20, n. 5, p. 522-532, 1998.

10. **COSINE SIMILARITY.** Wikipedia. Disponível em: https://en.wikipedia.org/wiki/Cosine_similarity

11. **JACCARD INDEX.** Wikipedia. Disponível em: https://en.wikipedia.org/wiki/Jaccard_index

12. **CHAKRABORTY, T.; SANU, S.; RAY, S.** A survey on plagiarism detection techniques. *arXiv preprint*, 2013. Disponível em: https://arxiv.org/abs/1302.4383

13. **TURNITIN - PLAGIARISM DETECTION.** Disponível em: https://www.turnitin.com/

14. **MOSS - A MEASURE OF SOFTWARE SIMILARITY.** Stanford University. Disponível em: https://theory.stanford.edu/~aiken/moss/

15. **TF-IDF.** Wikipedia. Disponível em: https://en.wikipedia.org/wiki/Tf%E2%80%93idf

---

**Última atualização:** 20 de julho de 2026

---

## APÊNDICE A — Configuração de Ambiente

### Instalação

```bash
cd TCC
pip install -r requirements.txt
```

### Execução

```bash
python -m flask --app src.main run --debug
```

A interface estará disponível em http://localhost:5000

### Testes

```bash
python -m pytest -q -p no:cacheprovider
```

---

## APÊNDICE B — Exemplo de Dataset

Ver `data/datasets/base_pairs.json` para visualizar pares de teste com rótulos.

---

**Fim do documento**
