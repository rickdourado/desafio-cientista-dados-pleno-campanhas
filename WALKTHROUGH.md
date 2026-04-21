# 🚀 Walkthrough — Desafio DS: Inteligência de Escolha de Telefones (WhatsApp)

> **Nível:** Analista de Dados Júnior | **Linguagem:** Python  
> Este guia te conduz passo a passo pela solução do desafio técnico da Prefeitura do Rio.

---

## 📋 Visão Geral do Problema

Você precisa responder uma pergunta de negócio simples com dados:

> *"Dado que um cidadão tem múltiplos telefones cadastrados, qual(is) devo usar para garantir que a mensagem chegue?"*

Para isso você vai:
1. **Explorar** os dados históricos de disparos e a dimensão de telefones
2. **Medir** a taxa de entrega por sistema de origem
3. **Detectar** se telefones mais novos entregam mais
4. **Criar** um score de priorização
5. **Propor** um experimento A/B para validar a solução

---

## 🗂️ Estrutura Recomendada de Repositório

```
desafio-whatsapp-ds/
│
├── README.md                   ← Sua apresentação do projeto
├── WALKTHROUGH.md              ← Este arquivo (opcional incluir)
│
├── notebooks/
│   ├── 01_eda_qualidade.ipynb  ← Parte 1: EDA e Qualidade das Fontes
│   ├── 02_priorizacao.ipynb    ← Parte 2: Ranking e Algoritmo
│   └── 03_experimento_ab.ipynb ← Parte 3: Desenho do A/B Test
│
├── src/
│   └── scoring.py              ← Funções reutilizáveis do algoritmo
│
└── requirements.txt
```

---

## ⚙️ Setup do Ambiente

### `requirements.txt`
```
pandas
pyarrow          # leitura de arquivos .parquet
google-cloud-storage  # acesso ao GCS (bucket da prefeitura)
matplotlib
seaborn
scipy            # testes estatísticos no A/B
numpy
jupyter
```

### Instalação
```bash
pip install -r requirements.txt
```

---

## 📥 Passo 0 — Leitura dos Dados

Os dados estão em formato **Parquet** no Google Cloud Storage.

```python
import pandas as pd

# Opção A: leitura direta via URL pública (se o bucket for público)
BASE_URL = "https://storage.googleapis.com/case_vagas/whatsapp/"

df_disparos = pd.read_parquet(BASE_URL + "base_disparo_mascarado.parquet")
df_telefones = pd.read_parquet(BASE_URL + "dim_telefone_mascarado.parquet")

# Opção B: baixar localmente primeiro com gsutil
# gsutil cp gs://case_vagas/whatsapp/*.parquet ./data/

print(df_disparos.shape)
print(df_disparos.head())
print(df_disparos.dtypes)
```

### Checklist de inspeção inicial
```python
# Para cada dataframe, sempre faça isso primeiro:
for df, nome in [(df_disparos, "disparos"), (df_telefones, "telefones")]:
    print(f"\n=== {nome} ===")
    print(f"Linhas: {df.shape[0]:,} | Colunas: {df.shape[1]}")
    print(df.dtypes)
    print(df.isnull().sum())
    print(df.describe(include='all'))
```

---

## 📊 Parte 1 — EDA e Qualidade das Fontes

### 1.1 Entendendo os campos-chave

Antes de qualquer análise, mapeie os campos que você vai usar:

| Campo | Tabela | O que representa |
|---|---|---|
| `status_disparo` | disparos | Se a mensagem foi entregue (DELIVERED, FAILED, etc.) |
| `id_sistema_mask` | telefones | Qual sistema originou aquele telefone |
| `registro_data_atualizacao` | telefones | Quando o telefone foi atualizado no sistema |
| chave de join | ambas | CPF ou ID do cidadão (verifique o nome exato) |

> ⚠️ **Dica:** Rode `df_disparos.columns.tolist()` e `df_telefones.columns.tolist()` para ver os nomes reais antes de começar.

---

### 1.2 Join entre as tabelas

```python
# Identifique a chave de ligação entre as tabelas
# Provavelmente algo como 'id_cidadao_mask' ou 'numero_telefone_mask'

df = df_disparos.merge(
    df_telefones,
    on='chave_de_join',  # ← substitua pelo nome real
    how='left'
)

print(f"Linhas após join: {df.shape[0]:,}")
print(f"% sem match: {df['id_sistema_mask'].isnull().mean():.1%}")
```

---

### 1.3 Análise: Taxa de Entrega por Sistema de Origem

