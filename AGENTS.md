# AGENTS.md — Desafio DS: Inteligência de Escolha WhatsApp (Prefeitura do Rio)

## 🎯 Missão do Projeto

Este projeto resolve um desafio técnico de Ciência de Dados: dado que um cidadão possui múltiplos telefones cadastrados em diferentes sistemas da Prefeitura do Rio, criar um algoritmo de priorização que escolha os **dois melhores números** para envio de mensagens via WhatsApp, maximizando a taxa de entrega e reduzindo custos.

---

## ⚙️ Stack e Ferramentas

- **Gerenciador de pacotes:** `uv` (nunca usar pip diretamente)
- **Linguagem:** Python 3.11+
- **Notebooks:** Jupyter (.ipynb), bem documentados em português
- **Formato dos dados:** Parquet (leitura via `pyarrow`)

---

## 📦 Setup Inicial do Projeto

Ao inicializar o projeto, execute **exatamente** os seguintes passos:

```bash
# 1. Inicializar projeto com uv
uv init desafio-whatsapp-ds
cd desafio-whatsapp-ds

# 2. Criar ambiente virtual
uv venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate    # Windows

# 3. Adicionar dependências
uv add pandas pyarrow numpy scipy matplotlib seaborn jupyter ipykernel

# 4. Adicionar dependências de desenvolvimento
uv add --dev black ruff pytest

# 5. Registrar kernel do Jupyter
uv run python -m ipykernel install --user --name=desafio-whatsapp --display-name "Desafio WhatsApp DS"
```

---

## 🗂️ Estrutura de Diretórios

Crie exatamente esta estrutura ao inicializar:

```
desafio-whatsapp-ds/
│
├── AGENTS.md                        ← Este arquivo
├── README.md                        ← Apresentação do projeto (preencher ao final)
├── pyproject.toml                   ← Gerenciado pelo uv (não editar manualmente)
├── uv.lock                          ← Lockfile do uv (commitar no git)
│
├── data/
│   └── .gitkeep                     ← Pasta para os Parquets locais (não commitar dados)
│
├── notebooks/
│   ├── 01_eda_qualidade.ipynb       ← Parte 1: EDA e Qualidade das Fontes
│   ├── 02_priorizacao.ipynb         ← Parte 2: Ranking e Algoritmo de Score
│   └── 03_experimento_ab.ipynb      ← Parte 3: Desenho do Teste A/B
│
├── src/
│   └── scoring.py                   ← Funções reutilizáveis do algoritmo de score
│
├── outputs/
│   └── .gitkeep                     ← Gráficos e tabelas exportados
│
└── .gitignore
```

### `.gitignore` padrão a criar:

```
.venv/
__pycache__/
*.pyc
.ipynb_checkpoints/
data/*.parquet
data/*.csv
outputs/*.png
.env
```

---

## 📓 Conteúdo Inicial dos Notebooks

Ao criar cada notebook, preencha as primeiras células com este padrão:

### `01_eda_qualidade.ipynb` — célula de setup:

```python
# Imports padrão
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

# Configurações de visualização
sns.set_theme(style="whitegrid", palette="muted")
plt.rcParams["figure.dpi"] = 120
pd.set_option("display.max_columns", None)
pd.set_option("display.float_format", "{:.4f}".format)

# Paths
DATA_DIR = Path("../data")
OUTPUT_DIR = Path("../outputs")
OUTPUT_DIR.mkdir(exist_ok=True)

# Leitura dos dados
df_disparos  = pd.read_parquet(DATA_DIR / "base_disparo_mascarado.parquet")
df_telefones = pd.read_parquet(DATA_DIR / "dim_telefone_mascarado.parquet")

print(f"disparos : {df_disparos.shape}")
print(f"telefones: {df_telefones.shape}")
```

### `02_priorizacao.ipynb` — célula de setup:

```python
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from pathlib import Path
import sys
sys.path.append("../src")
from scoring import calcular_score_telefone, wilson_lower_bound

sns.set_theme(style="whitegrid")
DATA_DIR   = Path("../data")
OUTPUT_DIR = Path("../outputs")
```

### `03_experimento_ab.ipynb` — célula de setup:

```python
import numpy as np
from scipy.stats import norm, proportions_ztest
import matplotlib.pyplot as plt
import seaborn as sns

sns.set_theme(style="whitegrid")
```

---

## 🧠 Funções a Implementar em `src/scoring.py`

Crie o arquivo com estas funções documentadas:

```python
"""
scoring.py — Algoritmo de priorização de telefones para disparo WhatsApp
Prefeitura do Rio de Janeiro — Desafio Técnico DS
"""

import numpy as np
import pandas as pd


def wilson_lower_bound(positives: int, total: int, confidence: float = 0.95) -> float:
    """
    Limite inferior do intervalo de confiança de Wilson para proporções.
    Mais robusto que a taxa simples para amostras com volumes diferentes.
    """
    # TODO: implementar


def calcular_score_telefone(
    row: pd.Series,
    sistema_scores: dict,
    hoje: pd.Timestamp = None,
    peso_sistema: float = 0.50,
    peso_frescor: float = 0.40,
    peso_ddd: float = 0.10,
    ddd_preferencial: str = "21",
) -> float:
    """
    Combina sistema de origem, frescor temporal e DDD em um score 0-1.
    Parâmetros de peso devem somar 1.0.
    """
    # TODO: implementar


def selecionar_top_n(
    df_telefones: pd.DataFrame,
    id_cidadao_col: str,
    score_col: str = "score",
    n: int = 2,
) -> pd.DataFrame:
    """
    Retorna os N telefones com maior score por cidadão.
    """
    # TODO: implementar
```

---

## 📏 Padrões de Código

- Todos os comentários e docstrings em **português**
- Usar `f-strings` para formatação de strings
- Nomear variáveis em `snake_case`
- Cada célula de notebook deve ter uma **célula Markdown acima** explicando o objetivo
- Salvar todo gráfico gerado em `outputs/` com `plt.savefig(..., dpi=150, bbox_inches='tight')`
- Rodar `ruff check src/` antes de considerar qualquer arquivo `.py` como finalizado

---

## ✅ Definição de "Tarefa Concluída"

Uma tarefa só está concluída quando:

1. O notebook roda do zero sem erros (`Kernel > Restart & Run All`)
2. Todos os gráficos estão salvos em `outputs/`
3. O `src/scoring.py` passa em `ruff check` sem erros
4. O `README.md` tem: objetivo, premissas assumidas e instruções de reprodução
