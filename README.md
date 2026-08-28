# Text Similarity Comparator (Flask)

API e interface web local para comparação de similaridade textual com três algoritmos:
- TF-IDF + cosseno
- Jaccard
- Levenshtein normalizado

## Requisitos

- Python 3.11+ (recomendado 3.12+)
- pip atualizado

Dependências Python são instaladas via `requirements.txt`.

## Instalação

### Windows (PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### Linux/macOS (bash/zsh)

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Execução

```bash
python -m flask --app src.main run --debug
```

Aplicação disponível em `http://127.0.0.1:5000`.

## Testes

```bash
python -m pytest -q -p no:cacheprovider
```

## Observações de Portabilidade

- Use sempre `python -m ...` em vez de binários diretos para evitar problemas de PATH.
- O projeto usa SQLite por padrão e não exige banco externo.
- O diretório `reports/` é gerado localmente e não deve ser versionado.