Essa é a análise central da Parte 1.

```python
# Criar flag binária: 1 se DELIVERED, 0 caso contrário
df['entregue'] = (df['status_disparo'] == 'DELIVERED').astype(int)

# Agregar por sistema de origem
taxa_por_sistema = (
    df.groupby('id_sistema_mask')
    .agg(
        total_disparos=('entregue', 'count'),
        total_entregues=('entregue', 'sum')
    )
    .assign(taxa_entrega=lambda x: x['total_entregues'] / x['total_disparos'])
    .sort_values('taxa_entrega', ascending=False)
    .reset_index()
)

print(taxa_por_sistema)
```

**Visualização:**
```python
import matplotlib.pyplot as plt
import seaborn as sns

fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# Gráfico 1: Taxa de entrega
sns.barplot(data=taxa_por_sistema, x='id_sistema_mask', y='taxa_entrega', ax=axes[0])
axes[0].set_title('Taxa de Entrega por Sistema de Origem')
axes[0].set_ylabel('Taxa de Entrega (DELIVERED)')
axes[0].axhline(df['entregue'].mean(), color='red', linestyle='--', label='Média Geral')
axes[0].legend()

# Gráfico 2: Volume de disparos (para detectar viés de seleção!)
sns.barplot(data=taxa_por_sistema, x='id_sistema_mask', y='total_disparos', ax=axes[1])
axes[1].set_title('Volume de Disparos por Sistema (Viés de Seleção)')
axes[1].set_ylabel('Número de Disparos')

plt.tight_layout()
plt.savefig('taxa_entrega_por_sistema.png', dpi=150, bbox_inches='tight')
plt.show()
```

> 🧠 **Por que dois gráficos?**  
> O README avisa sobre **viés de seleção**: sistemas com mais tentativas podem parecer melhores só por volume. Mostre os dois gráficos lado a lado para evidenciar isso — é um ponto diferencial na sua análise.

---

### 1.4 Análise: Decaimento por Data de Atualização

O objetivo aqui é descobrir se telefones "velhos" entregam menos.

```python
import numpy as np

# Calcular "idade" do telefone em dias no momento do disparo
# Se não tiver data do disparo, use a data atual como referência
df['data_atualizacao'] = pd.to_datetime(df['registro_data_atualizacao'])
df['data_disparo'] = pd.to_datetime(df['data_disparo'])  # ajuste o campo

df['dias_desde_atualizacao'] = (df['data_disparo'] - df['data_atualizacao']).dt.days

# Criar faixas de "frescor" do dado
bins = [0, 30, 90, 180, 365, 730, np.inf]
labels = ['0-30d', '31-90d', '91-180d', '6m-1a', '1a-2a', '2a+']

df['faixa_idade'] = pd.cut(df['dias_desde_atualizacao'], bins=bins, labels=labels)

# Taxa de entrega por faixa
decaimento = (
    df.groupby('faixa_idade', observed=True)
    .agg(taxa_entrega=('entregue', 'mean'), volume=('entregue', 'count'))
    .reset_index()
)

print(decaimento)
```

**Visualização do decaimento:**
```python
fig, ax = plt.subplots(figsize=(10, 5))

ax.plot(decaimento['faixa_idade'].astype(str), decaimento['taxa_entrega'], marker='o', linewidth=2)
ax.fill_between(range(len(decaimento)), decaimento['taxa_entrega'], alpha=0.1)
ax.set_title('Decaimento da Taxa de Entrega com a Idade do Telefone')
ax.set_xlabel('Tempo desde última atualização')
ax.set_ylabel('Taxa de Entrega')
ax.axhline(df['entregue'].mean(), color='red', linestyle='--', label='Média Geral')
ax.legend()

plt.savefig('decaimento_temporal.png', dpi=150, bbox_inches='tight')
plt.show()
```

> 💡 **Insight esperado:** A taxa de entrega tende a cair com o tempo. O ponto de inflexão mais acentuado é o "prazo de validade" — pode ser 6 meses, 1 ano. Destaque esse número como conclusão.

---

## 🏆 Parte 2 — Inteligência de Priorização

### 2.1 Ranking de Sistemas

Com os dados da Parte 1, agora você constrói um ranking rigoroso.

