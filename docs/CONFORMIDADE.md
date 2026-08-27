# MAPA DE CONFORMIDADE: CÓDIGO ↔ DOCUMENTO TCC

**Data:** 20/07/2026  
**Status:** Entrega 1 - Em progresso  
**Prazo:** 28/08/2026

---

## 1. CHECKLIST DE CONFORMIDADE

### Seção de Introdução
- [x] Problemática identificada e formalizada
- [x] Justificativa de pesquisa descrita
- [x] Objetivo geral definido
- [x] Objetivos específicos (6) listados
- [ ] Estrutura do documento descrita

**Arquivos relacionados no código:**
- `src/main.py` — Demonstra o conceito de "comparação textual"
- `src/api/routes.py` — Implementa os objetivos específicos #1, #2
- `README.md` — Prova de conceito funcional

---

### Seção de Referencial Teórico
- [x] 2.1 Similaridade Textual e Aplicações
  - [x] Definição matemática
  - [x] Aplicações práticas (5 cenários)
  - [x] Desafios listados
  
- [x] 2.2 TF-IDF + Similaridade de Cosseno
  - [x] Conceito e formulação matemática
  - [x] Vantagens e limitações
  - [ ] Exemplos práticos com dados reais
  
- [x] 2.3 Coeficiente de Jaccard
  - [x] Definição e interpretação
  - [x] Aplicação em textos
  - [x] Vantagens e limitações
  - [ ] Comparação direta com TF-IDF
  
- [x] 2.4 Distância de Levenshtein
  - [x] Definição com algoritmo DP
  - [x] Normalização para [0,1]
  - [x] Vantagens e limitações
  - [ ] Exemplos de typos reais
  
- [x] 2.5 Processamento de Linguagem Natural
  - [x] Tokenização
  - [x] Remoção de stopwords
  - [x] Stemming e Lematização
  - [x] Normalização
  - [ ] Impacto prático no sistema

**Arquivos relacionados no código:**
- `src/algorithms/tfidf_cosine.py` — Implementação TF-IDF (seção 2.2)
- `src/algorithms/jaccard.py` — Implementação Jaccard (seção 2.3)
- `src/algorithms/levenshtein.py` — Implementação Levenshtein (seção 2.4)
- `src/algorithms/common.py` — Pré-processamento (seção 2.5)
- `tests/test_algorithms.py` — Validação dos conceitos

---

### Seção de Metodologia
- [x] 3.1 Arquitetura do Sistema (diagrama + descrição)
- [x] 3.2 Tecnologias Utilizadas (tabela com justificativa)
- [x] 3.3 Metodologia de Avaliação (métricas: Acc, Prec, Rec, F1)
- [x] 3.4 Procedimento Experimental (5 passos)
- [ ] Descrição detalhada de cada componente

**Arquivos relacionados no código:**
- Arquitetura (seção 3.1): Mapeamento visual em `docs/ARCHITECTURE.md` (a criar)
- Tecnologias (seção 3.2): Confirmado em `requirements.txt`
- Avaliação (seção 3.3): Implementado em `src/services/comparison_service.py`
- Procedimento (seção 3.4): Script `scripts/generate_report.py`

---

### Seção de Implementação (capítulo 4)
- [x] 4.1 Estrutura de Arquivos (listagem comentada)
- [x] 4.2 Destaques da Implementação (4 subsecções)
- [ ] Fluxograma de execução (entrada → processamento → saída)
- [ ] Trechos de código comentados (exemplo: função de pré-processamento)
- [ ] Decisões de design justificadas

**Arquivos relacionados:**
- Todos em `src/` — mapeados para seção 4.2
- Testes em `tests/` — validam cada componente

---

### Seção de Resultados Preliminares (capítulo 5)
- [x] 5.1 Validação de Componentes
  - [x] Testes Unitários (14 passed)
  - [x] Cobertura de Casos (4 cenários testados)
- [x] 5.2 Observações Preliminares (3 algoritmos analisados)
- [ ] Tabela de resultados numéricos com dataset real
- [ ] Gráficos comparativos (se aplicável)
- [ ] Análise de limitações observadas

**Arquivos relacionados:**
- `reports/similarity_report_2026-07-20T19-29-00_618394+00-00.md` — Resultado do experimento
- `scripts/generate_report.py` — Gerador automático

---

### Seção de Conclusão (capítulo 6)
- [x] Síntese do trabalho realizado
- [x] Próximos passos para Entrega 2
- [ ] Discussão de impacto prático
- [ ] Limitações e sugestões de melhoria

---

### Referências Bibliográficas (capítulo 7)
- [x] 15 referências listadas (conforme requisito)
- [ ] Verificar conformidade ABNT de formatação
- [ ] Adicionar referências a papers específicos de cada algoritmo

---

## 2. RASTREABILIDADE: OBJETIVO ESPECÍFICO → CÓDIGO

