# Text Similarity Comparator (Flask)

API e interface web local para comparação de similaridade textual com três algoritmos:
- TF-IDF + cosseno
- Jaccard
- Levenshtein normalizado

Também inclui camada de IA híbrida:
- similaridade semântica local com scikit-learn (char n-grams)
- score ensemble (clássico + IA local)
- suporte opcional a provedores externos: Gemini, OpenAI e Claude

## Requisitos

- Python 3.11+ (recomendado 3.12+)
- pip atualizado

Dependências Python são instaladas via `requirements.txt`.

Bibliotecas incluídas no projeto:
- Flask
- pytest
- pypdf
- python-docx
- odfpy
- striprtf
- pandas
- numpy
- matplotlib
- seaborn
- openpyxl
- scikit-learn
- requests

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

Atalho Linux/macOS:

```bash
bash iniciar_sistema.sh
```

Aplicação disponível em `http://127.0.0.1:5000`.

## Endpoints úteis

- `POST /compare`: comparação clássica
- `POST /compare-ai`: comparação clássica + IA híbrida
- `POST /compare-files`: comparação por arquivos
- `GET /jobs/<job_id>`: consulta status de processamento assíncrono
- `POST /benchmark/performance`: benchmark de latência por algoritmo e formato
- `GET /supported-formats`: lista extensões suportadas por grupos

Payload básico para `POST /compare-ai`:

```json
{
	"text_a": "conteudo A",
	"text_b": "conteudo B",
	"include_providers": false
}
```

Se `include_providers` for `true`, as integrações externas são tentadas quando houver chave configurada.

Variáveis opcionais para IA externa:
- `TCC_GEMINI_API_KEY`
- `TCC_OPENAI_API_KEY`
- `TCC_CLAUDE_API_KEY`

Variáveis opcionais de performance:
- `TCC_CACHE_MAX_ITEMS` (default `1024`): tamanho do cache de comparações
- `TCC_ASYNC_COMPARE_THRESHOLD_BYTES` (default `1048576`): tamanho mínimo para processar upload em fila assíncrona
- `TCC_ASYNC_WORKERS` (default `2`): workers da fila assíncrona
- `TCC_MAX_UPLOAD_BYTES_BY_EXT` (JSON): limite por extensão.

Exemplo:

```bash
set TCC_MAX_UPLOAD_BYTES_BY_EXT={".pdf":1048576,".xlsx":524288}
```

## Testes

```bash
python -m pytest -q -p no:cacheprovider
```

## Observações de Portabilidade

- Use sempre `python -m ...` em vez de binários diretos para evitar problemas de PATH.
- O projeto usa SQLite por padrão e não exige banco externo.
- O diretório `reports/` é gerado localmente e não deve ser versionado.

## Teste de carga simples

```bash
python scripts/load_smoke.py
```

Esse script executa requisições concorrentes locais e retorna média, mediana e p95 de latência.

## Formatos suportados (resumo)

- Office: `.doc`, `.docx`, `.odt`, `.rtf`, `.xlsx`, `.xlsm`
- Código: `.py`, `.java`, `.c`, `.cpp`, `.h`, `.hpp`, `.cs`, `.js`, `.ts`, `.html`, `.css`, `.m`
- Texto/Dados: `.txt`, `.md`, `.csv`, `.json`, `.xml`, `.yml`, `.yaml`, `.sql`
