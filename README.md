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

## Testes

```bash
python -m pytest -q -p no:cacheprovider
```

## Observações de Portabilidade

- Use sempre `python -m ...` em vez de binários diretos para evitar problemas de PATH.
- O projeto usa SQLite por padrão e não exige banco externo.
- O diretório `reports/` é gerado localmente e não deve ser versionado.

## Formatos suportados (resumo)

- Office: `.doc`, `.docx`, `.odt`, `.rtf`, `.xlsx`, `.xlsm`
- Código: `.py`, `.java`, `.c`, `.cpp`, `.h`, `.hpp`, `.cs`, `.js`, `.ts`, `.html`, `.css`, `.m`
- Texto/Dados: `.txt`, `.md`, `.csv`, `.json`, `.xml`, `.yml`, `.yaml`, `.sql`