| Objetivo Específico | Seção TCC | Arquivo Código | Status |
|---|---|---|---|
| 1. Implementar 3 algoritmos em arquitetura em camadas | 3.1, 4.2 | `src/algorithms/*.py`, `src/services/`, `src/repositories/` | ✅ Completo |
| 2. Interface web para colagem/upload | 4.2.3 | `src/templates/index.html`, `src/static/app.js`, `src/api/routes.py` | ✅ Completo |
| 3. Metodologia de avaliação com métricas | 3.3 | `src/services/comparison_service.py` | ✅ Completo |
| 4. Dataset com pares rotulados | 3.4 | `data/datasets/base_pairs.json` | ✅ Completo |
| 5. Comparar desempenho dos 3 algoritmos | 5.1, 5.2 | `scripts/generate_report.py`, `reports/*` | ⚠️ Parcial (dados experimentais completos em Entrega 2) |
| 6. Documentar conclusões/limitações | 6.0, 5.2 | `docs/TCC.md` | ✅ Completo |

---

## 3. CHECKLIST PRÉ-ENTREGA 1 (28/08/2026)

### Código
- [x] 14 testes passando
- [x] API funcional (GET/POST em 5+ endpoints)
- [x] Interface web operacional
- [x] Banco SQLite com histórico persistente
- [x] Pré-processamento com stopwords + lematização
- [x] 3 algoritmos implementados
- [ ] Documentação inline (docstrings) em 100% das funções públicas
- [ ] Exemplo de uso em README bem detalhado

### Documentação (TCC)
- [x] Introdução formal (problema, objetivos)
- [x] Referencial teórico (5 seções)
- [x] Metodologia descrita
- [x] Implementação documentada
- [x] Resultados preliminares
- [x] Conclusão
- [x] Referências (15 itens)
- [ ] Formatação ABNT completa (verificar)
- [ ] Revisão de ortografia/gramática
- [ ] Inserção de figuras/diagramas (opcional mas recomendado)

### Prova de Conceito
- [x] Sistema executa sem erros
- [x] Testes passam
- [x] Banco persiste dados
- [x] Frontend responde a interações
- [x] Relatório é gerado automaticamente
- [ ] Dataset expandido para 20+ pares
- [ ] Experimento piloto executado

---

## 4. AÇÕES IMEDIATAS (próximos 39 dias até 28/08)

| Ação | Prazo | Responsável | Status |
|------|-------|-------------|--------|
| Expandir dataset para 20+ pares | 25/07 | Dev | 🟡 Em andamento |
| Adicionar docstrings em 100% do código | 27/07 | Dev | ⏳ Não iniciado |
| Executar experimento piloto completo | 30/07 | Pesquisador | ⏳ Não iniciado |
| Revisar ortografia TCC | 05/08 | Revisor | ⏳ Não iniciado |
| Converter para Word/PDF com formatação ABNT | 10/08 | Editor | ⏳ Não iniciado |
| Entregar para orientador revisar | 15/08 | Pesquisador | ⏳ Não iniciado |
| Ajustar feedback do orientador | 25/08 | Dev | ⏳ Não iniciado |
| **ENTREGA FINAL** | **28/08** | **Pesquisador** | **⏳ Pendente** |

---

## 5. ROADMAP PARA ENTREGAS SUBSEQUENTES

### Entrega 2 (~28/10/2026) — Aprofundamento Teórico + Evolução Prática
**Tarefas complementares:**
- Ampliar referencial teórico com comparação sistemática entre algoritmos na literatura
- Adicionar seção "Estado da Arte" (Turnitin, Copyscape, MOSS)
- Expandir dataset para 50-100 pares com cenários diversificados
- Migrar frontend para framework (React/Vue) se necessário
- Implementar cache e otimizações de performance
- Iniciar capítulo de "Trabalhos Relacionados"

### Entrega 3 (~28/12/2026) — Robustez + Validação
**Tarefas:**
- Sistema com todas as funcionalidades centrais testadas
- Dataset definitivo (100-150 pares)
- Experimentos preliminares completos
- Documentação interna expandida (arquitetura em diagramas)
- Capítulo de "Trabalhos Relacionados" concluído

### Entrega 4 (~28/02/2027) — Resultados + Discussão
**Tarefas:**
- Capítulo de Resultados com tabelas e gráficos
- Comparação visual (gráficos) entre algoritmos
- Discussão de limitações e casos de uso ideal para cada algoritmo
- Análise de performance (tempo de execução)

### Entrega 5 (~28/04/2027) — Fechamento
**Tarefas:**
- Conclusão final
- Revisão ABNT completa
- Slides e ensaio de apresentação
- Préparo para defesa

---

## 6. NOTAS IMPORTANTES

### Conformidade ABNT
- [ ] Fonte: Arial 12pt (corpo), títulos em negrito
- [ ] Espaçamento: 1.5 entre linhas
- [ ] Margens: 3cm (esq), 2cm (dir, sup, inf)
- [ ] Citações diretas em recuo de 4cm
- [ ] Referências em ordem alfabética

### Estrutura Recomendada Final do TCC
```
Capa
Contracapa
Resumo
Abstract
Sumário
1. Introdução
2. Referencial Teórico
3. Metodologia
4. Implementação
5. Resultados
6. Discussão
7. Conclusão
8. Referências
Apêndice A — Guia de Instalação
Apêndice B — Dataset Completo
```

---

**Próximo checkpoint:** 25/07/2026 - Expansão de dataset

