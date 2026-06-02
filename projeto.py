import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from pathlib import Path
import json
import os

from utils.data_loader import BASE_DIR, carregar_dados_docentes, carregar_dados_grupos_pesquisa, carregar_dados_apq, carregar_dados_icti, carregar_dados_bolsistas

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Observatório PROPEGI", layout="wide", initial_sidebar_state="expanded")

# --- PALETA DE CORES MANDATÓRIA ---
COLORS = {
    "Ciano": "#00FFFF",
    "Coral": "#FF5765",
    "Amarelo": "#FFFE91",
    "Roxo": "#8E8DE1",
    "Verde Limao": "#7AC46D",
    "Gelo": "#F8F8FF",
    "Fundo": "#0E1117",
    "Card": "#1E2130",
    "Texto": "#F5F5F5"
}

STRICTO = {
    'Homens': '#00FFFF',      
    'Mulheres': '#FF5765',    
    'Titulado': '#8E8DE1',    
    'Desistente': '#FFFE91',   
    'Unidade_1': '#26DFD0',    
    'Unidade_2': '#5CE0D8',    
    'Unidade_3': '#FFD700'     
}

# --- CSS PERSONALIZADO ---
st.markdown(f"""
    <style>
    [data-testid="stAppViewContainer"] {{ background-color: {COLORS['Fundo']} !important; }}
    [data-testid="stHeader"] {{ background: rgba(0,0,0,0); }}
    [data-testid="stSidebar"] > div, section[data-testid="stSidebar"] {{
        background-color: {COLORS['Card']} !important;
        color: {COLORS['Texto']} !important;
    }}
    [data-testid="stSidebar"] label, [data-testid="stSidebar"] .stRadio, [data-testid="stSidebar"] .stSelectbox {{
        color: {COLORS['Texto']} !important;
    }}
    [data-testid="stMain"] {{ background-color: transparent !important; }}
    [data-testid="stPlotlyChart"] .js-plotly-plot, .plotly, .js-plotly-plot {{
        background: transparent !important;
    }}
    .kpi-card {{
        background-color: {COLORS['Card']};
        padding: 20px;
        min-height: 150px;
        height: 150px;
        box-sizing: border-box;
        border-radius: 10px;
        border-top: 4px solid;
        text-align: center;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        margin-bottom: 20px;
    }}
    .kpi-value {{
        min-height: 42px;
        font-size: 32px;
        font-weight: 800;
        color: #FFFFFF;
        line-height: 1.05;
        letter-spacing: -0.03em;
        text-shadow: 0 2px 10px rgba(0, 0, 0, 0.28);
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 6px;
        white-space: nowrap;
    }}
    .kpi-label {{
        font-size: 13px;
        color: #D7DCEA;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        line-height: 1.2;
        min-height: 50px;
        display: flex;
        align-items: center;
        justify-content: center;
        text-align: center;
        text-shadow: 0 1px 0 rgba(0, 0, 0, 0.25);
    }}
    .kpi-delta {{
        min-height: 20px;
        font-size: 14px;
        font-weight: 700;
        line-height: 1;
        color: #21c55d;
        display: flex;
        align-items: center;
        justify-content: center;
    }}
    .kpi-note {{
        font-size: 11px;
        color: #9AA3AA;
        font-weight: 600;
        margin-top: 4px;
        line-height: 1;
    }}
    h1, h2, h3, h4, h5, h6, p, label, span, [data-testid="stMarkdownContainer"] {{
        color: #FFFFFF !important;
    }}
    div[role="radiogroup"] label p {{
        color: #FFFFFF !important;
    }}
    </style>
""", unsafe_allow_html=True)

# --- FUNÇÕES PARA CARDS E TÍTULOS ---
def kpi_card(label, value, color):
    st.markdown(f"""
        <div class="kpi-card" style="border-top-color: {color};">
            <div class="kpi-label">{label}</div>
            <div class="kpi-value">{value}</div>
            <div class="kpi-delta">&nbsp;</div>
        </div>
    """, unsafe_allow_html=True)

def kpi_card_delta(label, value, delta, color):
    delta_color = "green" if delta >= 0 else "red"
    arrow = "↑" if delta > 0 else ("↓" if delta < 0 else "-")
    note = "Ano anterior"
    st.markdown(f"""
        <div class="kpi-card" style="border-top-color: {color};">
            <div class="kpi-label">{label}</div>
            <div class="kpi-value">{value}</div>
            <div class="kpi-delta" style="color: {delta_color};">{arrow} {abs(delta):.1f}%</div>
            <div class="kpi-note">{note}</div>
        </div>
    """, unsafe_allow_html=True)

def chart_title(text):
    st.markdown(f"<div style='font-size:16px;font-weight:700;line-height:1.15;min-height:64px;margin:0 0 8px 0;display:flex;align-items:flex-start;padding-top:2px;max-width:100%;'>{text}</div>", unsafe_allow_html=True)

def chart_title_strong(text):
    st.markdown(f"<div style='font-size:13px;font-weight:800;line-height:1.2;min-height:50px;margin:0 0 10px 0;display:flex;align-items:center;justify-content:center;letter-spacing:0.06em;text-transform:uppercase;color:#D7DCEA;max-width:100%;text-shadow:0 1px 0 rgba(0, 0, 0, 0.25);'>{text}</div>", unsafe_allow_html=True)

@st.cache_data(show_spinner=False)
def load_inovacao_base_data():
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(base_dir, "data", "processed", "inovacao", "inovacao.csv")
    
    # DEBUG: Verifique se o arquivo existe
    if not os.path.exists(csv_path):
        st.error(f"Erro: Arquivo não encontrado em: {csv_path}")
        return pd.DataFrame()
        
    try:
        df = pd.read_csv(csv_path)
        # Se os dados carregarem, mostramos uma notificação de sucesso temporária
        # st.sidebar.success("Dados carregados com sucesso!") 
        return df
    except Exception as e:
        st.error(f"Erro ao ler CSV: {e}")
        return pd.DataFrame()


@st.cache_data(show_spinner=False)
def load_pi_data():
    import pandas as pd
    import os
    diretorio_atual = os.path.dirname(os.path.abspath(__file__))
    caminho_csv = os.path.join(diretorio_atual, "data", "processed", "desenvolvimento-tecnologico", "propriedade_intelectual_consolidado.csv")
    
    if os.path.exists(caminho_csv):
        df = pd.read_csv(caminho_csv)
        # Consolida as duas colunas de data (Patentes e Softwares) para extrair o ano
        if 'Data de deposito' in df.columns and 'Data' in df.columns:
            df['Ano_PI'] = pd.to_datetime(df['Data de deposito'].combine_first(df['Data']), errors='coerce').dt.year
        elif 'Data de deposito' in df.columns:
            df['Ano_PI'] = pd.to_datetime(df['Data de deposito'], errors='coerce').dt.year
        elif 'Data' in df.columns:
            df['Ano_PI'] = pd.to_datetime(df['Data'], errors='coerce').dt.year
        else:
            df['Ano_PI'] = pd.NA
        return df
    return pd.DataFrame()

def format_brl(value):
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

@st.cache_data(show_spinner=False)
def load_patentes_por_ano():
    csv_path = Path(__file__).parent / "dados com etl" / "data" / "processed" / "inovacao" / "propriedade_intelectual.csv"
    if not csv_path.exists(): return pd.DataFrame(columns=["Ano", "Patentes"])
    try:
        df = pd.read_csv(csv_path)
        col_data = next((c for c in df.columns if "data" in str(c).lower() and "deposit" in str(c).lower()), None)
        if not col_data: return pd.DataFrame(columns=["Ano", "Patentes"])
        anos = pd.to_datetime(df[col_data].astype(str).str.strip(), dayfirst=True, errors="coerce").dt.year
        df_anos = pd.DataFrame({"Ano": anos}).dropna()
        if df_anos.empty: return pd.DataFrame(columns=["Ano", "Patentes"])
        df_anos["Ano"] = df_anos["Ano"].astype(int)
        return df_anos.groupby("Ano", as_index=False).size().rename(columns={"size": "Patentes"}).sort_values("Ano")
    except:
        return pd.DataFrame(columns=["Ano", "Patentes"])


