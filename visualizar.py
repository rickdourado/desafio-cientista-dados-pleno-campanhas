import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
from pathlib import Path

# Configuração da página: Layout full, título e ícone
st.set_page_config(
    page_title="Rio - IA de Escolha",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Injeção de CSS (Brutalist / Sharp Geometry / High Contrast)
# Quebrando o padrão "Blue Trap" e "Cliché Arredondado"
st.markdown("""
<style>
    /* Esconder branding do Streamlit e aplicar fundo Dark de alto contraste */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Tipografia forte e cores ácidas para quebrar estética corporativa */
    h1 {
        font-weight: 900 !important;
        text-transform: uppercase;
        letter-spacing: -2px;
        color: #E2FF00 !important; /* Acid Green */
        border-bottom: 4px solid #FFF;
        padding-bottom: 10px;
    }
    h2, h3 {
        font-weight: 800 !important;
        letter-spacing: -1px;
    }
    
    /* Cantos vivos em todo lugar (0px border-radius) */
    div[data-testid="stMetricValue"] {
        font-weight: 900 !important;
        color: #E2FF00 !important;
    }
    
    div.stButton > button {
        border-radius: 0px !important;
        border: 2px solid #E2FF00 !important;
        color: #000 !important;
        background-color: #E2FF00 !important;
        font-weight:bold;
        text-transform: uppercase;
        transition: all 0.2s ease;
    }
    div.stButton > button:hover {
        background-color: #000 !important;
        color: #E2FF00 !important;
    }
    
    /* Tabs com bordas afiadas */
    div[data-baseweb="tab-list"] {
        gap: 0px;
    }
    div[data-baseweb="tab"] {
        border-radius: 0px !important;
        border: 1px solid #333;
        text-transform: uppercase;
        font-weight: bold;
    }
    
    /* Cards de Informação Fixos com borda */
    .brutalist-card {
        border: 2px solid #FFF;
        padding: 1.5rem;
        background: #111;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

st.title("⚡ Motor de Escolha WhatsApp")
st.markdown("### Monitoramento e Inteligência da Prefeitura do Rio")

@st.cache_data
def load_data(path, sample_size=5000):
    try:
        # Tenta carregar com e sem a extensão .parquet
        final_path = path if Path(path).exists() else Path(f"{path}.parquet")
        df = pd.read_parquet(final_path)
        return df.head(sample_size)
    except Exception as e:
        st.error(f"⚠️ Falha no I/O de dados path={path}: {e}")
        return pd.DataFrame()

# Paths default
DATA_DIR = Path("data")
OUTPUTS_DIR = Path("outputs")

# KPIs Rápidos no Topo
colA, colB, colC = st.columns(3)
colA.metric(label="Status do Motor", value="ONLINE 🟢", delta="V1 - Wilson LB")
colB.metric(label="Decaimento Temporal", value="ATIVO", delta="Meia-Vida: 365d")
colC.metric(label="Região Foco", value="DDD 21", delta="Score Boost")

st.markdown("<hr/>", unsafe_allow_html=True)

# Abas estilizadas
tab1, tab2, tab3, tab4 = st.tabs([
    "🎲 ORIGEM DOS DADOS (SAMPLE)",
    "📈 ANÁLISE DE QUALIDADE (EDA)",
    "🏆 INTELIGÊNCIA: RANKING E WILSON",
    "📋 RELATÓRIO TÉCNICO",
])

with tab1:
    st.markdown("## RAW DATA INSPECTION")
    c1, c2 = st.columns(2)
    
    with c1:
        st.markdown("<div class='brutalist-card'><h3>📱 TELEFONES ENRIQUECIDOS</h3><p>Visão expandida da tabela dimensão.</p></div>", unsafe_allow_html=True)
        df_telefones = load_data(DATA_DIR / "whatsapp_dim_telefone_mascarado")
        if not df_telefones.empty:
            st.dataframe(df_telefones, use_container_width=True)
            
    with c2:
        st.markdown("<div class='brutalist-card'><h3>📩 HISTÓRICO DE DISPAROS</h3><p>Log bruto do integrador WABA.</p></div>", unsafe_allow_html=True)
        df_disparos = load_data(DATA_DIR / "base_disparo_mascarado")
        if not df_disparos.empty:
            st.dataframe(df_disparos, use_container_width=True)

with tab2:
    st.markdown("## QUALIDADE DAS FONTES")
    st.markdown("Avaliamos o 'calor' das plataformas: quem entrega mais e qual o impacto real da idade do dado.")
    
    col1, col2 = st.columns(2, gap="large")
    with col1:
        st.markdown("### Vantagem por Sistema (Absoluta)")
        img_path = OUTPUTS_DIR / "taxa_entrega_sistema.png"
        if img_path.exists():
            st.image(str(img_path), use_column_width=True)
            with st.expander("📝 Nota Técnica"):
                st.write("Sistemas pequenos possuem variância enorme. Média bruta não deve guiar o motor.")
        else:
            st.warning("Gráfico não encontrado.")
            
    with col2:
        st.markdown("### Decaimento Exponencial (Frescor)")
        img_path2 = OUTPUTS_DIR / "decaimento_temporal.png"
        if img_path2.exists():
            st.image(str(img_path2), use_column_width=True)
            with st.expander("📝 Nota Técnica"):
                st.write("Retenção despenca após o primeiro ano. Formulamos meia-vida com log natural p/ equilibrar priorização.")
        else:
            st.warning("Gráfico não encontrado.")

with tab3:
    st.markdown("## FUNDAÇÃO DO MOTOR DE ESCOLHA")
    st.markdown("O Ranking Definitivo à Prova de Viés de Seleção.")

    st.markdown("<div class='brutalist-card'>A aplicação da cota inferior do intervalo de confiança de Wilson pune fontes pequenas de 'sorte' e prioriza fontes volumosas estáveis.</div>", unsafe_allow_html=True)

    img_path3 = OUTPUTS_DIR / "wilson_ranking_sistemas.png"
    if img_path3.exists():
        st.image(str(img_path3), use_column_width=True)
    else:
        st.warning("Gráfico não encontrado.")

with tab4:
    relatorio_path = Path("relatorio.html")
    if relatorio_path.exists():
        html_content = relatorio_path.read_text(encoding="utf-8")
        components.html(html_content, height=900, scrolling=True)
    else:
        st.error("relatorio.html não encontrado. Gere-o primeiro.")

# Sidebar estilizada
with st.sidebar:
    st.markdown("### ⚠️ COMANDOS")
    st.markdown("Motor WABA Mock")
    if st.button("RELOAD PIPELINE"):
        st.cache_data.clear()
        st.rerun()
    
    st.markdown("---")
    st.info("Interface renderizada seguindo filosofia **Brutalist / Functional** (evitando Glassmorphism genérico e templates arredondados padrão).")
