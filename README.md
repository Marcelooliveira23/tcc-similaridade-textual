# Ferramenta de Comparacao Textual

Aplicacao web em Flask para comparar textos com:
- TF-IDF + cosseno
- Jaccard
- Levenshtein normalizado

## Executar

```bash
python -m pip install -r requirements.txt
python -m flask --app src.main run --debug
```

## Testes

```bash
python -m pytest -q -p no:cacheprovider
```
