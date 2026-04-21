# 🚀 Desafio DS: Inteligência de Escolha WhatsApp (Prefeitura do Rio)

## 🎯 Contexto e Missão

Na Prefeitura do Rio, enviamos milhares de mensagens por mês via WhatsApp. Um desafio crítico é a **Multiplicidade**: um mesmo cidadão possui vários telefones vinculados a ele em diferentes sistemas (Saúde, Educação, IPTU, etc.), muitos dos quais estão desatualizados.

Este projeto implementa a **Inteligência de Escolha**: um algoritmo de priorização para identificar quais fontes de dados são mais confiáveis ("quentes") e escolher automaticamente os **dois melhores números** para garantir a entrega das mensagens com o menor custo.

---

## ⚙️ Setup do Ambiente

O projeto utiliza o gerenciador de pacotes `uv` para garantir reprodutibilidade e performance.

### Pré-requisitos
- Python 3.11+
- [uv](https://github.com/astral-sh/uv) instalado

### Configuração Inicial
```bash
# 1. Criar ambiente virtual e instalar dependências
uv venv
uv sync

# 2. Registrar o kernel do Jupyter (necessário para rodar os notebooks)
uv run python -m ipykernel install --user --name=desafio-whatsapp --display-name "Desafio WhatsApp DS"
```

---

## 🗂️ Estrutura do Projeto

```
desafio-whatsapp-ds/
│
├── data/                    ← Arquivos .parquet (ver seção de Dados)
├── notebooks/
│   ├── 01_eda_qualidade.ipynb    ← Parte 1: EDA e Qualidade das Fontes
│   ├── 02_priorizacao.ipynb      ← Parte 2: Ranking e Algoritmo de Score
│   └── 03_experimento_ab.ipynb   ← Parte 3: Desenho do Teste A/B
│
├── src/
│   └── scoring.py           ← Core logic: Algoritmo de Score e Wilson LB
│
├── outputs/                 ← Gráficos e tabelas exportados
├── pyproject.toml           ← Dependências gerenciadas pelo uv
└── AGENTS.md                ← Instruções de infra e arquitetura
```

---

## 🧠 Inteligência Implementada

O algoritmo de priorização em `src/scoring.py` baseia-se em três pilares fundamentais:

1.  **Ranking de Fontes (Wilson Lower Bound)**: Utilizamos estatística para rankear os sistemas de origem, penalizando fontes com baixo volume de dados e garantindo que a taxa de entrega seja estatisticamente sólida.
2.  **Decaimento Temporal (Frescor)**: Aplicamos um decaimento exponencial na pontuação baseado na data da última atualização do telefone. Dados "parados" no sistema perdem valor ao longo do tempo.
3.  **Localidade (DDD)**: Priorização de DDDs locais (ex: 21 para o Rio de Janeiro) como fator de desempate e afinidade.

---

## 📥 Dados

Os arquivos de dados originais (`.parquet`) devem ser colocados na pasta `data/`. 

Devido a restrições de acesso, os arquivos devem ser baixados manualmente via Google Cloud Console:
- **Bucket GCS**: [https://console.cloud.google.com/storage/browser/case_vagas/whatsapp](https://console.cloud.google.com/storage/browser/case_vagas/whatsapp)
- **Arquivos necessários**:
  - `base_disparo_mascarado.parquet`
  - `dim_telefone_mascarado.parquet`

---

## 🧪 Como Reproduzir

1.  Siga os passos da **Configuração Inicial**.
2.  Coloque os arquivos `.parquet` em `data/`.
3.  Execute os notebooks na ordem numérica (`01 -> 02 -> 03`) utilizando o kernel `Desafio WhatsApp DS`.
4.  As funções auxiliares e a lógica do score serão carregadas automaticamente de `src/scoring.py`.

---

## ✅ Checklist de Qualidade

- [x] Ambiente gerenciado por `uv`.
- [x] Código em `src/` validado pelo `ruff`.
- [x] Notebooks estruturados conforme o pipeline de análise.
- [x] Lógica de negócio isolada em módulos reutilizáveis.

---
🚀 *Implementado com foco em dados e impacto de negócio.*