```python
# Intervalo de confiança de Wilson (mais robusto que a taxa simples)
# Funciona melhor para amostras pequenas e evita distorções de volume
from scipy import stats

def wilson_lower_bound(positives, total, confidence=0.95):
    """
    Limite inferior do intervalo de confiança de Wilson.
    Boa prática para rankear proporções com volumes diferentes.
    """
    if total == 0:
        return 0
    z = stats.norm.ppf(1 - (1 - confidence) / 2)
    phat = positives / total
    denominator = 1 + z**2 / total
    center = phat + z**2 / (2 * total)
    margin = z * np.sqrt(phat * (1 - phat) / total + z**2 / (4 * total**2))
    return (center - margin) / denominator

# Aplicar ao dataframe de taxas
taxa_por_sistema['wilson_lb'] = taxa_por_sistema.apply(
    lambda row: wilson_lower_bound(row['total_entregues'], row['total_disparos']),
    axis=1
)

ranking_final = taxa_por_sistema.sort_values('wilson_lb', ascending=False).reset_index(drop=True)
ranking_final.index += 1
ranking_final.index.name = 'ranking'

print(ranking_final[['id_sistema_mask', 'total_disparos', 'taxa_entrega', 'wilson_lb']])
```

> 🧠 **Por que Wilson Lower Bound?**  
> Um sistema com 5 entregas em 5 tentativas (100%) não é necessariamente melhor que outro com 800 entregas em 1000 (80%). Wilson penaliza quem tem pouco volume — isso é o que você explica "matematicamente" que o desafio pede.

---

### 2.2 Algoritmo de Escolha (o coração do desafio)

Agora você cria um **score composto** para cada telefone de um cidadão.

```python
# Mapeamento: sistema → score base (derivado do ranking Wilson)
# Normalizar para escala 0-1
min_lb = ranking_final['wilson_lb'].min()
max_lb = ranking_final['wilson_lb'].max()
ranking_final['score_sistema'] = (ranking_final['wilson_lb'] - min_lb) / (max_lb - min_lb)

sistema_scores = ranking_final.set_index('id_sistema_mask')['score_sistema'].to_dict()

# Função de score por telefone
def calcular_score_telefone(row, sistema_scores, hoje=pd.Timestamp.today()):
    """
    Combina 3 dimensões em um score 0-1:
    1. Qualidade do sistema de origem     (peso 50%)
    2. Frescor do dado (data atualização) (peso 40%)
    3. DDD local (Rio de Janeiro = 21)    (peso 10%)
    """
    # Componente 1: sistema
    score_sistema = sistema_scores.get(row['id_sistema_mask'], 0)
    
    # Componente 2: frescor — decai exponencialmente
    dias = (hoje - pd.to_datetime(row['registro_data_atualizacao'])).days
    score_frescor = np.exp(-dias / 365)  # meia-vida de ~1 ano
    
    # Componente 3: DDD preferencial (ex: 21 para Rio)
    ddd = str(row.get('ddd', ''))
    score_ddd = 1.0 if ddd == '21' else 0.7
    
    # Score final ponderado
    score_final = (
        0.50 * score_sistema +
        0.40 * score_frescor +
        0.10 * score_ddd
    )
    return round(score_final, 4)

# Aplicar no dataframe de telefones
df_telefones['score'] = df_telefones.apply(
    lambda row: calcular_score_telefone(row, sistema_scores), axis=1
)

# Selecionar os 2 melhores por cidadão
top2_por_cidadao = (
    df_telefones
    .sort_values('score', ascending=False)
    .groupby('id_cidadao_mask')  # ajuste o campo
    .head(2)
    .reset_index(drop=True)
)

print(top2_por_cidadao.head(10))
```

> 💡 **Como justificar os pesos (50/40/10)?**  
> Você pode usar a correlação de Pearson entre cada variável e `entregue` para embasar os pesos. Exemplo: se `score_sistema` tem correlação 0.35 e `score_frescor` tem 0.28, distribua proporcionalmente. Mostre isso no notebook.

---

## 🧪 Parte 3 — Desenho do Experimento A/B

### 3.1 Estrutura do Experimento

```python
# ============================================================
# HIPÓTESES
# ============================================================
# H0 (nula):     O novo algoritmo NÃO melhora a taxa de entrega
#                taxa_algoritmo == taxa_atual
#
# H1 (alternativa): O novo algoritmo MELHORA a taxa de entrega
#                   taxa_algoritmo > taxa_atual   (teste unicaudal)


# ============================================================
# GRUPOS
# ============================================================
# Grupo A (controle, ~50%):  estratégia atual (aleatória / alfabética)
# Grupo B (tratamento, ~50%): algoritmo de score proposto


# ============================================================
# MÉTRICAS
# ============================================================
# Primária:   Taxa de entrega (DELIVERED / total disparos)
# Secundárias:
#   - Taxa de leitura/abertura (se disponível)
#   - Custo por mensagem entregue
#   - % de disparos desperdiçados (falhou E não havia outro número)
```

