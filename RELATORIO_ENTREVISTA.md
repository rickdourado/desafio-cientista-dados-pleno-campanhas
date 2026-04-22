# Relatório de Decisões Técnicas: Inteligência de Escolha WhatsApp

Este documento sumariza as principais premissas assumidas, os trade-offs considerados e as escolhas de arquitetura matemática adotadas na resolução do Desafio Técnico de Priorização de Contatos do WhatsApp para a Prefeitura do Rio. Foi redigido para apoiar a defesa do case durante entrevistas.

---

## 1. Tratamento e Modelagem dos Dados (A Base)
A exploração inicial (`01_eda_qualidade.ipynb`) revelou o primeiro desafio estrutural: a dimensionalidade da tabela de telefones, que possuía históricos de origens agrupados num array.

**Decisão Adotada:** 
Optei por um `explode` da coluna `telefone_aparicoes` via manipulação vetorial (`pandas`), convertendo os metadados JSON internos diretamente em novas features num data frame em formato *long*.
- **Por que não iterar/for-loops?** Na volumetria da prefeitura (milhões de cidadãos operando via Kafka/Airflow), loops nativos do Python quebram. O *Explode* atrelado ao *merge* do Pandas (inner join via hash do telefone com a base de disparos) é passível de portabilidade direta para uso de PySpark (caso seja big data distribuído). Foi priorizada a performance em processamento batch.

---

## 2. Abordagem Analítica: Wilson Lower Bound vs. Média Bruta
O `Desafio.md` alertou explicitamente sobre o **Viés de Seleção**: uma base pequena da SME poderia ter 10 disparos e 10 acertos (100%), enquanto a plataforma do IPTU com 5 milhões de contatos bate em 30%. O Motor de Regras não poderia considerar a base SME infinitamente melhor baseando-se em média bruta.

**Decisão Adotada:**
Ao invés de aplicar thresholds cruéis ("ignorar bases com < 1000 envios"), implementei a fórmula estatística **Wilson Lower Bound** (Score de Wilson) (`src/scoring.py`).
- **Como funciona:** O algoritmo estabelece para cada sistema o "limite inferior do seu intervalo de confiança a 95%". A SME com seus (10/10) sofrerá uma margem de erro massiva na fórmula devido ao baixo N, jogando seu "score de confiança real" para baixo (~60%). O sistema do IPTU que disparou (30/100) sofrerá pouca margem devido ao altíssimo N. 
- **Impacto para a Prefeitura:** Proteção da operação contra anomalias sazonais de sub-sistemas, priorizando de forma contundente bancos que têm volume estático e escalável e confiabilidade estressada sob rigor.

---

## 3. Frescor do Dado (Decaimento Exponencial)
Um telefone captado ontem pelo cadastro de Saúde é imensamente superior ao telefone captado em 2020 para cobrança de ISS. Como quantificar a velhice do dado analiticamente?

**Decisão Adotada:**
Não criei *ranges* fixos ("se menor que 30 dias ganha nota 1"). Fixei uma fórmula contínua matemática de **Decaimento Exponencial Temporal**.
- **Metodologia:** Usando uma função $e^{(-dias/365)}$, adotei uma *meia-vida* de 1 ano. Ou seja, se o telefone tem menos de uma semana, seu peso é 1.0 (pontuação máxima de tempo). Após 12 meses (365 dias), a multiplicação decodifica uma retenção de ~0.36. 
- **Por quê?** Isso evita que números adicionados no mesmo ano sofram perdas de qualidade bruscas ou escadas desiguais, mantendo um gradiente suave.

---

## 4. Unificação Ponderada do Algoritmo de Priorização
A função mestre combina o sistema, a região e o tempo. As ponderações adotadas foram ($50\%$ Sistema, $40\%$ Tempo, e $10\%$ DDD preferencial *21*). Com a junção feita numericamente de 0 a 1, aplico agrupamento sob a entidade chave (`Cidadão_CPF`) filtrando um Top 2 (`.head(2)`).

**Por que não usar um modelo de Machine Learning Complexo (XGBoost/LightGBM)?**
- Interpretatividade e Velocidade. Sendo o motor parte do caminho quente na volumetria de mensagens da Prefeitura, usar heurística estatística de performance garantida (O(1) após caches de score) é mais seguro economicamente em nuvem do que carregar um peso de inferência de Random Forest massivo para toda a população do Rio na fase semente.

---

## 5. Experimento de Negócio (O Desafio A/B)
A validação de que nosso ranqueamento é melhor que sorteio aleatório requer precisão, pois falhar em testar consome verbo público. Em `03_experimento_ab.ipynb`, detalhei uma premissa real.

**Premissas Adotadas:**
1. Realização de um "Z-test de Proporções" utilizando $p = 0.26$ de conversão basal.
2. Busquei provar se nosso algoritmo traz pelo menos +4% absolutos de ganho (MDE) em taxa de entrega de WhatsApp.
3. Isso demandou *4100 cidadãos únicos em amostra*. A recomendação arquitetada foi ligar o teste numa janela curta de dias sem contaminar eventos diferentes (apenas para avisos do mesmo domínio e.g. "Dengue"). 

A premissa foca em isolar a causa e provar ganho para *reduzir custos nas contas mensais das provedoras de envio/WABA*.