@st.cache_data(show_spinner=False)
def load_dt_data():
    import os
    import json
    import pandas as pd
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = None
    
    for root, dirs, files in os.walk(base_dir):
        if "dados.json" in files:
            json_path = os.path.join(root, "dados.json")
            break
            
    if json_path is None:
        return pd.DataFrame(columns=["Data", "Região", "Vendedor", "Produto", "Quantidade", "ValorTotal", "Mês"])

    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        df = pd.DataFrame(data)
        
        if not df.empty:
            if "Data" in df.columns:
                df["Data"] = pd.to_datetime(df["Data"], errors="coerce")
                df["Mês"] = df["Data"].dt.to_period("M").astype(str)
            if "Quantidade" in df.columns:
                df["Quantidade"] = pd.to_numeric(df["Quantidade"], errors="coerce").fillna(0)
            if "ValorTotal" in df.columns:
                df["ValorTotal"] = pd.to_numeric(df["ValorTotal"], errors="coerce").fillna(0)
        
        return df
    except Exception as e:
        return pd.DataFrame(columns=["Data", "Região", "Vendedor", "Produto", "Quantidade", "ValorTotal", "Mês"])

# MUDANÇA 1: Caminho Relativo Dinâmico (Funciona no PC e no GitHub)
@st.cache_data(ttl=0, show_spinner=False)
def load_pos_graduacao_data():
    import os
    
    # Pega a pasta exata onde o projeto.py está rodando
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Constrói o caminho relativo até a pasta dos CSVs
    lato_path = os.path.join(BASE_DIR, "data", "processed", "pos-graduacao", "lato_sensu_processado.csv")
    stricto_path = os.path.join(BASE_DIR, "data", "processed", "pos-graduacao", "stricto_sensu_processado.csv")
   
   
    # Tratamento Stricto Sensu
    stricto = pd.DataFrame()
    if os.path.exists(stricto_path):
        try:
            df_st = pd.read_csv(stricto_path)
            # Filtra apenas as linhas do censo geral e preenche as células mescladas do Excel
            df_censo = df_st[df_st['ABA_ORIGEM'].astype(str).str.contains('Censo', na=False, case=False)].copy()
            df_censo['PROGRAMA'] = df_censo['PROGRAMA'].ffill()
            df_censo['SITUAÇÃO'] = df_censo['SITUAÇÃO'].replace({'DOUTORADO': None, 'MESTRADO': None, 'TOTAL': None}).ffill()
            
            # Converte os números
            for col in ['MASCULINO', 'FEMININO', 'TOTAL']:
                df_censo[col] = pd.to_numeric(df_censo[col], errors='coerce').fillna(0)
            
            # Limpa o texto
            df_censo['PROGRAMA'] = df_censo['PROGRAMA'].astype(str).str.strip()
            df_censo['NIVEL'] = df_censo['NIVEL'].astype(str).str.strip().str.title()
            df_censo['SITUAÇÃO'] = df_censo['SITUAÇÃO'].astype(str).str.strip().str.title()
            
            stricto = df_censo
        except Exception as e:
            st.sidebar.error(f"Erro ao processar Stricto: {e}")

    # Tratamento Lato Sensu 
    lato = pd.DataFrame()
    if os.path.exists(lato_path):
        try:
            lato = pd.read_csv(lato_path)
        except:
            pass

    return {'stricto': stricto, 'lato': lato}


# --- SIDEBAR (NAVEGAÇÃO) ---
with st.sidebar:
    st.image("logo-upe.png", width=150)
    st.title("Menu de Navegação")
    tela = st.radio("Selecione a Tela:", ["Visão Geral", "Pesquisa", "Inovação", "Desenvolvimento Tecnológico", "Pós-Graduação"])
    st.info("Painel de Gestão Estratégica PROPEGI")

# --- FILTRO GLOBAL ---
col_img, col_titulo = st.columns([1, 10])
with col_img:
    st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)
    st.image("propegi.png", width=1000)
with col_titulo:
    st.title(tela)
col_filter1, col_filter2 = st.columns([1, 3])
with col_filter1:
    ano_selected = st.selectbox("📅 FILTRO ANO", [2026, 2025, 2024, 2023, 2022], index=0)

# =========================================================
# TELA 1: VISÃO GERAL (ALTA GESTÃO)
# =========================================================


if tela == "Visão Geral":
    st.header("Visão Geral do Observatório")
    
    # 1. Carregamento Seguro dos Dados
    df_visao = load_inovacao_base_data().copy()
    df_icti = carregar_dados_icti()
    
    # Filtrar pelo ano selecionado para os Cards
    ano_alvo = int(ano_selected)
    df_visao_ano = pd.DataFrame()
    if not df_visao.empty and 'Ano' in df_visao.columns:
        df_visao['Ano'] = pd.to_numeric(df_visao['Ano'], errors='coerce')
        df_visao_ano = df_visao[df_visao['Ano'] == ano_alvo]
        
    # --- 1. CARDS (KPIs) ---
    total_fomento = float(df_visao_ano["Receita"].sum()) if not df_visao_ano.empty and "Receita" in df_visao_ano.columns else 0
    total_bolsas_inov = int(df_visao_ano["Total de Bolsas"].sum()) if not df_visao_ano.empty and "Total de Bolsas" in df_visao_ano.columns else 0
    
    # Pega as bolsas do ICTI/Pesquisa para somar o total global
    total_bolsas_icti = 0
    if not df_icti.empty and 'ANO_ARQUIVO' in df_icti.columns:
        total_bolsas_icti = len(df_icti[df_icti['ANO_ARQUIVO'].astype(str) == str(ano_alvo)])
        
    total_bolsas = total_bolsas_inov + total_bolsas_icti
    total_entregas = len(df_visao_ano) if not df_visao_ano.empty else 0

    col1, col2, col3 = st.columns(3)
    with col1: kpi_card("Total Fomento Captado (Ano)", format_brl(total_fomento), COLORS["Ciano"])
    with col2: kpi_card("Total Bolsas Ofertadas (Ano)", str(total_bolsas), COLORS["Coral"])
    with col3: kpi_card("Entregas Científicas (Ano)", str(total_entregas), COLORS["Amarelo"])

    st.markdown("---")

    # --- 2. PÓS E PESQUISA ---
    st.subheader("Relação de Bolsistas IC (Últimos 4 anos)")
    
    if not df_icti.empty and 'ANO_ARQUIVO' in df_icti.columns:
        # Agrupa a quantidade de bolsistas por ano (últimos 4 anos em relação ao selecionado)
        df_evolucao = df_icti.groupby('ANO_ARQUIVO').size().reset_index(name='Bolsistas IC')
        df_evolucao['ANO_ARQUIVO'] = pd.to_numeric(df_evolucao['ANO_ARQUIVO'], errors='coerce')
        df_evolucao = df_evolucao[(df_evolucao['ANO_ARQUIVO'] <= ano_alvo) & (df_evolucao['ANO_ARQUIVO'] > (ano_alvo - 4))]
        
        if not df_evolucao.empty:
            fig_pos = px.bar(df_evolucao, x='ANO_ARQUIVO', y='Bolsistas IC', text='Bolsistas IC',
                             title=f"Evolução de Bolsistas IC ({ano_alvo-3} a {ano_alvo})",
                             template="plotly_dark", color_discrete_sequence=[COLORS["Roxo"]])
            fig_pos.update_traces(textposition='outside')
            fig_pos.update_layout(height=450, margin=dict(t=30, b=20, l=10, r=10), xaxis_title="Ano", yaxis_title="Quantidade de Bolsistas")
            fig_pos.update_xaxes(type='category')
            st.plotly_chart(fig_pos, use_container_width=True)
        else:
            st.info(f"Sem dados de bolsistas para o período de {ano_alvo-3} a {ano_alvo}.")
    else:
        st.info("Dados de bolsistas não encontrados.")

    st.markdown("---")

    # --- 3. INOVAÇÃO E DESENVOLVIMENTO TECNOLÓGICO (MAPAS) ---
    st.subheader("Inovação e Desenvolvimento Tecnológico")
    col_map1, col_map2 = st.columns(2)
    
    with col_map1:
        chart_title("Projetos por Cidade (Acumulado)")
        if not df_visao.empty and "Cidade" in df_visao.columns:
            df_cidade = df_visao.groupby("Cidade").size().reset_index(name="Projetos").sort_values("Projetos", ascending=True)
            fig_cidade = px.bar(df_cidade.tail(15), x="Projetos", y="Cidade", orientation="h", 
                                template="plotly_dark", color_discrete_sequence=[COLORS["Verde Limao"]])
            fig_cidade.update_layout(height=400, margin=dict(t=20, b=20, l=10, r=10), yaxis_title="", xaxis_title="Qtd Projetos")
            st.plotly_chart(fig_cidade, use_container_width=True)
        else:
            st.info("Dados de Cidade não disponíveis.")
            
    with col_map2:
        chart_title("Projetos por Região (Acumulado)")
        if not df_visao.empty and "Região" in df_visao.columns:
            df_regiao = df_visao.groupby("Região").size().reset_index(name="Projetos")
            fig_regiao = px.pie(df_regiao, values="Projetos", names="Região", hole=0.5, 
                                template="plotly_dark", color_discrete_sequence=[COLORS["Ciano"], COLORS["Amarelo"], COLORS["Coral"]])
            fig_regiao.update_layout(height=400, margin=dict(t=20, b=20, l=10, r=10))
            st.plotly_chart(fig_regiao, use_container_width=True)
        else:
            st.info("Dados de Região não disponíveis.")

    # --- 4. MAPA INTERATIVO GEOGRÁFICO ---
    st.markdown("---")
    st.subheader("Distribuição Geográfica dos Projetos")
    
    if not df_visao.empty and "Cidade" in df_visao.columns:
        # Dicionário de coordenadas (Latitude e Longitude)
        # Como o CSV contém os nomes das cidades (ex: "Recife - PE"), precisamos mapeá-los.
        # Adicione outras cidades aqui se necessário no futuro.
        coord_cidades = {
            "Recife - PE": {"lat": -8.0476, "lon": -34.8770},
            "Caruaru - PE": {"lat": -8.2833, "lon": -35.9761},
            "Garanhuns - PE": {"lat": -8.8828, "lon": -36.4969},
            "Petrolina - PE": {"lat": -9.3833, "lon": -40.5000},
            "Nazaré da Mata - PE": {"lat": -7.7414, "lon": -35.2269},
            "Serra Talhada - PE": {"lat": -7.9919, "lon": -38.2972},
            "Salgueiro - PE": {"lat": -8.0744, "lon": -39.1192},
            "Arcoverde - PE": {"lat": -8.4181, "lon": -37.0542},
            "Palmares - PE": {"lat": -8.6833, "lon": -35.5917},
            "Goiana - PE": {"lat": -7.5603, "lon": -35.0044},
            "Camaragibe - PE": {"lat": -8.0222, "lon": -34.9786},
            "Jaboatão dos Guararapes - PE": {"lat": -8.1139, "lon": -35.0153},
            "São Paulo - SP": {"lat": -23.5505, "lon": -46.6333},
            "Campinas - SP": {"lat": -22.9099, "lon": -47.0626},
            "Rio de Janeiro - RJ": {"lat": -22.9068, "lon": -43.1729},
            "Belo Horizonte - MG": {"lat": -19.9167, "lon": -43.9345},
            "Brasília - DF": {"lat": -15.7942, "lon": -47.8822}
        }
        
        # Agrupa os projetos por cidade
        df_mapa = df_visao.groupby("Cidade").size().reset_index(name="Qtd Projetos")
        
        # Aplica as coordenadas com base no dicionário
        df_mapa["lat"] = df_mapa["Cidade"].apply(lambda x: coord_cidades.get(x, {}).get("lat"))
        df_mapa["lon"] = df_mapa["Cidade"].apply(lambda x: coord_cidades.get(x, {}).get("lon"))
        
        # Remove cidades que não estão no dicionário
        df_mapa_plot = df_mapa.dropna(subset=["lat", "lon"])
        
        if not df_mapa_plot.empty:
            fig_mapa = px.scatter_mapbox(
                df_mapa_plot, 
                lat="lat", 
                lon="lon", 
                hover_name="Cidade", 
                hover_data={"lat": False, "lon": False, "Qtd Projetos": True},
                size="Qtd Projetos",
                size_max=50,
                color_discrete_sequence=[COLORS["Ciano"]], 
                zoom=5, # Zoom inicial ajustado para o Nordeste
                center={"lat": -8.0476, "lon": -34.8770}, # Centralizado em Pernambuco
                mapbox_style="carto-positron"
                #mapbox_style="carto-darkmatter"
                #mapbox_style="open-street-map"
            )
            fig_mapa.update_layout(margin={"r":0,"t":0,"l":0,"b":0}, height=500)
            st.plotly_chart(fig_mapa, use_container_width=True)
        else:
            st.info("Nenhuma cidade do arquivo CSV com coordenadas mapeadas foi encontrada para o ano filtrado.")