### 3.2 Cálculo do Tamanho de Amostra

```python
from scipy.stats import norm

def calcular_tamanho_amostra(taxa_base, melhoria_esperada, alpha=0.05, poder=0.80):
    """
    Calcula o n mínimo por grupo para detectar uma melhoria.
    
    Parâmetros:
    - taxa_base: taxa de entrega atual (ex: 0.65 = 65%)
    - melhoria_esperada: delta mínimo detectável (ex: 0.05 = +5pp)
    - alpha: nível de significância (padrão 5%)
    - poder: poder estatístico desejado (padrão 80%)
    """
    taxa_tratamento = taxa_base + melhoria_esperada
    z_alpha = norm.ppf(1 - alpha)        # unicaudal
    z_beta = norm.ppf(poder)
    
    p_bar = (taxa_base + taxa_tratamento) / 2
    
    n = (z_alpha + z_beta)**2 * 2 * p_bar * (1 - p_bar) / (melhoria_esperada**2)
    return int(np.ceil(n))

# Exemplo com valores razoáveis
taxa_atual = df['entregue'].mean()
print(f"Taxa atual de entrega: {taxa_atual:.1%}")

# Queremos detectar melhoria de 3 pontos percentuais
n_por_grupo = calcular_tamanho_amostra(
    taxa_base=taxa_atual,
    melhoria_esperada=0.03
)
print(f"Tamanho mínimo por grupo: {n_por_grupo:,} disparos")
print(f"Total necessário: {n_por_grupo * 2:,} disparos")

# Estimar duração com base no volume médio diário
volume_diario = 1000  # ajuste com dado real
duracao_dias = (n_por_grupo * 2) / volume_diario
print(f"Duração estimada: {duracao_dias:.0f} dias (~{duracao_dias/7:.1f} semanas)")
```

### 3.3 Análise dos Resultados (pós-experimento)

```python
from scipy.stats import chi2_contingency, proportions_ztest

def analisar_ab_test(entregues_A, total_A, entregues_B, total_B, alpha=0.05):
    """
    Testa se o grupo B (algoritmo) é significativamente melhor que A (controle).
    """
    taxa_A = entregues_A / total_A
    taxa_B = entregues_B / total_B
    lift = (taxa_B - taxa_A) / taxa_A
    
    # Teste z para proporções
    counts = np.array([entregues_B, entregues_A])
    nobs = np.array([total_B, total_A])
    z_stat, p_valor = proportions_ztest(counts, nobs, alternative='larger')
    
    print(f"Taxa Controle (A): {taxa_A:.2%}")
    print(f"Taxa Tratamento (B): {taxa_B:.2%}")
    print(f"Lift: {lift:+.1%}")
    print(f"P-valor: {p_valor:.4f}")
    
    if p_valor < alpha:
        print(f"✅ Resultado SIGNIFICATIVO — rejeitar H0 (α={alpha})")
        print("   → Implantar o algoritmo em produção.")
    else:
        print(f"❌ Resultado NÃO significativo — falhar em rejeitar H0")
        print("   → Coletar mais dados ou revisar o algoritmo.")

# Simulação de resultado (substitua pelos dados reais)
analisar_ab_test(
    entregues_A=6500, total_A=10000,
    entregues_B=7100, total_B=10000
)
```

---

## ✅ Checklist Final antes de Enviar

- [ ] Todos os notebooks rodam do zero sem erros (`Kernel > Restart & Run All`)
- [ ] README.md explica: contexto, premissas, como reproduzir, principais conclusões
- [ ] Os gráficos têm títulos, eixos rotulados e salvos em arquivo
- [ ] O viés de seleção está **explicitamente discutido**
- [ ] O algoritmo de score tem os pesos **justificados com dados**
- [ ] O experimento A/B define claramente: H0, métricas, n e duração

---

## 💡 Dicas para se Destacar como Júnior

1. **Comente o "porquê", não só o "o quê"** — explique as decisões no notebook, não apenas o código
2. **Wilson Lower Bound** em vez de taxa simples — mostra conhecimento estatístico
3. **Mostrar o viés de seleção explicitamente** — o próprio README do desafio avisa; isso é um filtro
4. **Proposta de pesos baseada em correlação** — fundamenta o algoritmo com dados, não chute
5. **Gráfico de decaimento temporal** — visual claro, impacto de negócio direto

---

*Boa sorte! 🚀*
