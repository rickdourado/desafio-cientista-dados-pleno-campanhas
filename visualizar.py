import streamlit as st
import pandas as pd
from pathlib import Path

# Configuração da página
st.set_page_config(page_title="Visualizador de Dados Whatsapp", layout="wide")

st.title("🔍 Visualizador de Dados - Prefeitura do Rio")
st.markdown("Visualizador rápido dos arquivos Parquet gerados e extraídos para o Desafio.")

@st.cache_data
def load_data(path, sample_size=5000):
    try:
        df = pd.read_parquet(path)
        return df.head(sample_size)
    except Exception as e:
        st.error(f"Erro ao ler os dados de {path}: {e}")
        return pd.DataFrame()

# Paths (apontando localmente considerando o run em /home/.../desafio...)
DATA_DIR = Path("data")
OUTPUTS_DIR = Path("outputs")

# Abas
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📌 Dimensão Telefones", 
    "📩 Histórico de Disparos",
    "📊 Parte 1: Taxa de Entrega",
    "📉 Parte 1: Decaimento",
    "🏆 Parte 2: Ranking Wilson"
])

with tab1:
    st.header("Tabela: dim_telefone_mascarado_public")
    df_telefones = load_data(DATA_DIR / "dim_telefone_mascarado_public")
    if not df_telefones.empty:
        st.write(f"Mostrando primeira amostra de {len(df_telefones)} linhas:")
        st.dataframe(df_telefones)
        
with tab2:
    st.header("Tabela: base_disparo_mascarado_public")
    df_disparos = load_data(DATA_DIR / "base_disparo_mascarado_public")
    if not df_disparos.empty:
        st.write(f"Mostrando primeira amostra de {len(df_disparos)} linhas:")
        st.dataframe(df_disparos)

with tab3:
    st.header("Parte 1: Taxa de Entrega por Sistema")
    st.image(str(OUTPUTS_DIR / "taxa_entrega_sistema.png"), use_column_width=True)
    st.markdown("Mostra a proporção bruta de sucesso baseada na origem dos telefones. Sistemas pequenos podem mascarar performance ideal.")

with tab4:
    st.header("Parte 1: Decaimento Temporal")
    st.image(str(OUTPUTS_DIR / "decaimento_temporal.png"), use_column_width=True)
    st.markdown("Exibe como um número de telefone estagnado/velho perde drasticamente a viabilidade de disparo via WhatsApp.")

with tab5:
    st.header("Parte 2: Ponderação e Ranking Seguro (Wilson Lower Bound)")
    st.image(str(OUTPUTS_DIR / "wilson_ranking_sistemas.png"), use_column_width=True)
    st.markdown("Aplica punição para sistemas com baixa minutagem/amostra e exibe o nível conservador de sucesso das campanhas. Esse ranking é a fundação da Inteligência de Escolha.")

st.sidebar.markdown("### Atalhos")
st.sidebar.info("Estes DataFrames contêm todas as colunas complexas, como `telefone_aparicoes` (arrays). Em Streamlit as colunas complexas costumam ser renderizadas como string JSON ou objetos para facilitar visualização.")