# =========================================================
# TELA 2: COORDENAÇÃO DE PESQUISA
# =========================================================
elif tela == "Pesquisa":
    # 1. Carregamento dos dados gerais (Sem filtro ainda)
    df_docentes_all = carregar_dados_docentes()
    df_gp_all = carregar_dados_grupos_pesquisa()
    df_apq_all = carregar_dados_apq()
    df_icti_all = carregar_dados_icti()
    df_bolsistas_all = carregar_dados_bolsistas()

    # 2. Definição do ano atual e ano anterior para o cálculo dos Deltas
    ano_atual = int(ano_selected)
    ano_anterior = ano_atual - 1

    # 3. Criar os DataFrames filtrados por ANO ATUAL
    if not df_bolsistas_all.empty and 'ANO_REFERENCIA' in df_bolsistas_all.columns:
        df_bolsistas = df_bolsistas_all[df_bolsistas_all['ANO_REFERENCIA'].astype(str) == str(ano_atual)]
    else:
        df_bolsistas = df_bolsistas_all
        
    if not df_icti_all.empty and 'ANO_ARQUIVO' in df_icti_all.columns:
         df_icti = df_icti_all[df_icti_all['ANO_ARQUIVO'].astype(str) == str(ano_atual)]
    else:
         df_icti = df_icti_all

    # 4. Criar os DataFrames filtrados por ANO ANTERIOR (Para o cálculo das setinhas verdes/vermelhas)
    if not df_bolsistas_all.empty and 'ANO_REFERENCIA' in df_bolsistas_all.columns:
        df_bolsistas_ant = df_bolsistas_all[df_bolsistas_all['ANO_REFERENCIA'].astype(str) == str(ano_anterior)]
    else:
        df_bolsistas_ant = pd.DataFrame()
        
    if not df_icti_all.empty and 'ANO_ARQUIVO' in df_icti_all.columns:
         df_icti_ant = df_icti_all[df_icti_all['ANO_ARQUIVO'].astype(str) == str(ano_anterior)]
    else:
         df_icti_ant = pd.DataFrame()

    df_docentes = df_docentes_all
    df_gp = df_gp_all
    df_apq = df_apq_all

    # 5. Helpers inteligentes para encontrar os nomes reais das colunas
    col_prog = next((c for c in df_icti_all.columns if 'PROGRAMA' in c or 'MODALIDADE' in c), 'PROGRAMA') if not df_icti_all.empty else 'PROGRAMA'
    col_vinc = next((c for c in df_icti_all.columns if 'VÍNC' in c or 'VINC' in c), 'VINCULO') if not df_icti_all.empty else 'VINCULO'
    col_cotista = next((c for c in df_icti_all.columns if 'COTISTA' in c), 'COTISTA') if not df_icti_all.empty else 'COTISTA'
    col_discente = next((c for c in df_icti_all.columns if 'DISCENTE' in c), 'DISCENTE') if not df_icti_all.empty else 'DISCENTE'
    col_agencia = next((c for c in df_bolsistas_all.columns if 'AGENCIA' in c), 'AGENCIA_FOMENTO') if not df_bolsistas_all.empty else 'AGENCIA_FOMENTO'

    # Função matemática do Delta (%)
    def calc_delta(atual, anterior):
        if anterior == 0:
            return 100.0 if atual > 0 else 0.0
        return ((atual - anterior) / anterior) * 100.0

    # 6. Cálculo dos Totais do ANO ATUAL
    total_pibic = df_icti[df_icti[col_prog].astype(str).str.contains('PIBIC', na=False) & ~df_icti[col_prog].astype(str).str.contains('EM', na=False)].shape[0] if not df_icti.empty and col_prog in df_icti.columns else 0
    total_pibiti = df_icti[df_icti[col_prog].astype(str).str.contains('PIBIT', na=False)].shape[0] if not df_icti.empty and col_prog in df_icti.columns else 0
    total_pibic_em = df_icti[df_icti[col_prog].astype(str).str.contains('EM', na=False)].shape[0] if not df_icti.empty and col_prog in df_icti.columns else 0
    
    total_estudantes = df_icti[col_discente].nunique() if not df_icti.empty and col_discente in df_icti.columns else 0
    total_cnpq = df_bolsistas[df_bolsistas[col_agencia].astype(str).str.contains('CNPQ', na=False)].shape[0] if not df_bolsistas.empty and col_agencia in df_bolsistas.columns else 0
    total_facepe = df_bolsistas[df_bolsistas[col_agencia].astype(str).str.contains('FACEPE', na=False)].shape[0] if not df_bolsistas.empty and col_agencia in df_bolsistas.columns else 0

    total_docentes = df_docentes.shape[0] if not df_docentes.empty else 0
    total_gp = df_gp['NOME DO GRUPO'].nunique() if not df_gp.empty and 'NOME DO GRUPO' in df_gp.columns else df_gp.shape[0]

    # 7. Cálculo dos Totais do ANO ANTERIOR
    ant_pibic = df_icti_ant[df_icti_ant[col_prog].astype(str).str.contains('PIBIC', na=False) & ~df_icti_ant[col_prog].astype(str).str.contains('EM', na=False)].shape[0] if not df_icti_ant.empty and col_prog in df_icti_ant.columns else 0
    ant_pibiti = df_icti_ant[df_icti_ant[col_prog].astype(str).str.contains('PIBIT', na=False)].shape[0] if not df_icti_ant.empty and col_prog in df_icti_ant.columns else 0
    ant_pibic_em = df_icti_ant[df_icti_ant[col_prog].astype(str).str.contains('EM', na=False)].shape[0] if not df_icti_ant.empty and col_prog in df_icti_ant.columns else 0
    
    ant_estudantes = df_icti_ant[col_discente].nunique() if not df_icti_ant.empty and col_discente in df_icti_ant.columns else 0
    ant_cnpq = df_bolsistas_ant[df_bolsistas_ant[col_agencia].astype(str).str.contains('CNPQ', na=False)].shape[0] if not df_bolsistas_ant.empty and col_agencia in df_bolsistas_ant.columns else 0
    ant_facepe = df_bolsistas_ant[df_bolsistas_ant[col_agencia].astype(str).str.contains('FACEPE', na=False)].shape[0] if not df_bolsistas_ant.empty and col_agencia in df_bolsistas_ant.columns else 0

    # 8. Renderização dos KPIs
    col1, col2, col3, col4 = st.columns(4)
    with col1: kpi_card_delta("TOTAL DE BOLSAS PIBIC", str(total_pibic), calc_delta(total_pibic, ant_pibic), COLORS["Ciano"])
    with col2: kpi_card_delta("TOTAL DE BOLSAS PIBITI", str(total_pibiti), calc_delta(total_pibiti, ant_pibiti), COLORS["Coral"])
    with col3: kpi_card_delta("TOTAL DE BOLSAS PIBIC-EM", str(total_pibic_em), calc_delta(total_pibic_em, ant_pibic_em), COLORS["Amarelo"])
    with col4: kpi_card_delta("GRUPOS DE PESQUISA", str(total_gp), 0.0, COLORS["Verde Limao"]) # GP geralmente não é segmentado por ano no ETL

    st.markdown("<br>", unsafe_allow_html=True)
    col_k1, col_k2, col_k3, col_k4 = st.columns(4)
    with col_k1:
        kpi_card("TOTAL DE DOCENTES PESQUISADORES", str(total_docentes), COLORS["Roxo"])
    with col_k2:
        kpi_card_delta("TOTAL DE ESTUDANTES PESQUISADORES", str(total_estudantes), calc_delta(total_estudantes, ant_estudantes), COLORS["Ciano"])
    with col_k3:
        kpi_card_delta("TOTAL BOLSISTAS PRODUTIVIDADE CNPQ", str(total_cnpq), calc_delta(total_cnpq, ant_cnpq), COLORS["Coral"])
    with col_k4:
        kpi_card_delta("TOTAL BOLSISTAS PRODUTIVIDADE FACEPE", str(total_facepe), calc_delta(total_facepe, ant_facepe), COLORS["Amarelo"])

    # 9. Gráficos de Rosca
    col_d1, col_d2, col_d3, col_d4 = st.columns(4)
    chart_height = 160
    
    # Tratamento seguro caso a coluna 'COTISTA' não exista naquele ano específico
    tem_cotista = col_cotista in df_icti.columns if not df_icti.empty else False

    with col_d1:
        if not df_icti.empty and col_vinc in df_icti.columns:
            df_vol = df_icti[df_icti[col_vinc].astype(str).str.contains('VOLUNT', na=False)]
            cot_vol = df_vol[df_vol[col_cotista].astype(str).str.contains('SIM', na=False)].shape[0] if tem_cotista else 0
            ncot_vol = df_vol.shape[0] - cot_vol
            val_vol = [cot_vol, ncot_vol] if (cot_vol+ncot_vol)>0 else [0, 1]
        else:
            val_vol = [0, 1]

        fig_vol_cot = px.pie(values=val_vol, names=["Cotistas", "Não cotistas"], hole=0.65, color_discrete_sequence=[COLORS["Ciano"], COLORS["Coral"]])
        fig_vol_cot.update_layout(template="plotly_dark", showlegend=False, height=chart_height, margin=dict(t=10,b=10,l=10,r=10), paper_bgcolor='rgba(0,0,0,0)')
        chart_title_strong("% Voluntários (cotistas vs não cotistas)")
        st.plotly_chart(fig_vol_cot, use_container_width=True)

    with col_d2:
        if not df_icti.empty and col_vinc in df_icti.columns:
            df_bol = df_icti[~df_icti[col_vinc].astype(str).str.contains('VOLUNT', na=False)]
            cot_bol = df_bol[df_bol[col_cotista].astype(str).str.contains('SIM', na=False)].shape[0] if tem_cotista else 0
            ncot_bol = df_bol.shape[0] - cot_bol
            val_bol = [cot_bol, ncot_bol] if (cot_bol+ncot_bol)>0 else [0, 1]
        else:
            val_bol = [0, 1]

        fig_bol_cot = px.pie(values=val_bol, names=["Cotistas", "Não cotistas"], hole=0.65, color_discrete_sequence=[COLORS["Ciano"], COLORS["Roxo"]])
        fig_bol_cot.update_layout(template="plotly_dark", showlegend=False, height=chart_height, margin=dict(t=10,b=10,l=10,r=10), paper_bgcolor='rgba(0,0,0,0)')
        chart_title_strong("% Bolsistas (cotistas vs não cotistas)")
        st.plotly_chart(fig_bol_cot, use_container_width=True)

    with col_d3:
        if not df_icti.empty and col_vinc in df_icti.columns:
            df_fom = df_icti[~df_icti[col_vinc].astype(str).str.contains('VOLUNT', na=False)]
            cnpq_count = df_fom[df_fom[col_vinc].astype(str).str.contains('CNPQ', na=False)].shape[0]
            upe = df_fom.shape[0] - cnpq_count
            val_fom = [upe, cnpq_count] if (upe+cnpq_count)>0 else [0, 1]
        else:
            val_fom = [0, 1]

        fig_bol_fom = px.pie(values=val_fom, names=["UPE", "CNPq"], hole=0.65, color_discrete_sequence=[COLORS["Coral"], COLORS["Verde Limao"]])
        fig_bol_fom.update_layout(template="plotly_dark", showlegend=False, height=chart_height, margin=dict(t=10,b=10,l=10,r=10), paper_bgcolor='rgba(0,0,0,0)')
        chart_title_strong("% Bolsistas (UPE vs CNPq)")
        st.plotly_chart(fig_bol_fom, use_container_width=True)

    with col_d4:
        st.write("")

    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
    st.markdown("<div style='position:relative;left:50%;right:50%;margin-left:-50vw;margin-right:-50vw;width:100vw;height:1px;background:#2b2f36;'></div>", unsafe_allow_html=True)
    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

    col_c1, col_c2 = st.columns(2)

    with col_c1:
        # A evolução temporal usa 'df_icti_all' (todos os anos) para mostrar o gráfico de linha contínuo
        chart_title("Evolução Temporal de Bolsas IC")
        if not df_icti_all.empty and 'ANO_ARQUIVO' in df_icti_all.columns:
            df_temp = df_icti_all.copy()
            df_temp['Categoria'] = df_temp[col_prog].apply(lambda x: 'PIBIC_EM' if 'EM' in str(x) else ('PIBITI' if 'PIBIT' in str(x) else 'PIBIC'))
            df_bolsas_evolucao = df_temp.groupby(['ANO_ARQUIVO', 'Categoria']).size().reset_index(name='Quantidade')
            
            fig_bolsas = go.Figure()
            for cat, color in zip(['PIBIC', 'PIBITI', 'PIBIC_EM'], [COLORS["Ciano"], COLORS["Amarelo"], COLORS["Coral"]]):
                d = df_bolsas_evolucao[df_bolsas_evolucao['Categoria'] == cat]
                fig_bolsas.add_trace(go.Scatter(x=d["ANO_ARQUIVO"], y=d["Quantidade"], name=cat, line=dict(color=color)))
        else:
            fig_bolsas = go.Figure()
        
        fig_bolsas.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', height=340, margin=dict(t=20,b=20,l=20,r=20), font=dict(size=12))
        st.plotly_chart(fig_bolsas, use_container_width=True)

        chart_title("Recursos dos Editais APQ")
        if not df_apq_all.empty and 'ANO_REFERENCIA_ABA' in df_apq_all.columns:
            col_valor = next((c for c in df_apq_all.columns if 'VALOR' in c), None)
            if col_valor:
                df_apq_group = df_apq_all.copy()
                df_apq_group[col_valor] = pd.to_numeric(df_apq_group[col_valor].astype(str).str.replace(r'[^\d.]', '', regex=True), errors='coerce').fillna(0)
                df_apq_group = df_apq_group.groupby('ANO_REFERENCIA_ABA')[col_valor].sum().reset_index()
                df_apq_group.rename(columns={'ANO_REFERENCIA_ABA': 'Ano', col_valor: 'Montante'}, inplace=True)
                df_apq_group = df_apq_group.sort_values('Ano')
            else:
                df_apq_group = pd.DataFrame(columns=['Ano', 'Montante'])
        else:
            df_apq_group = pd.DataFrame(columns=['Ano', 'Montante'])

        if not df_apq_group.empty:
            fig_apq = px.line(df_apq_group, x="Ano", y="Montante", markers=True, template="plotly_dark", color_discrete_sequence=[COLORS["Ciano"]])
            fig_apq.update_traces(line=dict(color="white", width=3), marker=dict(size=9), text=df_apq_group["Montante"].apply(lambda v: f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")), textposition="top center")
        else:
            fig_apq = go.Figure()
            
        fig_apq.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', height=340, margin=dict(t=30,b=20,l=10,r=10))
        fig_apq.update_yaxes(visible=False, showticklabels=False)
        st.plotly_chart(fig_apq, use_container_width=True)

    with col_c2:
        chart_title("Evolução dos Grupos de Pesquisa por Área de Conhecimento")
        if not df_gp_all.empty and 'ANO DE FORMAÇÃO' in df_gp_all.columns and 'ÁREA DE CONHECIMENTO' in df_gp_all.columns:
            df_gp_area = df_gp_all.groupby(['ANO DE FORMAÇÃO', 'ÁREA DE CONHECIMENTO']).size().reset_index(name='Quantidade')
            fig_gp_area = px.bar(df_gp_area, x="ANO DE FORMAÇÃO", y="Quantidade", color="ÁREA DE CONHECIMENTO", template="plotly_dark", color_discrete_sequence=[COLORS["Ciano"], COLORS["Coral"], COLORS["Roxo"], COLORS["Verde Limao"], COLORS["Amarelo"], COLORS["Gelo"]])
        else:
            fig_gp_area = go.Figure()
            
        fig_gp_area.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', legend=dict(orientation="h", y=-0.2), height=720, margin=dict(t=20,b=20,l=10,r=10))
        st.plotly_chart(fig_gp_area, use_container_width=True)

    # --- Seção: Pesquisadores e Bolsas Produtividade ---
    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
    
    chart_title("Quantidade de Pesquisadores Ativos UPE por Função e Titulação")
    if not df_docentes.empty and 'FUNÇÃO GERAL' in df_docentes.columns and 'ESCOLARIDADE' in df_docentes.columns:
        df_func = df_docentes.groupby(['FUNÇÃO GERAL', 'ESCOLARIDADE']).size().reset_index(name='Quantidade')
        fig_funcoes = px.bar(df_func, x='FUNÇÃO GERAL', y='Quantidade', color='ESCOLARIDADE', barmode='group', template='plotly_dark', color_discrete_sequence=[COLORS["Coral"], COLORS["Roxo"], COLORS["Ciano"], COLORS["Amarelo"]])
    else:
        fig_funcoes = go.Figure()
        
    fig_funcoes.update_layout(height=400, margin=dict(t=30, b=30, l=10, r=10), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', legend_title_text='Titulação', yaxis_title='Quantidade', xaxis_title='Função')
    fig_funcoes.update_traces(texttemplate='%{y}', textposition='outside')
    st.plotly_chart(fig_funcoes, use_container_width=True)

    # Abas inferiores
    tab_dist_alunos, tab_ranking_gp = st.tabs(["Distribuição de Alunos", "Ranking de GP"])
    
    with tab_dist_alunos:
        chart_title("Alunos Voluntários e Bolsistas por Modalidade (Cotista vs Não Cotista)")
        
        # Correção inteligente para gerar o gráfico mesmo que a coluna 'COTISTA' falte em anos antigos
        if not df_icti.empty and col_vinc in df_icti.columns:
            df_modalidade = df_icti.copy()
            df_modalidade['Tipo'] = df_modalidade[col_vinc].apply(lambda x: 'Voluntário' if 'VOLUNT' in str(x) else 'Bolsista')
            
            if tem_cotista:
                df_modalidade['Cotista'] = df_modalidade[col_cotista].apply(lambda x: 'Cotista' if 'SIM' in str(x) else 'Não Cotista')
            else:
                df_modalidade['Cotista'] = 'Não Informado'
                
            df_mod_group = df_modalidade.groupby([col_prog, 'Tipo', 'Cotista']).size().reset_index(name='Quantidade')
            
            fig_bolsistas_mod = px.bar(df_mod_group, x=col_prog, y="Quantidade", color="Cotista", facet_col="Tipo", barmode="group", color_discrete_map={'Cotista': COLORS["Ciano"], 'Não Cotista': COLORS["Roxo"], 'Não Informado': COLORS["Amarelo"]})
            fig_bolsistas_mod.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', legend_title_text="Categoria", height=420)
            st.plotly_chart(fig_bolsistas_mod, use_container_width=True)
        else:
            st.info(f"Dados insuficientes para gerar a distribuição de alunos no ano de {ano_selected}.")

        st.markdown("<hr style='border:1px solid #2b2f36'>", unsafe_allow_html=True)
        chart_title("Bolsistas por Unidade e por Grande Área")
        
        col_unidade_icti = next((c for c in df_icti.columns if 'UNIDADE' in c), None)
        col_area_icti = next((c for c in df_icti.columns if 'GRANDE' in c or 'ÁREA' in c), None)
        
        if not df_icti.empty and col_unidade_icti and col_area_icti:
            df_area_icti = df_icti.groupby([col_unidade_icti, col_area_icti]).size().reset_index(name='Quantidade')
            fig_areas = px.bar(df_area_icti, x=col_unidade_icti, y="Quantidade", color=col_area_icti, template="plotly_dark", color_discrete_sequence=px.colors.qualitative.Pastel)
            fig_areas.update_layout(height=500, margin=dict(t=20, b=20, l=10, r=10), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', legend_title_text='Grande Área')
            st.plotly_chart(fig_areas, use_container_width=True)

    with tab_ranking_gp:
        col_f1, col_f2 = st.columns([1, 3])
        anos_gp = sorted(df_gp['ANO DE FORMAÇÃO'].dropna().unique().tolist(), reverse=True) if not df_gp.empty and 'ANO DE FORMAÇÃO' in df_gp.columns else ["N/A"]
        
        with col_f1:
            ano_gp_selected = st.selectbox("Selecione o Ano de Formação do GP", anos_gp)
            
        chart_title(f"Ranking: Grupos de Pesquisa por Unidade e Curso (Filtro: {ano_gp_selected})")
        
        if not df_gp.empty and 'ANO DE FORMAÇÃO' in df_gp.columns and 'Nº ESTUDANTES' in df_gp.columns:
            df_gp['Nº ESTUDANTES'] = pd.to_numeric(df_gp['Nº ESTUDANTES'], errors='coerce').fillna(0)
            df_year = df_gp[df_gp['ANO DE FORMAÇÃO'] == ano_gp_selected]
            
            parts = []
            for un in df_year['CAMPUS'].unique():
                tmp = df_year[df_year['CAMPUS'] == un].sort_values('Nº ESTUDANTES', ascending=False).head(6)
                parts.append(tmp)
            df_top_groups = pd.concat(parts) if parts else df_year.copy()

            fig_rank = px.bar(df_top_groups, x='Nº ESTUDANTES', y='NOME DO GRUPO', color='CURSO', facet_col='CAMPUS', orientation='h', template='plotly_dark', color_discrete_sequence=[COLORS['Coral'], COLORS['Ciano'], COLORS['Roxo']])
            fig_rank.update_layout(height=600, margin=dict(t=30, b=30, l=10, r=10), showlegend=True, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            fig_rank.update_yaxes(tickfont=dict(size=10))
            st.plotly_chart(fig_rank, use_container_width=True)
        else:
            st.info("Dados de Grupos de Pesquisa insuficientes para gerar o ranking.")



# =========================================================
# TELA 3: INOVAÇÃO
# =========================================================

elif tela == "Inovação":
    st.header("Inovação")
    
    df_inov = load_inovacao_base_data().copy()
    
    if not df_inov.empty and 'Ano' in df_inov.columns:
        df_inov['Ano'] = pd.to_numeric(df_inov['Ano'], errors='coerce')
        df_inov['Receita'] = pd.to_numeric(df_inov['Receita'], errors='coerce').fillna(0)
        df_inov['Total de Bolsas'] = pd.to_numeric(df_inov['Total de Bolsas'], errors='coerce').fillna(0)
        
        ano_alvo = int(ano_selected)
        df_atual = df_inov[df_inov['Ano'] == ano_alvo]
        df_anterior = df_inov[df_inov['Ano'] == (ano_alvo - 1)]
        
        # Cálculos de Crescimento
        rec_atual = df_atual['Receita'].sum()
        rec_ant = df_anterior['Receita'].sum()
        pct_rec = ((rec_atual - rec_ant) / rec_ant * 100) if rec_ant > 0 else 0
        
        bol_atual = df_atual['Total de Bolsas'].sum()
        bol_ant = df_anterior['Total de Bolsas'].sum()
        pct_bol = ((bol_atual - bol_ant) / bol_ant * 100) if bol_ant > 0 else 0
        
        # Cards
        # Cards padronizados (estilo PROPEGI)
        col_k1, col_k2, col_k3, col_k4 = st.columns(4) # Usa 4 colunas para manter a mesma largura dos cards da Pesquisa
        
        with col_k1:
            # Passa o pct_rec calculado para o kpi_card_delta formatar a seta e cor
            kpi_card_delta("TOTAL DE RECURSOS CAPTADOS", format_brl(rec_atual), pct_rec, COLORS["Ciano"])
        with col_k2:
            kpi_card_delta("TOTAL DE BOLSAS INOVAÇÃO", str(int(bol_atual)), pct_bol, COLORS["Verde Limao"])
        with col_k3:
            st.empty() # Espaço vazio para manter alinhamento
        with col_k4:
            st.empty() # Espaço vazio para manter alinhamento   
        st.markdown("---")
        
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("Tendência Setor Privado / Público por ano")
            if 'Setor' in df_inov.columns:
                df_setor = df_inov.groupby(['Ano', 'Setor'])['Receita'].sum().reset_index()
                fig_setor = px.line(df_setor, x='Ano', y='Receita', color='Setor', markers=True, template="plotly_dark", color_discrete_sequence=[COLORS["Ciano"], COLORS["Coral"], COLORS["Amarelo"]])
                fig_setor.update_xaxes(type='category')
                st.plotly_chart(fig_setor, use_container_width=True)
                
        with c2:
            st.subheader("Evolução: Projetos Vigentes e Receita Anual")
            df_evolucao = df_inov.groupby('Ano').agg(Projetos=('Projeto', 'count'), Receita=('Receita', 'sum')).reset_index()
            fig_evo = make_subplots(specs=[[{"secondary_y": True}]])
            fig_evo.add_trace(go.Bar(x=df_evolucao['Ano'], y=df_evolucao['Projetos'], name="Qtd Projetos", marker_color=COLORS["Roxo"]), secondary_y=False)
            fig_evo.add_trace(go.Scatter(x=df_evolucao['Ano'], y=df_evolucao['Receita'], name="Receita Bruta", marker_color=COLORS["Verde Limao"]), secondary_y=True)
            fig_evo.update_layout(template="plotly_dark", barmode='group')
            fig_evo.update_xaxes(type='category')
            st.plotly_chart(fig_evo, use_container_width=True)
            
        c3, c4 = st.columns(2)
        with c3:
            st.subheader("Receita Média Anual por Projeto")
            df_media = df_inov.groupby('Ano')['Receita'].mean().reset_index(name='Receita Média')
            fig_media = px.bar(df_media, x='Ano', y='Receita Média', text_auto='.2s', template="plotly_dark", color_discrete_sequence=[COLORS["Ciano"]])
            fig_media.update_xaxes(type='category')
            st.plotly_chart(fig_media, use_container_width=True)
            
        with c4:
            st.subheader(f"Projetos por Segmento ({ano_alvo})")
            if 'Segmento' in df_atual.columns and not df_atual.empty:
                df_seg = df_atual.groupby('Segmento').size().reset_index(name='Qtd')
                fig_seg = px.pie(df_seg, values='Qtd', names='Segmento', hole=0.4, template="plotly_dark")
                st.plotly_chart(fig_seg, use_container_width=True)
    else:
        st.warning("Dados de inovação indisponíveis.")

# =========================================================
# TELA 4: DESENVOLVIMENTO TECNOLÓGICO
# =========================================================

elif tela == "Desenvolvimento Tecnológico":
    st.header("Desenvolvimento Tecnológico")
    
    df_inov = load_inovacao_base_data().copy()
    df_pi = load_pi_data().copy()
    ano_alvo = int(ano_selected)
    
    # Cálculos PI (Patentes)
    patentes_atual = 0
    patentes_ant = 0
    pct_patentes = 0
    
    if not df_pi.empty and 'Categoria_Aba' in df_pi.columns and 'Ano_PI' in df_pi.columns:
        df_patentes = df_pi[df_pi['Categoria_Aba'].str.contains('Patent', case=False, na=False)]
        patentes_atual = len(df_patentes[df_patentes['Ano_PI'] == ano_alvo])
        patentes_ant = len(df_patentes[df_patentes['Ano_PI'] == (ano_alvo - 1)])
        pct_patentes = ((patentes_atual - patentes_ant) / patentes_ant * 100) if patentes_ant > 0 else 0

    # Card
    # Card padronizado (estilo PROPEGI)
    col_p1, col_p2, col_p3, col_p4 = st.columns(4) # Usa 4 colunas para não ficar gigante
    
    with col_p1:
        kpi_card_delta("TOTAL DE PATENTES", str(int(patentes_atual)), pct_patentes, COLORS["Coral"])
    with col_p2:
        st.empty()
    with col_p3:
        st.empty()
    with col_p4:
        st.empty()
        
    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
    st.markdown("---")
    
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Evolução de Propriedade Intelectual")
        if not df_pi.empty and 'Ano_PI' in df_pi.columns:
            df_pi_evo = df_pi.groupby(['Ano_PI', 'Categoria_Aba']).size().reset_index(name='Qtd')
            fig_pi = px.bar(df_pi_evo, x='Ano_PI', y='Qtd', color='Categoria_Aba', template="plotly_dark", barmode='group')
            fig_pi.update_xaxes(type='category', title="Ano")
            st.plotly_chart(fig_pi, use_container_width=True)
        else:
            st.info("Sem dados de Propriedade Intelectual.")
            
    with c2:
        st.subheader(f"Natureza dos Projetos ({ano_alvo})")
        if not df_inov.empty and 'Natureza' in df_inov.columns:
            df_atual_inov = df_inov[df_inov['Ano'] == ano_alvo]
            if not df_atual_inov.empty:
                df_nat = df_atual_inov.groupby('Natureza').size().reset_index(name='Qtd')
                fig_nat = px.pie(df_nat, values='Qtd', names='Natureza', hole=0.4, template="plotly_dark", color_discrete_sequence=px.colors.qualitative.Pastel)
                st.plotly_chart(fig_nat, use_container_width=True)
            else:
                st.info("Sem dados de Natureza para o ano selecionado.")
                
    st.markdown("---")
    c3, c4 = st.columns(2)
    
    with c3:
        st.subheader(f"TRL dos Projetos de Inovação ({ano_alvo})")
        if not df_inov.empty and 'TRL' in df_inov.columns:
            df_atual_inov = df_inov[df_inov['Ano'] == ano_alvo]
            if not df_atual_inov.empty:
                df_trl = df_atual_inov.groupby('TRL').size().reset_index(name='Qtd')
                # Converte TRL para string para garantir eixo categórico correto
                df_trl['TRL'] = df_trl['TRL'].astype(str)
                fig_trl = px.bar(df_trl, x='TRL', y='Qtd', template="plotly_dark", color_discrete_sequence=[COLORS["Ciano"]])
                st.plotly_chart(fig_trl, use_container_width=True)
            else:
                st.info("Sem dados de TRL para o ano.")
                
    with c4:
        st.subheader(f"Projetos por Região de Desenvolvimento ({ano_alvo})")
        if not df_inov.empty and 'Região' in df_inov.columns:
            df_atual_inov = df_inov[df_inov['Ano'] == ano_alvo]
            if not df_atual_inov.empty:
                df_reg = df_atual_inov.groupby('Região').size().reset_index(name='Qtd')
                fig_reg = px.bar(df_reg.sort_values("Qtd", ascending=True), x='Qtd', y='Região', orientation='h', template="plotly_dark", color_discrete_sequence=[COLORS["Amarelo"]])
                st.plotly_chart(fig_reg, use_container_width=True)
                
    st.subheader(f"Quantidade de Projetos por Cidade ({ano_alvo})")
    if not df_inov.empty and 'Cidade' in df_inov.columns:
        df_atual_inov = df_inov[df_inov['Ano'] == ano_alvo]
        if not df_atual_inov.empty:
            df_cid = df_atual_inov.groupby('Cidade').size().reset_index(name='Qtd').sort_values("Qtd", ascending=False)
            fig_cid = px.bar(df_cid, x='Cidade', y='Qtd', template="plotly_dark", color_discrete_sequence=[COLORS["Verde Limao"]])
            st.plotly_chart(fig_cid, use_container_width=True)


# =========================================================
# TELA 5: PÓS-GRADUAÇÃO
# =========================================================
elif tela == "Pós-Graduação":
    tipo_pos = st.selectbox("Selecione a Categoria:", ["Stricto Sensu", "Lato Sensu"])
    pos_data = load_pos_graduacao_data()
    
    stricto_df_all = pos_data.get('stricto', pd.DataFrame()).copy()
    lato_df_all = pos_data.get('lato', pd.DataFrame()).copy()

    # Função matemática do Delta (%)
    def calc_delta_pos(atual, anterior):
        if anterior == 0:
            return 100.0 if atual > 0 else 0.0
        return ((atual - anterior) / anterior) * 100.0

    if tipo_pos == "Stricto Sensu":
        if stricto_df_all.empty:
            st.warning("⚠️ Os dados do Censo Stricto Sensu não foram encontrados na pasta data/processed/pos-graduacao/")
        else:
            # ---------------------------------------------------------
            # LÓGICA DE FILTRO DE ANO COM "FALLBACK INTELIGENTE"
            # ---------------------------------------------------------
            stricto_df_all['ANO_REF'] = stricto_df_all['ABA_ORIGEM'].astype(str).str.extract(r'(20\d{2})').astype(float)
            stricto_df_all['ANO_REF'] = stricto_df_all['ANO_REF'].fillna(int(ano_selected)) # Prevenção para abas sem ano
            
            anos_disponiveis = stricto_df_all['ANO_REF'].dropna().unique()
            ano_alvo = int(ano_selected)
            
            # Se o ano selecionado não existe, pega o último ano disponível anterior a ele
            if ano_alvo not in anos_disponiveis and len(anos_disponiveis) > 0:
                anos_menores = [a for a in anos_disponiveis if a <= ano_alvo]
                if anos_menores:
                    ano_alvo = int(max(anos_menores))
                    st.info(f"ℹ️ Não há censo para {ano_selected}. Exibindo os dados mais recentes disponíveis ({ano_alvo}).")
                else:
                    ano_alvo = int(min(anos_disponiveis))
                    st.info(f"ℹ️ Exibindo os dados de {ano_alvo}.")

            st.markdown(f"### Indicadores de Desempenho ({ano_alvo})")

            # Separa os DataFrames do ano alvo e do ano anterior (para gerar os deltas % de crescimento)
            stricto_df = stricto_df_all[stricto_df_all['ANO_REF'] == ano_alvo].copy()
            stricto_df_ant = stricto_df_all[stricto_df_all['ANO_REF'] == (ano_alvo - 1)].copy()

            # --- CÁLCULOS ANO ATUAL ---
            total_programas = stricto_df['PROGRAMA'].nunique()
            df_mestrado = stricto_df[stricto_df['NIVEL'] == 'Mestrado']
            df_doutorado = stricto_df[stricto_df['NIVEL'] == 'Doutorado']
            
            mat_mestrado = int(df_mestrado[df_mestrado['SITUAÇÃO'] == 'Matriculado']['TOTAL'].sum())
            tit_mestrado = int(df_mestrado[df_mestrado['SITUAÇÃO'] == 'Titulado']['TOTAL'].sum())
            mat_doutorado = int(df_doutorado[df_doutorado['SITUAÇÃO'] == 'Matriculado']['TOTAL'].sum())
            tit_doutorado = int(df_doutorado[df_doutorado['SITUAÇÃO'] == 'Titulado']['TOTAL'].sum())
            
            qtd_mestrados = df_mestrado[df_mestrado['TOTAL'] > 0]['PROGRAMA'].nunique()
            qtd_doutorados = df_doutorado[df_doutorado['TOTAL'] > 0]['PROGRAMA'].nunique()
            
            total_alunos = mat_mestrado + tit_mestrado + mat_doutorado + tit_doutorado
            taxa_titulacao = ((tit_mestrado + tit_doutorado) / total_alunos * 100) if total_alunos > 0 else 0

            # --- CÁLCULOS ANO ANTERIOR (PARA DELTAS) ---
            ant_programas = stricto_df_ant['PROGRAMA'].nunique() if not stricto_df_ant.empty else 0
            df_mes_ant = stricto_df_ant[stricto_df_ant['NIVEL'] == 'Mestrado'] if not stricto_df_ant.empty else pd.DataFrame()
            df_dou_ant = stricto_df_ant[stricto_df_ant['NIVEL'] == 'Doutorado'] if not stricto_df_ant.empty else pd.DataFrame()
            
            ant_mat_mes = int(df_mes_ant[df_mes_ant['SITUAÇÃO'] == 'Matriculado']['TOTAL'].sum()) if not df_mes_ant.empty else 0
            ant_tit_mes = int(df_mes_ant[df_mes_ant['SITUAÇÃO'] == 'Titulado']['TOTAL'].sum()) if not df_mes_ant.empty else 0
            ant_mat_dou = int(df_dou_ant[df_dou_ant['SITUAÇÃO'] == 'Matriculado']['TOTAL'].sum()) if not df_dou_ant.empty else 0
            ant_tit_dou = int(df_dou_ant[df_dou_ant['SITUAÇÃO'] == 'Titulado']['TOTAL'].sum()) if not df_dou_ant.empty else 0
            
            ant_qtd_mes = df_mes_ant[df_mes_ant['TOTAL'] > 0]['PROGRAMA'].nunique() if not df_mes_ant.empty else 0
            ant_qtd_dou = df_dou_ant[df_dou_ant['TOTAL'] > 0]['PROGRAMA'].nunique() if not df_dou_ant.empty else 0
            
            ant_total_alunos = ant_mat_mes + ant_tit_mes + ant_mat_dou + ant_tit_dou
            ant_taxa = ((ant_tit_mes + ant_tit_dou) / ant_total_alunos * 100) if ant_total_alunos > 0 else 0

            # --- RENDERIZAÇÃO DOS KPIS ---
            kpi_cols = st.columns(8)
            with kpi_cols[0]: kpi_card_delta("Nº de Programas", f"{total_programas}", calc_delta_pos(total_programas, ant_programas), COLORS["Amarelo"])
            with kpi_cols[1]: kpi_card_delta("Nº de Mestrados", f"{qtd_mestrados}", calc_delta_pos(qtd_mestrados, ant_qtd_mes), COLORS["Ciano"])
            with kpi_cols[2]: kpi_card_delta("Matriculados - Mestrado", f"{mat_mestrado}", calc_delta_pos(mat_mestrado, ant_mat_mes), COLORS["Ciano"])
            with kpi_cols[3]: kpi_card_delta("Titulados - Mestrado", f"{tit_mestrado}", calc_delta_pos(tit_mestrado, ant_tit_mes), COLORS["Ciano"])
            with kpi_cols[4]: kpi_card_delta("Nº de Doutorados", f"{qtd_doutorados}", calc_delta_pos(qtd_doutorados, ant_qtd_dou), COLORS["Coral"])
            with kpi_cols[5]: kpi_card_delta("Matriculados - Doutorado", f"{mat_doutorado}", calc_delta_pos(mat_doutorado, ant_mat_dou), COLORS["Coral"])
            with kpi_cols[6]: kpi_card_delta("Titulados - Doutorado", f"{tit_doutorado}", calc_delta_pos(tit_doutorado, ant_tit_dou), COLORS["Coral"])
            with kpi_cols[7]: kpi_card_delta("Índice Titulação", f"{taxa_titulacao:.1f}%", taxa_titulacao - ant_taxa, COLORS["Amarelo"]) 

            st.markdown("<div style='height:10px'></div><div style='position:relative;left:50%;right:50%;margin-left:-50vw;margin-right:-50vw;width:100vw;height:1px;background:#2b2f36;'></div><div style='height:6px'></div>", unsafe_allow_html=True)
            
            # --- GRÁFICOS REAIS ---
            col_s1, col_s2 = st.columns(2)
            
            with col_s1:
                chart_title("Distribuição de Alunos por Gênero e Nível (Matriculados)")
                df_matriculados = stricto_df[stricto_df['SITUAÇÃO'] == 'Matriculado'].copy()
                if not df_matriculados.empty:
                    df_matriculados_melt = df_matriculados.melt(id_vars=['PROGRAMA', 'NIVEL'], value_vars=['MASCULINO', 'FEMININO'], var_name='Gênero', value_name='Quantidade')
                    df_matriculados_melt['Gênero'] = df_matriculados_melt['Gênero'].str.title()
                    
                    df_gen_nivel = df_matriculados_melt.groupby(['NIVEL', 'Gênero'])['Quantidade'].sum().reset_index()
                    
                    fig_gen = px.bar(df_gen_nivel, x="NIVEL", y="Quantidade", color="Gênero", barmode="group", template='plotly_dark', color_discrete_sequence=[COLORS["Ciano"], COLORS["Coral"]])
                    fig_gen.update_layout(height=420, margin=dict(t=20, b=20, l=20, r=20), xaxis_title="Nível", yaxis_title="Quantidade de Alunos")
                    st.plotly_chart(fig_gen, use_container_width=True)
                else:
                    st.info("Sem dados de matriculados para este ano.")

            with col_s2:
                chart_title("Total de Alunos Matriculados por Programa")
                if not df_matriculados.empty:
                    df_prog = df_matriculados.groupby(['PROGRAMA', 'NIVEL'])['TOTAL'].sum().reset_index()
                    df_prog = df_prog[df_prog['TOTAL'] > 0]
                    
                    altura_grafico = max(420, len(df_prog['PROGRAMA'].unique()) * 30)
                    
                    fig_prog = px.bar(df_prog, x="TOTAL", y="PROGRAMA", color="NIVEL", orientation='h', template='plotly_dark', color_discrete_sequence=[COLORS["Ciano"], COLORS["Coral"]])
                    fig_prog.update_layout(height=altura_grafico, margin=dict(t=20, b=20, l=20, r=20), xaxis_title="Quantidade", yaxis_title="")
                    fig_prog.update_yaxes(categoryorder='total ascending', tickfont=dict(size=10))
                    st.plotly_chart(fig_prog, use_container_width=True)
                else:
                    st.info("Sem dados de programas para este ano.")

    else:
        # ---------------------------------------------------------
        # LÓGICA LATO SENSU (DADOS REAIS)
        # ---------------------------------------------------------
        if lato_df_all.empty:
            st.warning("⚠️ O arquivo 'lato_sensu_processado.csv' não foi encontrado na pasta data/processed/pos-graduacao/. Por favor, certifique-se de que rodou o script de ETL e moveu o arquivo para lá.")
        else:
            lato_df = lato_df_all.copy()
            
            # --- FILTRO LATO SENSU: MOSTRAR APENAS CURSOS EXISTENTES ATÉ O ANO SELECIONADO ---
            col_ano_criacao = next((c for c in lato_df.columns if 'ano' in str(c).lower() and 'cria' in str(c).lower()), None)
            if col_ano_criacao:
                lato_df[col_ano_criacao] = pd.to_numeric(lato_df[col_ano_criacao], errors='coerce')
                # Exibe cursos criados/renovados até o ano do filtro
                lato_df = lato_df[lato_df[col_ano_criacao] <= int(ano_selected)]
            
            st.markdown(f"### Indicadores de Desempenho (Acumulado até {ano_selected})")

            # Buscadores Inteligentes de Colunas
            col_unidade = next((c for c in lato_df.columns if 'unidade' in str(c).lower()), 'UNIDADE')
            col_area = next((c for c in lato_df.columns if 'área' in str(c).lower() or 'area' in str(c).lower()), 'GRANDE ÁREA E ÁREA DE CONHECIMENTO')
            col_natureza = next((c for c in lato_df.columns if 'natureza' in str(c).lower()), 'NATUREZA')
            col_modalidade = next((c for c in lato_df.columns if 'modalidade' in str(c).lower()), 'MODALIDADE')
            col_vagas = next((c for c in lato_df.columns if 'máximo' in str(c).lower() or 'vagas' in str(c).lower()), None)
            
            # --- KPIS ---
            total_cursos = len(lato_df)
            total_vagas = int(pd.to_numeric(lato_df[col_vagas], errors='coerce').sum()) if col_vagas else 0
            total_unidades = lato_df[col_unidade].nunique() if col_unidade in lato_df.columns else 0
            cursos_ead = len(lato_df[lato_df[col_modalidade].astype(str).str.contains('EAD', case=False, na=False)]) if col_modalidade in lato_df.columns else 0

            kpi_cols = st.columns(4)
            with kpi_cols[0]: kpi_card("Nº de Cursos Ativos", f"{total_cursos}", COLORS["Coral"])
            with kpi_cols[1]: kpi_card("Total de Vagas Ofertadas", f"{total_vagas:,}".replace(',', '.'), COLORS["Amarelo"])
            with kpi_cols[2]: kpi_card("Unidades Ofertantes", f"{total_unidades}", COLORS["Verde Limao"])
            with kpi_cols[3]: kpi_card("Cursos EAD / Híbridos", f"{cursos_ead}", COLORS["Ciano"])
            
            st.markdown("<div style='height:10px'></div><div style='position:relative;left:50%;right:50%;margin-left:-50vw;margin-right:-50vw;width:100vw;height:1px;background:#2b2f36;'></div><div style='height:6px'></div>", unsafe_allow_html=True)
            
            # --- GRÁFICOS REAIS LATO SENSU ---
            col1, col2 = st.columns(2)
            with col1:
                chart_title("Nº de Cursos por Grande Área")
                if col_area in lato_df.columns:
                    df_area = lato_df[col_area].value_counts().reset_index()
                    df_area.columns = ['Área', 'Cursos']
                    fig_area = px.bar(df_area, x="Área", y="Cursos", color="Área", template='plotly_dark', color_discrete_sequence=px.colors.qualitative.Pastel)
                    fig_area.update_layout(height=420, margin=dict(t=20, b=20, l=10, r=10), showlegend=False)
                    st.plotly_chart(fig_area, use_container_width=True)
                else:
                    st.info("Coluna de Área não encontrada.")

            with col2:
                chart_title("Cursos por Unidade, Natureza e Modalidade")
                if all(c in lato_df.columns for c in [col_unidade, col_natureza, col_modalidade]):
                    df_exemplo = lato_df.groupby([col_unidade, col_natureza, col_modalidade]).size().reset_index(name='Nº de Cursos')
                    fig_h = px.bar(df_exemplo, x=col_unidade, y='Nº de Cursos', color=col_natureza, barmode='group', facet_col=col_modalidade, template='plotly_dark', color_discrete_sequence=[COLORS["Ciano"], COLORS["Coral"]])
                    fig_h.update_layout(height=420, margin=dict(t=20, b=20, l=10, r=10))
                    st.plotly_chart(fig_h, use_container_width=True)
                else:
                    st.info("Colunas de Unidade/Natureza/Modalidade não encontradas.")





# --- RODAPÉ ÚNICO E FINAL ---
st.markdown("---")
st.markdown(f"<div style='text-align: center; color: grey;'>Observatório de Inteligência UPE - v1.0.0 (Filtro Atual: {ano_selected})</div>", unsafe_allow_html=True)