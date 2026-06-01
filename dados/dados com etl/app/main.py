import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from pathlib import Path
import json
import re
import unicodedata

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

# Paleta específica para Stricto Sensu (coesa entre gráficos)
STRICTO = {
    'Homens': '#00FFFF',      # Ciano
    'Mulheres': '#FF5765',    # Coral
    'Titulado': '#8E8DE1',    # Lilás pastel
    'Desistente': '#FFFE91',   # Amarelo pastel
    # cores adicionais para unidades/linhas
    'Unidade_1': '#26DFD0',    # Aqua
    'Unidade_2': '#5CE0D8',    # Verde pastel
    'Unidade_3': '#FFD700'     # Amarelo-ouro
}

# --- CSS PERSONALIZADO (Layout Estilo Manual PROPEGI) ---
st.markdown(f"""
    <style>
    [data-testid="stAppViewContainer"] {{ background-color: {COLORS['Fundo']}; }}
    [data-testid="stHeader"] {{ background: rgba(0,0,0,0); }}
    
    /* Estilização dos Cards Superiores */
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
    .kpi-value {{ font-size: 24px; font-weight: bold; color: white; line-height: 1.1; }}
    .kpi-label {{
        font-size: 12px;
        color: #999;
        text-transform: uppercase;
        line-height: 1.15;
        min-height: 44px;
        display: flex;
        align-items: center;
        justify-content: center;
        text-align: center;
    }}
    </style>
""", unsafe_allow_html=True)

# --- FUNÇÃO PARA CRIAR CARDS ---
def kpi_card(label, value, color):
    st.markdown(f"""
        <div class="kpi-card" style="border-top-color: {color};">
            <div class="kpi-label">{label}</div>
            <div class="kpi-value">{value}</div>
        </div>
    """, unsafe_allow_html=True)

# --- NOVA FUNÇÃO PARA CARDS COM DELTA ---
def kpi_card_delta(label, value, delta, color):
    delta_color = "green" if delta >= 0 else "red"
    arrow = "↑" if delta >= 0 else "↓"
    st.markdown(f"""
        <div class="kpi-card" style="border-top-color: {color};">
            <div class="kpi-label">{label}</div>
            <div class="kpi-value">{value} <span style="font-size: 16px; color: {delta_color};">{arrow} {abs(delta):.1f}%</span></div>
        </div>
    """, unsafe_allow_html=True)


def chart_title(text):
    st.markdown(
        f"<div style='font-size:16px;font-weight:700;line-height:1.2;min-height:44px;margin:0 0 8px 0;display:flex;align-items:flex-end;'>{text}</div>",
        unsafe_allow_html=True,
    )


def normalize_df(df, mapping):
    """
    Retorna uma cópia de `df` com colunas renomeadas segundo `mapping`.

    mapping: dict, por exemplo {'year':'Ano', 'campus':'Unidade', 'qty':'Quantidade'}

    Exemplo de uso:
        df_norm = normalize_df(df_real, {'year':'Ano','campus':'Unidade','type':'Status','qty':'Quantidade'})

    A função não altera o DataFrame original.
    """
    if df is None:
        return None
    df2 = df.copy()
    try:
        df2 = df2.rename(columns=mapping)
    except Exception:
        # Se ocorrer qualquer problema, retornamos a cópia sem alteração
        return df2
    return df2

def _read_csv_flexible(path_obj):
    for enc in ("utf-8-sig", "utf-8", "latin1"):
        try:
            return pd.read_csv(path_obj, encoding=enc)
        except Exception:
            continue
    return pd.DataFrame()


@st.cache_data(show_spinner=False)
def load_processed_data():
    root = Path(__file__).resolve().parents[1] / "data" / "processed"
    data = {}

    csv_map = {
        "inovacao_dashboard": root / "inovacao" / "dashboard_inovacao.csv",
        "inovacao_pi": root / "inovacao" / "propriedade_intelectual.csv",
        "dt_dados": root / "desenvolvimento_tecnologico" / "dados.json",
        "pesquisa_bolsistas_2023": root / "pesquisa" / "bolsistas_pq_dt" / "bolsistas_2023.csv",
        "pesquisa_bolsistas_2024": root / "pesquisa" / "bolsistas_pq_dt" / "bolsistas_2024.csv",
        "pesquisa_docentes": root / "pesquisa" / "docentes_ativos_upe" / "docentes_ativos.csv",
        "pesquisa_grupos": root / "pesquisa" / "grupos_de_pesquisa" / "grupos_pesquisa.csv",
        "pesquisa_apq": root / "pesquisa" / "planilhas_apq" / "prestacao_contas_apq.csv",
        "pesquisa_icti_2022": root / "pesquisa" / "planilhas_icti" / "icti_2022.csv",
        "pesquisa_icti_2023": root / "pesquisa" / "planilhas_icti" / "icti_2023.csv",
        "pesquisa_icti_2023_extra": root / "pesquisa" / "planilhas_icti" / "icti_2023_extra.csv",
        "pesquisa_icti_2024": root / "pesquisa" / "planilhas_icti" / "icti_2024.csv",
        "pesquisa_icti_2025": root / "pesquisa" / "planilhas_icti" / "icti_2025.csv",
        "pos_stricto": root / "pos_graduacao" / "censo_stricto_sensu.csv",
        "pos_lato": root / "pos_graduacao" / "lato_sensu.csv",
    }

    for key, file_path in csv_map.items():
        if not file_path.exists():
            data[key] = pd.DataFrame()
            continue
        df = _read_csv_flexible(file_path)
        if not df.empty:
            df.columns = [_slug_text(c) for c in df.columns]
        data[key] = df

    json_path = root / "desenvolvimento_tecnologico" / "dados.json"
    if json_path.exists():
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                json_data = json.load(f)
        except Exception:
            with open(json_path, "r", encoding="latin1") as f:
                json_data = json.load(f)
        data["dt_dados_json"] = pd.DataFrame(json_data)
        if not data["dt_dados_json"].empty:
            data["dt_dados_json"].columns = [_slug_text(c) for c in data["dt_dados_json"].columns]
    else:
        data["dt_dados_json"] = pd.DataFrame()

    return data


DATASETS = load_processed_data()


def _format_int(value):
    try:
        return f"{int(round(float(value))):,}".replace(",", ".")
    except Exception:
        return "0"


def _format_million_brl(value):
    try:
        return f"R$ {float(value) / 1_000_000:.1f}M"
    except Exception:
        return "R$ 0.0M"


def _pct_delta(current, previous):
    if previous in (None, 0) or pd.isna(previous):
        return 0.0
    try:
        return ((float(current) - float(previous)) / float(previous)) * 100.0
    except Exception:
        return 0.0


def _get_year_col(df):
    return _find_col(df, ["ano", "ano_de_criacao", "data", "data_de_deposito"])


def _counts_df(series, key_name, value_name):
    if series is None:
        return pd.DataFrame(columns=[key_name, value_name])
    df_counts = series.value_counts(dropna=False).rename_axis(key_name).reset_index(name=value_name)
    return df_counts

# --- SIDEBAR (NAVEGAÇÃO) ---
with st.sidebar:
    st.image("https://www.upe.br/templates/padraogoverno01/images/logo-upe.png", width=150) # Logo UPE
    st.title("Menu de Navegação")
    tela = st.radio("Selecione a Tela:", 
                   ["Visão Geral", "Pesquisa", "Inovação", "Desenvolvimento Tecnológico", "Pós-Graduação"])
    st.info("Painel de Gestão Estratégica PROPEGI")

# --- FILTRO GLOBAL (Obrigatório no topo) ---
st.title(f"📊 {tela}")
col_filter1, col_filter2 = st.columns([1, 3])
with col_filter1:
    ano_selected = st.selectbox("📅 FILTRO ANO", [2025, 2024, 2023, 2022], index=0)

# =========================================================
# TELA 1: VISÃO GERAL (ALTA GESTÃO)
# =========================================================
if tela == "Visão Geral":
    st.markdown(
        """
        <div style='background:transparent;padding:12px 8px;margin-bottom:8px;color:#cfd8dc;'>
        <strong>Coordenações disponíveis:</strong>
        <ul style='margin:6px 0 0 18px;padding:0;color:#b0bec5;'>
          <li><strong>Pesquisa</strong>: KPIs e análises de bolsas, grupos de pesquisa, produtividade e evolução por áreas.</li>
          <li><strong>Inovação</strong>: indicadores de projetos, patentes, receitas e bolsas de inovação.</li>
          <li><strong>Desenvolvimento Tecnológico</strong>: acompanhamento de projetos, receitas por região, produtos e fornecedores.</li>
          <li><strong>Pós-Graduação</strong>: painéis por programa, matrícula, titulação e desempenho.</li>
        </ul>
        <div style='margin-top:6px;color:#90a4ae;'>Use a barra lateral para navegar entre as coordenações e explorar os painéis detalhados.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns(3)
    with col1: kpi_card_delta("Total Fomento Captado", "R$ 14.5M", 8.4, COLORS["Ciano"])
    with col2: kpi_card_delta("Pesquisadores Ativos", "1.890", -2.3, COLORS["Coral"])
    with col3: kpi_card_delta("Entregas Científicas (Ano)", "4.210", 5.1, COLORS["Amarelo"])

    # Indicadores de metas lado a lado
    col_g1, col_g2 = st.columns(2)

    with col_g1:
        chart_title("Meta 1")
        fig_gauge_1 = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = 450,
            title = {'text': "Meta 1"},
            gauge = {'axis': {'range': [None, 500]}, 'bar': {'color': COLORS['Ciano']}}
        ))
        fig_gauge_1.update_layout(paper_bgcolor=COLORS['Card'], font={'color': "white"})
        st.plotly_chart(fig_gauge_1, use_container_width=True)

    with col_g2:
        chart_title("Meta 2")
        fig_gauge_2 = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = 320,
            title = {'text': "Meta 2"},
            gauge = {'axis': {'range': [None, 400]}, 'bar': {'color': COLORS['Coral']}}
        ))
        fig_gauge_2.update_layout(paper_bgcolor=COLORS['Card'], font={'color': "white"})
        st.plotly_chart(fig_gauge_2, use_container_width=True)

# =========================================================
# TELA 2: COORDENAÇÃO DE PESQUISA
# =========================================================
elif tela == "Pesquisa":
    icti_year_map = {
        2022: DATASETS.get("pesquisa_icti_2022", pd.DataFrame()),
        2023: DATASETS.get("pesquisa_icti_2023", pd.DataFrame()),
        2024: DATASETS.get("pesquisa_icti_2024", pd.DataFrame()),
        2025: DATASETS.get("pesquisa_icti_2025", pd.DataFrame()),
    }
    df_icti_year = icti_year_map.get(int(ano_selected), pd.DataFrame())
    programa_col = _find_col(df_icti_year, ["programa", "programa_1"])

    if programa_col and not df_icti_year.empty:
        prog_series = df_icti_year[programa_col].astype(str).str.upper()
        total_pibic = int(prog_series.str.contains("PIBIC", na=False).sum())
        total_pibiti = int(prog_series.str.contains("PIBITI", na=False).sum())
        total_pibic_em = int(prog_series.str.contains("EM", na=False).sum())
    else:
        total_pibic, total_pibiti, total_pibic_em = 450, 120, 60

    df_grupos = DATASETS.get("pesquisa_grupos", pd.DataFrame())
    total_grupos = int(len(df_grupos)) if not df_grupos.empty else 42

    df_docentes = DATASETS.get("pesquisa_docentes", pd.DataFrame())
    doc_total_col = _find_col(df_docentes, ["n_de_servidores", "n_serv_1", "n_de_servidores_"])
    total_docentes = int(_to_number(df_docentes[doc_total_col]).sum()) if doc_total_col else 340

    total_estudantes = int(total_pibic + total_pibiti + total_pibic_em)

    df_bolsas_pq = pd.concat(
        [
            DATASETS.get("pesquisa_bolsistas_2023", pd.DataFrame()),
            DATASETS.get("pesquisa_bolsistas_2024", pd.DataFrame()),
        ],
        ignore_index=True,
    )
    total_bolsistas_cnpq = int(len(df_bolsas_pq)) if not df_bolsas_pq.empty else 85

    col1, col2, col3, col4 = st.columns(4)
    with col1: kpi_card_delta("TOTAL DE BOLSAS PIBIC", _format_int(total_pibic), 0.0, COLORS["Ciano"])
    with col2: kpi_card_delta("TOTAL DE BOLSAS PIBITI", _format_int(total_pibiti), 0.0, COLORS["Coral"])
    with col3: kpi_card_delta("TOTAL DE BOLSAS PIBIC-EM", _format_int(total_pibic_em), 0.0, COLORS["Amarelo"])
    with col4: kpi_card_delta("GRUPOS DE PESQUISA", _format_int(total_grupos), 0.0, COLORS["Verde Limao"])
    # Segunda linha de KPIs solicitada
    st.markdown("<br>", unsafe_allow_html=True)
    col_k1, col_k2, col_k3, col_k4 = st.columns(4)
    with col_k1:
        kpi_card("TOTAL DE DOCENTES PESQUISADORES", _format_int(total_docentes), COLORS["Roxo"])
    with col_k2:
        kpi_card("TOTAL DE ESTUDANTES PESQUISADORES", _format_int(total_estudantes), COLORS["Ciano"])
    with col_k3:
        kpi_card_delta("TOTAL DE BOLSISTAS PRODUTIVIDADE CNPQ", _format_int(total_bolsistas_cnpq), 0.0, COLORS["Coral"])
    with col_k4:
        kpi_card_delta("TOTAL DE BOLSISTAS PRODUTIVIDADE FACEPE", "42", 3.1, COLORS["Amarelo"])

    # Donut charts aligned with KPI cards (same visual area)
    col_d1, col_d2, col_d3, col_d4 = st.columns(4)
    chart_height = 160

    with col_d1:
        fig_vol_cot = px.pie(
            values=[35, 65],
            names=["Cotistas", "Não cotistas"],
            hole=0.65,
            color_discrete_sequence=[COLORS["Ciano"], COLORS["Coral"]],
        )
        fig_vol_cot.update_layout(template="plotly_dark", showlegend=False, height=chart_height, margin=dict(t=10,b=10,l=10,r=10), paper_bgcolor='rgba(0,0,0,0)')
        st.markdown("<div style='text-align:center; color: #9aa0ac; font-size:12px'>% Voluntários (cotistas vs não cotistas)</div>", unsafe_allow_html=True)
        st.plotly_chart(fig_vol_cot, use_container_width=True)

    with col_d2:
        fig_bol_cot = px.pie(
            values=[48, 52],
            names=["Cotistas", "Não cotistas"],
            hole=0.65,
            color_discrete_sequence=[COLORS["Ciano"], COLORS["Roxo"]],
        )
        fig_bol_cot.update_layout(template="plotly_dark", showlegend=False, height=chart_height, margin=dict(t=10,b=10,l=10,r=10), paper_bgcolor='rgba(0,0,0,0)')
        st.markdown("<div style='text-align:center; color: #9aa0ac; font-size:12px'>% Bolsistas (cotistas vs não cotistas)</div>", unsafe_allow_html=True)
        st.plotly_chart(fig_bol_cot, use_container_width=True)

    with col_d3:
        fig_bol_fom = px.pie(
            values=[60, 40],
            names=["UPE", "CNPq"],
            hole=0.65,
            color_discrete_sequence=[COLORS["Coral"], COLORS["Verde Limao"]],
        )
        fig_bol_fom.update_layout(template="plotly_dark", showlegend=False, height=chart_height, margin=dict(t=10,b=10,l=10,r=10), paper_bgcolor='rgba(0,0,0,0)')
        st.markdown("<div style='text-align:center; color: #9aa0ac; font-size:12px'>% Bolsistas (UPE vs CNPq)</div>", unsafe_allow_html=True)
        st.plotly_chart(fig_bol_fom, use_container_width=True)

    with col_d4:
        st.write("")

    col_c1, col_c2 = st.columns(2)

    with col_c1:
        chart_title("Evolução Temporal de Bolsas IC")
        rows_bolsas = []
        for ano_ref, df_icti_ref in icti_year_map.items():
            prog_col_ref = _find_col(df_icti_ref, ["programa", "programa_1"])
            if prog_col_ref and not df_icti_ref.empty:
                s = df_icti_ref[prog_col_ref].astype(str).str.upper()
                rows_bolsas.append(
                    {
                        "Ano": ano_ref,
                        "PIBIC": int(s.str.contains("PIBIC", na=False).sum()),
                        "PIBITI": int(s.str.contains("PIBITI", na=False).sum()),
                        "PIBIC_EM": int(s.str.contains("EM", na=False).sum()),
                    }
                )
        df_bolsas = pd.DataFrame(rows_bolsas)
        if df_bolsas.empty:
            df_bolsas = pd.DataFrame(
                {
                    "Ano": [2022, 2023, 2024, 2025],
                    "PIBIC": [380, 400, 420, 450],
                    "PIBITI": [90, 100, 110, 120],
                    "PIBIC_EM": [40, 50, 45, 60],
                }
            )
        fig_bolsas = go.Figure()
        fig_bolsas.add_trace(go.Scatter(x=df_bolsas["Ano"], y=df_bolsas["PIBIC"], name="PIBIC", line=dict(color=COLORS["Ciano"])))
        fig_bolsas.add_trace(go.Scatter(x=df_bolsas["Ano"], y=df_bolsas["PIBITI"], name="PIBITI", line=dict(color=COLORS["Amarelo"])))
        fig_bolsas.add_trace(go.Scatter(x=df_bolsas["Ano"], y=df_bolsas["PIBIC_EM"], name="PIBIC_EM", line=dict(color=COLORS["Coral"])))
        fig_bolsas.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', height=340, margin=dict(t=20,b=20,l=20,r=20), font=dict(size=12))
        st.plotly_chart(fig_bolsas, use_container_width=True)

        chart_title("Recursos dos Editais APQ")
        df_apq_raw = DATASETS.get("pesquisa_apq", pd.DataFrame())
        apq_val_col = _find_col(df_apq_raw, ["valor_aprovado_r", "valor_aprovado"])
        apq_date_col = _find_col(df_apq_raw, ["data_que_recebeu_o_recurso", "data_que_enviou_a_prestacao_de_contas"])
        if apq_val_col and apq_date_col and not df_apq_raw.empty:
            tmp_apq = df_apq_raw.copy()
            tmp_apq["Ano"] = pd.to_datetime(tmp_apq[apq_date_col], errors="coerce", dayfirst=True).dt.year
            tmp_apq["Montante"] = _to_number(tmp_apq[apq_val_col])
            df_apq = tmp_apq.groupby("Ano", as_index=False)["Montante"].sum().dropna()
            df_apq = df_apq.sort_values("Ano")
        else:
            df_apq = pd.DataFrame(
                {
                    "Ano": [2022, 2023, 2024, 2025],
                    "Montante": [351865.17, 599334.00, 533322.70, 738000.00],
                }
            )
        fig_apq = px.line(
            df_apq,
            x="Ano",
            y="Montante",
            markers=True,
            template="plotly_dark",
            color_discrete_sequence=[COLORS["Ciano"]]
        )
        fig_apq.update_traces(
            line=dict(color="white", width=3),
            marker=dict(size=9),
            text=df_apq["Montante"].apply(lambda valor: f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")),
            textposition="top center"
        )
        fig_apq.update_layout(
            template="plotly_dark",
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            height=340,
            margin=dict(t=20,b=20,l=20,r=20),
            showlegend=True,
            font=dict(size=12)
        )
        fig_apq.update_yaxes(title_text="Montante (R$)")
        fig_apq.update_xaxes(title_text="Ano")
        st.plotly_chart(fig_apq, use_container_width=True)

        # --- Evolução GRUPOS DE PESQUISA POR ÁREA DE CONHECIMENTO E POR ANO ---

        areas = [
            "Administração",
            "Biologia geral",
            "Ciências Agrárias",
            "Ciências Biológicas",
            "Ciências da saúde",
            "Ciências exatas e da terra",
            "Ciências Humanas",
            "Ciências sociais aplicadas",
            "Engenharias",
            "Geografia Física",
            "Linguística, Letras e Artes"
        ]

        anos_area = [2022, 2023, 2024, 2025]
        rows_area = []
        for ai, area in enumerate(areas):
            base = 5 + ai
            for i, ano in enumerate(anos_area):
                qtd = int(base + i * (2 + (ai % 3)))
                rows_area.append({"Ano": ano, "Area": area, "Grupos": qtd})

        df_area_groups = pd.DataFrame(rows_area)

        # Mostrar apenas a evolução (séries) — ocupa a coluna atual (lado esquerdo)
        chart_title("Evolução dos Grupos de Pesquisa por Área de Conhecimento")
        sel_area = st.selectbox("Selecione a Área:", areas, index=0, key="sel_area_evo")
        df_sel = df_area_groups[df_area_groups['Area'] == sel_area]
        if df_sel.empty:
            st.info("Dados não disponíveis para a área selecionada.")
        else:
            fig_area_evo = px.line(df_sel, x='Ano', y='Grupos', markers=True, template='plotly_dark')
            fig_area_evo.update_layout(height=420, margin=dict(t=10, b=10, l=10, r=10), legend_title_text='Área')
            fig_area_evo.update_xaxes(dtick=1)
            st.plotly_chart(fig_area_evo, use_container_width=True)

        # --- Rankings adicionais solicitados ---
        col_r1, col_r2 = st.columns(2)

        # Ranking Pesquisadores Ativos UPE por Unidade e Titulação
        with col_r1:
            chart_title("Ranking: Pesquisadores Ativos UPE — por Unidade e Titulação")
            titulacoes = ["Graduado", "Especialista", "Mestres", "Doutores", "Pós-doc"]
            unidades_rank = ["Recife", "Garanhuns", "Petrolina"]
            rows_pesq = []
            for un in unidades_rank:
                for tit in titulacoes:
                    # mock: maiores números em Recife
                    base = 30 if un == 'Recife' else (15 if un == 'Garanhuns' else 10)
                    adj = titulacoes.index(tit) * 3
                    qtd = int(base + adj + np.random.randint(0,5))
                    rows_pesq.append({"Unidade": un, "Titulacao": tit, "Quantidade": qtd})

            df_pesq = pd.DataFrame(rows_pesq)
            # gráfico agrupado por Unidade (x) com barras por Titulação
            fig_pesq = px.bar(df_pesq, x='Unidade', y='Quantidade', color='Titulacao', barmode='group', template='plotly_dark', color_discrete_sequence=[COLORS['Ciano'], COLORS['Coral'], COLORS['Roxo'], COLORS['Amarelo'], COLORS['Verde Limao']])
            fig_pesq.update_layout(height=380, margin=dict(t=10,b=10,l=10,r=10), legend_title_text='Titulação')
            st.plotly_chart(fig_pesq, use_container_width=True)

        # Ranking de Alunos por Campus e Curso
        with col_r2:
            chart_title("Ranking: Alunos por Campus e Curso")
            campuses = ["Recife", "Garanhuns", "Petrolina"]
            cursos_rank = ["Biotecnologia", "Eng. de Software", "Saúde Pública", "Administração", "Direito Aplicado"]
            rows_alunos = []
            for camp in campuses:
                for curso in cursos_rank:
                    base = 300 if camp == 'Recife' else (120 if camp == 'Garanhuns' else 80)
                    adj = (cursos_rank.index(curso) * 20)
                    qtd = int(base - adj + np.random.randint(-10,30))
                    rows_alunos.append({"Campus": camp, "Curso": curso, "Alunos": max(0, qtd)})

            df_alunos = pd.DataFrame(rows_alunos)
            sel_campus = st.selectbox("Selecione Campus:", campuses, index=0, key="sel_campus_rank")
            df_campus = df_alunos[df_alunos['Campus'] == sel_campus].sort_values('Alunos', ascending=True)
            fig_alunos = px.bar(df_campus, x='Alunos', y='Curso', orientation='h', template='plotly_dark', color='Curso')
            fig_alunos.update_layout(height=380, margin=dict(t=10,b=10,l=10,r=10), showlegend=False)
            st.plotly_chart(fig_alunos, use_container_width=True)

        # --- Seção adicional: Pesquisadores e Bolsas Produtividade ---
        st.markdown("---")
        # removed section header per request
        # Gráfico de pesquisadores fica fora do agrupamento de abas
        chart_title("Quantidade de Pesquisadores Ativos UPE por Função e Titulação")
        funcoes = ["Docente", "Pesquisador", "Técnico Administrativo"]
        titulacoes = ["Graduado", "Especialista", "Mestres", "Doutores", "Pós-doc"]
        rows_pf = []
        for ano in [2022, 2023, 2024, 2025]:
            for f in funcoes:
                for t in titulacoes:
                    base = 50 if f == 'Docente' else (20 if f == 'Pesquisador' else 8)
                    qtd = int(base + titulacoes.index(t)*5 + (ano-2022)*2 + np.random.randint(0,4))
                    rows_pf.append({"Ano": ano, "Funcao": f, "Titulacao": t, "Quantidade": qtd})
        df_pf = pd.DataFrame(rows_pf)
        df_pf_year = df_pf[df_pf['Ano'] == int(ano_selected)]
        fig_pf = px.bar(df_pf_year, x='Funcao', y='Quantidade', color='Titulacao', barmode='group', template='plotly_dark')
        fig_pf.update_layout(height=420, margin=dict(t=20,b=20,l=20,r=20))
        st.plotly_chart(fig_pf, use_container_width=True)

        # Dados-mock compartilhados entre CNPq, FACEPE e evolução
        anos = [2022, 2023, 2024, 2025]
        unidades = ["Recife", "Garanhuns", "Petrolina"]
        modalidades = ["Iniciação", "Mestrado", "Doutorado"]
        areas = ["Saúde", "Engenharia", "Ciências Humanas", "Biológicas"]

        rows_c = []
        for ano in anos:
            for un in unidades:
                for mod in modalidades:
                    for ar in areas:
                        qtd = int(5 + (ano-2022)*3 + unidades.index(un)*2 + modalidades.index(mod)*2 + np.random.randint(0,5))
                        rows_c.append({"Ano": ano, "Unidade": un, "Modalidade": mod, "Area": ar, "Quantidade": qtd})
        df_cnpq = pd.DataFrame(rows_c)

        rows_f = []
        for ano in anos:
            for un in unidades:
                for mod in modalidades:
                    for ar in areas:
                        qtd = int(3 + (ano-2022)*2 + unidades.index(un)*1 + modalidades.index(mod)*2 + np.random.randint(0,4))
                        rows_f.append({"Ano": ano, "Unidade": un, "Modalidade": mod, "Area": ar, "Quantidade": qtd})
        df_facepe = pd.DataFrame(rows_f)

        tab_evol, tab_cnpq, tab_facepe = st.tabs(["Evolução Bolsas Produtividade", "Bolsas Produtividade CNPq", "Bolsas Produtividade FACEPE"])

        # Tab 1: Evolução Bolsas Produtividade (CNPq vs FACEPE)
        with tab_evol:
            chart_title("Evolução: Bolsas Produtividade CNPq vs FACEPE")
            # aggregate by year from mocks
            agg_c = df_cnpq.groupby('Ano')['Quantidade'].sum().reset_index().rename(columns={'Quantidade':'CNPq'})
            agg_f = df_facepe.groupby('Ano')['Quantidade'].sum().reset_index().rename(columns={'Quantidade':'FACEPE'})
            df_evol = agg_c.merge(agg_f, on='Ano')
            df_plot = df_evol.melt(id_vars='Ano', value_vars=['CNPq','FACEPE'], var_name='Fonte', value_name='Quantidade')
            fig_e = px.line(df_plot, x='Ano', y='Quantidade', color='Fonte', markers=True, template='plotly_dark')
            fig_e.update_layout(height=420, margin=dict(t=20,b=20,l=20,r=20))
            st.plotly_chart(fig_e, use_container_width=True)

        # Tab 2: Bolsas Produtividade CNPq
        with tab_cnpq:
            chart_title("Quantidade de Bolsas Produtividade CNPq")
            dim = st.selectbox("Agrupar por:", ["Ano","Unidade","Modalidade","Area"], index=0, key='dim_cnpq')
            agg = df_cnpq.groupby(dim)['Quantidade'].sum().reset_index().sort_values('Quantidade', ascending=True)
            if dim == 'Ano':
                agg['Ano'] = agg['Ano'].astype(str)
                agg = agg.sort_values('Ano', ascending=True)
                fig_c = px.bar(agg, x='Quantidade', y='Ano', orientation='h', template='plotly_dark', color='Ano')
            else:
                fig_c = px.bar(agg, x='Quantidade', y=dim, orientation='h', template='plotly_dark', color=dim)
            fig_c.update_traces(marker_line_width=0)
            fig_c.update_layout(height=420, margin=dict(t=20,b=20,l=20,r=20))
            st.plotly_chart(fig_c, use_container_width=True)

        # Tab 3: Bolsas Produtividade FACEPE
        with tab_facepe:
            chart_title("Quantidade de Bolsas Produtividade FACEPE")
            dim_f = st.selectbox("Dimensionar por:", ["Ano","Unidade","Modalidade","Area"], index=0, key='dim_facepe')
            aggf = df_facepe.groupby(dim_f)['Quantidade'].sum().reset_index().sort_values('Quantidade', ascending=True)
            if dim_f == 'Ano':
                aggf['Ano'] = aggf['Ano'].astype(str)
                aggf = aggf.sort_values('Ano', ascending=True)
                fig_f = px.bar(aggf, x='Quantidade', y='Ano', orientation='h', template='plotly_dark', color='Ano')
            else:
                fig_f = px.bar(aggf, x='Quantidade', y=dim_f, orientation='h', template='plotly_dark', color=dim_f)
            fig_f.update_traces(marker_line_width=0)
            fig_f.update_layout(height=420, margin=dict(t=20,b=20,l=20,r=20))
            st.plotly_chart(fig_f, use_container_width=True)

    with col_c2:
        chart_title("Quantidade de Bolsas por Modalidade")
        df_modal = pd.DataFrame({
            "Modalidade": ["CNPq", "UPE", "CNPq", "UPE", "CNPq", "UPE"],
            "Tipo": ["PIBIC", "PIBIC", "PIBITI", "PIBITI", "PIBIC_EM", "PIBIC_EM"],
            "Quantidade": [200, 180, 50, 70, 30, 40]
        })
        color_map = {"PIBIC": COLORS["Ciano"], "PIBITI": COLORS["Amarelo"], "PIBIC_EM": COLORS["Coral"]}
        fig_modal = px.bar(df_modal, x="Modalidade", y="Quantidade", color="Tipo", barmode="group", color_discrete_map=color_map)
        fig_modal.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', legend_title_text="Tipo de Bolsa", height=380, margin=dict(t=20,b=20,l=20,r=20))
        st.plotly_chart(fig_modal, use_container_width=True)

        chart_title("Alunos Voluntários e Bolsistas por Modalidade (Cotista vs Não Cotista)")
        col_v1, col_v2 = st.columns(2)

        with col_v1:
            chart_title("Alunos Voluntários por Modalidade")
            df_vol_modal = pd.DataFrame({
                "Modalidade": ["Cotista", "Não Cotista"] * 3,
                "Tipo": ["PIBIC"]*2 + ["PIBITI"]*2 + ["PIBIC_EM"]*2,
                "Quantidade": [120, 80, 40, 35, 25, 15]
            })
            fig_vol_modal = px.bar(df_vol_modal, x="Modalidade", y="Quantidade", color="Tipo", barmode="group", color_discrete_map=color_map)
            fig_vol_modal.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', legend_title_text="Tipo de Bolsa", height=420, margin=dict(t=20,b=20,l=20,r=20))
            st.plotly_chart(fig_vol_modal, use_container_width=True)

        with col_v2:
            chart_title("Alunos Bolsistas por Modalidade")
            df_bolsistas = pd.DataFrame({
                "Modalidade": ["Cotista", "Não Cotista"] * 3,
                "Tipo": ["PIBIC"]*2 + ["PIBITI"]*2 + ["PIBIC_EM"]*2,
                "Quantidade": [100, 60, 30, 25, 20, 10]
            })
            fig_bolsistas = px.bar(df_bolsistas, x="Modalidade", y="Quantidade", color="Tipo", barmode="group", color_discrete_map=color_map)
            fig_bolsistas.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', legend_title_text="Tipo de Bolsa", height=420, margin=dict(t=20,b=20,l=20,r=20))
            st.plotly_chart(fig_bolsistas, use_container_width=True)

        # --- Alunos Bolsistas por Unidade e por Grande Área ---
        chart_title("Bolsistas por Unidade e por Grande Área")
        col_u1, col_u2 = st.columns(2)

        with col_u1:
            df_bol_unidade = pd.DataFrame({
                "Unidade": ["Recife", "Garanhuns", "Petrolina"] * 3,
                "Tipo": ["PIBIC"]*3 + ["PIBITI"]*3 + ["PIBIC_EM"]*3,
                "Quantidade": [120, 40, 30, 30, 10, 8, 20, 5, 3]
            })
            fig_bol_unidade = px.bar(df_bol_unidade, x="Unidade", y="Quantidade", color="Tipo", barmode="group", color_discrete_map=color_map)
            fig_bol_unidade.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', legend_title_text="Tipo de Bolsa", height=420, margin=dict(t=30,b=30,l=30,r=30))
            st.plotly_chart(fig_bol_unidade, use_container_width=True)

        with col_u2:
            df_bol_area = pd.DataFrame({
                "Grande Area": ["Ciências Biológicas", "Engenharia", "Saúde Pública"] * 3,
                "Tipo": ["PIBIC"]*3 + ["PIBITI"]*3 + ["PIBIC_EM"]*3,
                "Quantidade": [80, 60, 40, 20, 30, 15, 10, 8, 5]
            })
            fig_bol_area = px.bar(df_bol_area, x="Grande Area", y="Quantidade", color="Tipo", barmode="group", color_discrete_map=color_map)
            fig_bol_area.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', legend_title_text="Tipo de Bolsa", height=420, margin=dict(t=30,b=30,l=30,r=30))
            st.plotly_chart(fig_bol_area, use_container_width=True)

        # --- Evolução do Número de Alunos Desistentes por Unidade (Voluntários vs Bolsistas) ---
        chart_title("Evolução do Número de Alunos Desistentes por Unidade (Voluntários vs Bolsistas)")
        unidades = ["Recife", "Garanhuns", "Petrolina"]
        anos_des = [2022, 2023, 2024, 2025]
        status_des = ["Voluntário", "Bolsista"]
        rows = []
        for ui, un in enumerate(unidades):
            for stt in status_des:
                for i, ano in enumerate(anos_des):
                    base = 30 if stt == "Voluntário" else 18
                    step = 6 if stt == "Voluntário" else 3
                    qtd = int(base + i * step + ui * 2)
                    rows.append({"Ano": ano, "Unidade": un, "Status": stt, "Quantidade": qtd})

        df_desistentes = pd.DataFrame(rows)

        fig_desist = px.line(
            df_desistentes,
            x='Ano',
            y='Quantidade',
            color='Unidade',
            facet_col='Status',
            markers=True,
            template='plotly_dark',
            color_discrete_map={
                'Recife': COLORS['Coral'],
                'Garanhuns': STRICTO['Unidade_2'],
                'Petrolina': STRICTO['Unidade_3']
            }
        )
        fig_desist.update_layout(height=420, margin=dict(t=30, b=30, l=30, r=30), legend_title_text='Unidade')
        fig_desist.update_xaxes(dtick=1)
        st.plotly_chart(fig_desist, use_container_width=True)

        # --- Ranking: Grupos de Pesquisa por Unidade e Curso (filtro por ano) ---
        chart_title("Ranking: Grupos de Pesquisa por Unidade e Curso (Filtro: ano selecionado)")
        # Mock de grupos por unidade/curso/ano
        grupos = [f"Grupo {c}{i}" for c in ['A','B','C','D','E','F'] for i in range(1,4)]
        cursos = ["Biotecnologia", "Engenharia", "Saúde Pública"]
        rows = []
        for ano in [2022, 2023, 2024, 2025]:
            for un in unidades:
                for curso in cursos:
                    for g in range(3):
                        nome = f"Grupo {curso[:3]}-{g+1} {un}"
                        membros = max(3, int(np.random.poisson(lam=12) + (0 if un != 'Recife' else 8)))
                        rows.append({"Ano": ano, "Unidade": un, "Curso": curso, "Grupo": nome, "Membros": membros})

        df_groups = pd.DataFrame(rows)

        # Filtrar pelo ano selecionado na sidebar
        df_year = df_groups[df_groups['Ano'] == int(ano_selected)]

        # Selecionar top N grupos por unidade (ranking)
        top_n = 6
        parts = []
        for un in df_year['Unidade'].unique():
            tmp = df_year[df_year['Unidade'] == un].sort_values('Membros', ascending=False).head(top_n)
            parts.append(tmp)
        if parts:
            df_top_groups = pd.concat(parts)
        else:
            df_top_groups = df_year.copy()

        # Gráfico facetado horizontal por Unidade, ordenado por Membros (cada facet mostra ranking)
        fig_rank = px.bar(
            df_top_groups,
            x='Membros',
            y='Grupo',
            color='Curso',
            facet_col='Unidade',
            orientation='h',
            template='plotly_dark',
            color_discrete_sequence=[COLORS['Coral'], COLORS['Ciano'], COLORS['Roxo']]
        )
        fig_rank.update_layout(height=520, margin=dict(t=30, b=30, l=10, r=10), showlegend=True)
        fig_rank.update_yaxes(tickfont=dict(size=11))
        st.plotly_chart(fig_rank, use_container_width=True)

        


# =========================================================
# TELA 3: INOVAÇÃO
# =========================================================
elif tela == "Inovação":
    df_inov = DATASETS.get("inovacao_dashboard", pd.DataFrame()).copy()
    df_pi = DATASETS.get("inovacao_pi", pd.DataFrame()).copy()

    ano_col_inov = _find_col(df_inov, ["ano"])
    receita_col = _find_col(df_inov, ["receita"])
    bolsas_total_col = _find_col(df_inov, ["total_de_bolsas"])
    projeto_col = _find_col(df_inov, ["projeto"])
    cidade_col = _find_col(df_inov, ["cidade"])
    setor_col = _find_col(df_inov, ["setor"])
    natureza_col = _find_col(df_inov, ["natureza"])
    segmento_col = _find_col(df_inov, ["segmento"])
    regiao_col = _find_col(df_inov, ["regiao"])
    trl_col = _find_col(df_inov, ["trl"])
    vigente_col = _find_col(df_inov, ["vigente", "vigencia"])
    inst_col = _find_col(df_inov, ["instituicao", "instituicao_1"])

    if receita_col:
        df_inov["_receita_num"] = _to_number(df_inov[receita_col])
    else:
        df_inov["_receita_num"] = np.nan

    if bolsas_total_col:
        df_inov["_bolsas_num"] = _to_number(df_inov[bolsas_total_col])
    else:
        df_inov["_bolsas_num"] = np.nan

    if ano_col_inov and not df_inov.empty:
        df_inov["_ano"] = pd.to_numeric(df_inov[ano_col_inov], errors="coerce")
    else:
        df_inov["_ano"] = np.nan

    df_curr = df_inov[df_inov["_ano"] == int(ano_selected)] if "_ano" in df_inov.columns else pd.DataFrame()
    df_prev = df_inov[df_inov["_ano"] == int(ano_selected) - 1] if "_ano" in df_inov.columns else pd.DataFrame()

    recursos_curr = float(df_curr["_receita_num"].sum()) if not df_curr.empty else 14_500_000.0
    recursos_prev = float(df_prev["_receita_num"].sum()) if not df_prev.empty else recursos_curr
    bolsas_curr = float(df_curr["_bolsas_num"].sum()) if not df_curr.empty else 25.0
    bolsas_prev = float(df_prev["_bolsas_num"].sum()) if not df_prev.empty else bolsas_curr

    col_deposito = _find_col(df_pi, ["data_de_deposito"])
    if col_deposito and not df_pi.empty:
        df_pi["_ano_dep"] = pd.to_datetime(df_pi[col_deposito], errors="coerce", dayfirst=True).dt.year
        patentes_curr = int((df_pi["_ano_dep"] == int(ano_selected)).sum())
        patentes_prev = int((df_pi["_ano_dep"] == int(ano_selected) - 1).sum())
        total_patentes = int((df_pi["_ano_dep"] <= int(ano_selected)).sum())
    else:
        patentes_curr, patentes_prev, total_patentes = 14, 13, 14

    col1, col2, col3 = st.columns(3)
    with col1:
        kpi_card_delta("TOTAL DE RECURSOS CAPTADOS", _format_million_brl(recursos_curr), _pct_delta(recursos_curr, recursos_prev), COLORS["Ciano"])
    with col2:
        kpi_card_delta("TOTAL DE BOLSAS INOVAÇÃO", _format_int(bolsas_curr), _pct_delta(bolsas_curr, bolsas_prev), COLORS["Verde Limao"])
    with col3:
        kpi_card_delta("TOTAL DE PATENTES", _format_int(total_patentes), _pct_delta(patentes_curr, patentes_prev), COLORS["Amarelo"])

    col_line1, col_line2 = st.columns(2)

    with col_line1:
        chart_title("Evolução de Propriedade Intelectual - PATENTES por ano")
        if not df_pi.empty and "_ano_dep" in df_pi.columns:
            df_patentes_ano = (
                df_pi.dropna(subset=["_ano_dep"])
                .groupby("_ano_dep", as_index=False)
                .size()
                .rename(columns={"_ano_dep": "Ano", "size": "Patentes"})
                .sort_values("Ano")
            )
        else:
            df_patentes_ano = pd.DataFrame(
                {
                    "Ano": [2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025],
                    "Patentes": [0, 1, 1, 2, 3, 4, 6, 8, 14],
                }
            )
        fig_patentes_ano = px.line(
            df_patentes_ano,
            x="Ano",
            y="Patentes",
            markers=True,
            template="plotly_dark",
            color_discrete_sequence=[COLORS["Amarelo"]]
        )
        fig_patentes_ano.update_traces(line=dict(width=4), marker=dict(size=10))
        fig_patentes_ano.update_layout(height=360, margin=dict(t=20, b=20, l=20, r=20), showlegend=False)
        fig_patentes_ano.update_yaxes(title_text="Quantidade de patentes")
        fig_patentes_ano.update_xaxes(title_text="Ano")
        st.plotly_chart(fig_patentes_ano, use_container_width=True)

    with col_line2:
        chart_title("Evolução do Número de Projetos Vigentes")
        st.caption("Exibe a evolução do número de convênios formalizados por ano, com os valores captados e o crescimento em relação ao ano anterior.")
        if not df_inov.empty and ano_col_inov:
            df_vig = df_inov.copy()
            if vigente_col:
                vig_series = df_vig[vigente_col].astype(str).str.lower()
                mask_vig = vig_series.str.contains("vig|sim|s|1", regex=True, na=False)
                if mask_vig.any():
                    df_vig = df_vig[mask_vig]
            df_vigentes = (
                df_vig.dropna(subset=["_ano"])
                .groupby("_ano", as_index=False)
                .agg(
                    **{
                        "Convênios formalizados": (projeto_col if projeto_col else "_ano", "count"),
                        "Valores captados (R$ mi)": ("_receita_num", "sum"),
                    }
                )
                .rename(columns={"_ano": "Ano"})
                .sort_values("Ano")
            )
            df_vigentes["Valores captados (R$ mi)"] = df_vigentes["Valores captados (R$ mi)"] / 1_000_000
        else:
            df_vigentes = pd.DataFrame(
                {
                    "Ano": [2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025],
                    "Convênios formalizados": [3, 4, 6, 8, 11, 13, 17, 21, 26],
                    "Valores captados (R$ mi)": [0.8, 1.1, 1.8, 2.7, 4.0, 5.1, 6.4, 8.2, 10.0],
                }
            )
        df_vigentes["Crescimento %"] = df_vigentes["Convênios formalizados"].pct_change().fillna(0) * 100
        fig_vigentes = make_subplots(specs=[[{"secondary_y": True}]])
        fig_vigentes.add_trace(
            go.Bar(
                x=df_vigentes["Ano"],
                y=df_vigentes["Convênios formalizados"],
                name="Convênios formalizados",
                marker_color=COLORS["Ciano"],
                hovertemplate="Ano: %{x}<br>Convênios: %{y}<br>Captado: R$ %{customdata[0]:.1f} mi<extra></extra>",
                customdata=df_vigentes[["Valores captados (R$ mi)"]].to_numpy(),
            ),
            secondary_y=False,
        )
        fig_vigentes.add_trace(
            go.Scatter(
                x=df_vigentes["Ano"],
                y=df_vigentes["Crescimento %"],
                name="Crescimento vs. ano anterior",
                mode="lines+markers+text",
                line=dict(color=COLORS["Coral"], width=4),
                marker=dict(size=9),
                text=["-", "", "", "", "", "", "", "", ""],
                hovertemplate="Ano: %{x}<br>Crescimento: %{y:.1f}%<extra></extra>",
            ),
            secondary_y=True,
        )
        fig_vigentes.update_layout(
            template="plotly_dark",
            height=360,
            margin=dict(t=20, b=20, l=20, r=20),
            legend_title_text="",
        )
        fig_vigentes.update_xaxes(title_text="Ano")
        fig_vigentes.update_yaxes(title_text="Número de convênios", secondary_y=False)
        fig_vigentes.update_yaxes(title_text="Crescimento (%)", secondary_y=True)
        st.plotly_chart(fig_vigentes, use_container_width=True)

    col_idt1, col_idt2 = st.columns(2)

    with col_idt1:
        chart_title("Projetos por ano")
        if not df_inov.empty and ano_col_inov:
            df_projetos = (
                df_inov.dropna(subset=["_ano"])
                .groupby("_ano", as_index=False)
                .agg(**{"Quantidade de Projetos": (projeto_col if projeto_col else "_ano", "count")})
                .rename(columns={"_ano": "Ano"})
                .sort_values("Ano")
            )
        else:
            df_projetos = pd.DataFrame(
                {
                    "Ano": [2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025],
                    "Quantidade de Projetos": [1, 2, 7, 12, 22, 28, 52, 64, 33],
                }
            )
        fig_proj_ano = px.bar(
            df_projetos,
            x="Ano",
            y="Quantidade de Projetos",
            color="Ano",
            template="plotly_dark",
            color_discrete_sequence=[COLORS["Ciano"], COLORS["Coral"], COLORS["Amarelo"], COLORS["Roxo"], COLORS["Verde Limao"], COLORS["Ciano"], COLORS["Coral"], COLORS["Amarelo"], COLORS["Coral"]]
        )
        fig_proj_ano.update_layout(height=420, margin=dict(t=20, b=20, l=20, r=20), showlegend=False)
        fig_proj_ano.update_yaxes(title_text="Quantidade de Projetos")
        fig_proj_ano.update_xaxes(title_text="Ano de realização")
        st.plotly_chart(fig_proj_ano, use_container_width=True)

    with col_idt2:
        chart_title("Projetos por Cidade")
        if not df_inov.empty and cidade_col:
            df_cidade = _counts_df(df_inov[cidade_col].fillna("Não informado"), "Cidade", "Projetos").sort_values("Projetos", ascending=True)
        else:
            df_cidade = pd.DataFrame(
                {
                    "Cidade": [
                        "Abreu e Lima - PE", "Arcoverde", "Arcoverde - PE", "Barueri - SP", "Betânia - CE",
                        "Boiutva - SP", "Brasília - DF", "Cabo - PE", "Camaragibe - PE", "Canhotinho - PE",
                        "Fortaleza - CE", "Foz do Iguaçu - PR", "Garanhuns - PE", "Ilha de Itamaracá - PE",
                        "Jandira - SP", "Maceió - AL", "Maringá - PR", "Olinda - PE", "Primavera - PE",
                    ],
                    "Projetos": [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 135],
                }
            )
        # Usar bolhas (scatter) para facilitar a relação entre cidade e volume
        fig_cidade = px.scatter(
            df_cidade,
            x="Cidade",
            y="Projetos",
            size="Projetos",
            color="Cidade",
            template="plotly_dark",
            size_max=55,
            hover_name="Cidade",
        )
        fig_cidade.update_traces(marker=dict(line=dict(width=0)))
        fig_cidade.update_layout(height=420, margin=dict(t=20, b=20, l=20, r=20), showlegend=False)
        st.plotly_chart(fig_cidade, use_container_width=True)

    col_status_proj, col_receita_proj = st.columns(2)

    with col_status_proj:
        chart_title("Status dos Projetos")
        if not df_inov.empty and vigente_col:
            df_status = _counts_df(df_inov[vigente_col].fillna("Não informado").astype(str).str.title(), "Status", "Quantidade")
        else:
            df_status = pd.DataFrame(
                {
                    "Status": ["Em andamento", "Em formalização", "Em tramitação", "Finalizado"],
                    "Quantidade": [72, 2, 8, 18],
                }
            )
        fig_status = px.pie(
            df_status,
            names="Status",
            values="Quantidade",
            hole=0.55,
            template="plotly_dark",
            color="Status",
            color_discrete_map={
                "Em andamento": COLORS["Coral"],
                "Em formalização": COLORS["Amarelo"],
                "Em tramitação": COLORS["Verde Limao"],
                "Finalizado": COLORS["Roxo"]
            }
        )
        fig_status.update_layout(height=360, margin=dict(t=20, b=20, l=20, r=20), showlegend=True)
        st.plotly_chart(fig_status, use_container_width=True)

    with col_receita_proj:
        chart_title("Receita dos Projetos")
        if not df_inov.empty and vigente_col:
            df_receita_proj = (
                df_inov.assign(Status=df_inov[vigente_col].fillna("Não informado").astype(str).str.title())
                .groupby("Status", as_index=False)["_receita_num"]
                .sum()
                .rename(columns={"_receita_num": "Receita"})
            )
            df_receita_proj["Receita"] = df_receita_proj["Receita"] / 1_000_000
        else:
            df_receita_proj = pd.DataFrame(
                {
                    "Status": ["Em andamento", "Em formalização", "Em tramitação", "Finalizado"],
                    "Receita": [0.8, 0.2, 0.5, 1.6],
                }
            )
        fig_receita_proj = px.bar(
            df_receita_proj,
            x="Status",
            y="Receita",
            template="plotly_dark",
            color="Status",
            color_discrete_map={
                "Em andamento": COLORS["Coral"],
                "Em formalização": COLORS["Amarelo"],
                "Em tramitação": COLORS["Verde Limao"],
                "Finalizado": COLORS["Roxo"]
            }
        )
        fig_receita_proj.update_layout(height=360, margin=dict(t=20, b=20, l=20, r=20), showlegend=False)
        fig_receita_proj.update_yaxes(title_text="Receita")
        fig_receita_proj.update_xaxes(title_text="Status")
        st.plotly_chart(fig_receita_proj, use_container_width=True)

    col_idt3, col_idt4 = st.columns(2)

    with col_idt3:
        chart_title("Setor dos projetos")
        if not df_inov.empty and setor_col:
            df_setor = _counts_df(df_inov[setor_col].fillna("Não informado").astype(str).str.title(), "Setor", "Quantidade")
        else:
            df_setor = pd.DataFrame({"Setor": ["Privado", "Público"], "Quantidade": [75, 25]})
        fig_setor = px.pie(
            df_setor,
            names="Setor",
            values="Quantidade",
            hole=0.55,
            template="plotly_dark",
            color="Setor",
            color_discrete_map={"Privado": COLORS["Ciano"], "Público": COLORS["Coral"]}
        )
        fig_setor.update_layout(height=380, margin=dict(t=20, b=20, l=20, r=20), showlegend=True)
        st.plotly_chart(fig_setor, use_container_width=True)

    with col_idt4:
        chart_title("Setores Anuais dos Projetos")
        if not df_inov.empty and setor_col and ano_col_inov:
            tmp_setores = df_inov.copy()
            tmp_setores["_setor_norm"] = tmp_setores[setor_col].fillna("Não informado").astype(str).str.lower()
            tmp_setores["_setor_cat"] = np.where(tmp_setores["_setor_norm"].str.contains("priv"), "Setor privado", "Setor público")
            df_setores_anuais = (
                tmp_setores.dropna(subset=["_ano"]).groupby(["_ano", "_setor_cat"]).size().reset_index(name="Quantidade")
            )
            df_setores_anuais = (
                df_setores_anuais.pivot(index="_ano", columns="_setor_cat", values="Quantidade")
                .fillna(0)
                .reset_index()
                .rename(columns={"_ano": "Ano"})
            )
        else:
            df_setores_anuais = pd.DataFrame(
                {
                    "Ano": [2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025],
                    "Setor privado": [1, 2, 5, 10, 20, 23, 36, 49, 19],
                    "Setor público": [0, 0, 1, 2, 2, 5, 8, 15, 13],
                }
            )
        fig_setores_anuais = px.bar(
            df_setores_anuais,
            x="Ano",
            y=["Setor privado", "Setor público"],
            barmode="group",
            template="plotly_dark",
            color_discrete_sequence=[COLORS["Ciano"], COLORS["Coral"]]
        )
        fig_setores_anuais.update_layout(height=420, margin=dict(t=20, b=20, l=20, r=20), legend_title_text="Setor")
        fig_setores_anuais.update_xaxes(title_text="Ano")
        fig_setores_anuais.update_yaxes(title_text="Quantidade de Projetos")
        st.plotly_chart(fig_setores_anuais, use_container_width=True)

    col_idt5, col_idt6 = st.columns(2)

    with col_idt5:
        chart_title("Natureza dos Projetos")
        if not df_inov.empty and natureza_col:
            df_natureza = _counts_df(df_inov[natureza_col].fillna("Não informado").astype(str), "Natureza", "Quantidade")
        else:
            df_natureza = pd.DataFrame(
                {
                    "Natureza": ["Inovação Aberta", "PD&I", "RESITEC", "Serviço Tecnológico", "Termo de Confiabilidade"],
                    "Quantidade": [4, 82, 6, 3, 2],
                }
            )
        fig_natureza = px.pie(
            df_natureza,
            names="Natureza",
            values="Quantidade",
            hole=0.55,
            template="plotly_dark",
            color="Natureza",
            color_discrete_sequence=[COLORS["Ciano"], COLORS["Coral"], COLORS["Verde Limao"], COLORS["Amarelo"], COLORS["Roxo"]]
        )
        fig_natureza.update_layout(height=420, margin=dict(t=20, b=20, l=20, r=20), showlegend=True)
        st.plotly_chart(fig_natureza, use_container_width=True)

    with col_idt6:
        chart_title("Quantidade de projetos por Segmento")
        if not df_inov.empty and segmento_col:
            df_segmento = _counts_df(df_inov[segmento_col].fillna("Não informado").astype(str), "Segmento", "Projetos").sort_values("Projetos", ascending=True)
        else:
            df_segmento = pd.DataFrame(
                {
                    "Segmento": [
                        "Agronegócio", "Construção Civil", "Educação", "Eventos", "Gestão Municipal",
                        "Gestão Pública", "Indústria Aeroespacial", "Indústria Alcoquímica", "Indústria Alimentícia",
                        "Indústria Automotiva", "Indústria de Bebidas Alcoólicas", "Indústria de Eletrônicos",
                        "Indústria de Embalagens", "Indústria de Limpeza e Higiene", "Indústria de Materiais de Construção",
                        "Indústria de Produtos Sanitários", "Indústria de Vidros", "Indústria Petroquímica",
                        "Indústria Química", "Indústria Siderúrgica", "Indústria 4.0", "Inovação Social",
                        "Pesquisa e Desenvolvimento", "Saúde", "Setor de Energia", "Setor Hospitalar",
                    ],
                    "Projetos": [1, 10, 4, 9, 6, 13, 1, 4, 7, 9, 4, 6, 7, 3, 1, 2, 1, 5, 3, 2, 1, 4, 21, 7, 2, 4],
                }
            )
        fig_segmento = px.bar(
            df_segmento,
            x="Projetos",
            y="Segmento",
            orientation="h",
            template="plotly_dark",
            color="Segmento"
        )
        fig_segmento.update_layout(height=420, margin=dict(t=20, b=20, l=20, r=20), showlegend=True)
        st.plotly_chart(fig_segmento, use_container_width=True)

    st.markdown("### Outros Indicadores de Projetos")
    col_extra1, col_extra2 = st.columns(2)
    col_extra3, col_extra4 = st.columns([2, 1])

    with col_extra1:
        chart_title("Projetos por Região de Desenvolvimento")
        if not df_inov.empty and regiao_col:
            df_regiao = _counts_df(df_inov[regiao_col].fillna("Não informado").astype(str), "Região", "Projetos").sort_values("Projetos", ascending=True)
        else:
            df_regiao = pd.DataFrame(
                {
                    "Região": ["Agreste", "Petrolina, Garanhuns, Arcoverde", "RMR - Núcleo Centro", "Sertão de Itaparica", "Sertão do Moxotó", "Agreste Meridional", "RMR"],
                    "Projetos": [1, 1, 1, 2, 3, 2, 5],
                }
            )
        fig_regiao = px.bar(
            df_regiao,
            x="Projetos",
            y="Região",
            orientation="h",
            template="plotly_dark",
            color="Região"
        )
        fig_regiao.update_layout(height=520, margin=dict(t=20, b=20, l=20, r=20), showlegend=True)
        st.plotly_chart(fig_regiao, use_container_width=True)

    with col_extra2:
        chart_title("Receita Média Anual por Projeto")
        if not df_inov.empty and ano_col_inov:
            df_receita_media = (
                df_inov.dropna(subset=["_ano"]).groupby("_ano", as_index=False)["_receita_num"].mean().rename(
                    columns={"_ano": "Ano", "_receita_num": "Faturamento médio"}
                )
            )
        else:
            df_receita_media = pd.DataFrame(
                {
                    "Ano": [2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025],
                    "Faturamento médio": [56000, 82000, 240000, 185000, 300000, 255000, 170000, 260000, 540000],
                }
            )
        fig_receita_media = px.bar(
            df_receita_media,
            x="Ano",
            y="Faturamento médio",
            template="plotly_dark",
            color="Faturamento médio",
            color_continuous_scale=[COLORS["Verde Limao"], COLORS["Ciano"], COLORS["Coral"]]
        )
        fig_receita_media.update_layout(height=420, margin=dict(t=20, b=20, l=20, r=20), showlegend=False)
        fig_receita_media.update_yaxes(title_text="Faturamento médio")
        fig_receita_media.update_xaxes(title_text="Ano")
        st.plotly_chart(fig_receita_media, use_container_width=True)

    with col_extra3:
        chart_title("Receita Anual dos Projetos")
        if not df_inov.empty and ano_col_inov:
            df_receita = (
                df_inov.dropna(subset=["_ano"]).groupby("_ano", as_index=False)["_receita_num"].sum().rename(
                    columns={"_ano": "Ano", "_receita_num": "Faturamento"}
                )
            )
        else:
            df_receita = pd.DataFrame(
                {
                    "Ano": [2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025],
                    "Faturamento": [0, 0, 1800000, 2300000, 6500000, 7000000, 8500000, 16700000, 17500000],
                }
            )
        fig_receita = px.bar(
            df_receita,
            x="Ano",
            y="Faturamento",
            template="plotly_dark",
            color="Faturamento",
            color_continuous_scale=[COLORS["Ciano"], COLORS["Roxo"], COLORS["Coral"]]
        )
        fig_receita.update_layout(height=420, margin=dict(t=20, b=20, l=20, r=20), showlegend=False)
        fig_receita.update_yaxes(title_text="Faturamento aproximado ao decorrer dos anos")
        fig_receita.update_xaxes(title_text="Ano")
        st.plotly_chart(fig_receita, use_container_width=True)

    with col_extra4:
        qtd_empresas = int(df_inov[inst_col].nunique()) if (not df_inov.empty and inst_col) else 162
        qtd_projetos = int(len(df_inov)) if not df_inov.empty else 229
        receita_total = float(df_inov["_receita_num"].sum()) if not df_inov.empty else 9_000_376.82
        receita_fmt = f"R$ {receita_total:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        # Usar a função de card consistente com o resto do dashboard
        kpi_card("Quantidade de Empresas", _format_int(qtd_empresas), "#4f88d8")
        kpi_card("Quantidade de Projetos", _format_int(qtd_projetos), "#4f88d8")
        kpi_card("Receita Total", receita_fmt, "#77a6eb")

    st.markdown("### Bolsas e Nível de Maturidade")
    col_inov_1, col_inov_2 = st.columns(2)

    with col_inov_1:
        chart_title("Bolsas de Inovação")
        bolsa_cols = [c for c in df_inov.columns if c.startswith("bolsas_")] if not df_inov.empty else []
        if bolsa_cols:
            df_bolsas_inovacao = pd.DataFrame(
                {
                    "Categoria": [c.replace("bolsas_", "").replace("_", " ").title() for c in bolsa_cols],
                    "Quantidade": [float(_to_number(df_inov[c]).sum()) for c in bolsa_cols],
                }
            )
        else:
            df_bolsas_inovacao = pd.DataFrame(
                {
                    "Categoria": ["Médio/Aprendiz", "Coordenador", "Pesquisador", "Doutorandos", "Mestrandos", "Graduandos"],
                    "Quantidade": [7, 129, 212, 92, 87, 202],
                }
            )
        fig_bolsas_inovacao = px.bar(
            df_bolsas_inovacao,
            x="Quantidade",
            y="Categoria",
            orientation="h",
            template="plotly_dark",
            color="Categoria",
            color_discrete_sequence=[COLORS["Coral"], COLORS["Ciano"], COLORS["Amarelo"], COLORS["Roxo"], COLORS["Verde Limao"], COLORS["Ciano"]]
        )
        fig_bolsas_inovacao.update_layout(height=360, margin=dict(t=20, b=20, l=20, r=20), showlegend=False)
        fig_bolsas_inovacao.update_xaxes(title_text="Quantidade")
        st.plotly_chart(fig_bolsas_inovacao, use_container_width=True)

    with col_inov_2:
        chart_title("TRL dos Projetos de Inovação")
        if not df_inov.empty and trl_col:
            df_trl = _counts_df(df_inov[trl_col].fillna("Não informado").astype(str), "TRL", "Projetos").sort_values("TRL")
        else:
            df_trl = pd.DataFrame({"TRL": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9], "Projetos": [4, 1, 2, 10, 7, 9, 10, 6, 2, 12]})
        fig_trl = px.bar(
            df_trl,
            x="TRL",
            y="Projetos",
            template="plotly_dark",
            color="Projetos",
            color_continuous_scale=[COLORS["Ciano"], COLORS["Roxo"], COLORS["Coral"]]
        )
        fig_trl.update_layout(height=360, margin=dict(t=20, b=20, l=20, r=20), showlegend=False)
        fig_trl.update_xaxes(title_text="TRL")
        fig_trl.update_yaxes(title_text="Quantidade de Projetos")
        st.plotly_chart(fig_trl, use_container_width=True)

    total_bolsas_proj = int(df_inov["_bolsas_num"].sum()) if not df_inov.empty else 612
    st.markdown(f"<div style='background:#e8a3a3;padding:16px 14px;border-radius:6px;margin:10px 0 18px 0;text-align:center;color:#111;'><div style='font-size:18px;font-weight:700;'>Total de Bolsas em Projetos</div><div style='font-size:44px;line-height:1.0;font-weight:700;margin-top:6px;'>{total_bolsas_proj}</div></div>", unsafe_allow_html=True)
    
elif tela == "Desenvolvimento Tecnológico":
    df_dt = DATASETS.get("dt_dados_json", pd.DataFrame()).copy()
    dt_data_col = _find_col(df_dt, ["data"])
    dt_reg_col = _find_col(df_dt, ["regiao"])
    dt_prod_col = _find_col(df_dt, ["produto"])
    dt_qtd_col = _find_col(df_dt, ["quantidade"])
    dt_val_col = _find_col(df_dt, ["valortotal", "valor_total"])

    if not df_dt.empty and dt_data_col and dt_val_col:
        df_dt["Data"] = pd.to_datetime(df_dt[dt_data_col], errors="coerce")
        df_dt["Mês"] = df_dt["Data"].dt.to_period("M").astype(str)
        df_dt["ValorTotal"] = _to_number(df_dt[dt_val_col])
        if dt_qtd_col:
            df_dt["Quantidade"] = _to_number(df_dt[dt_qtd_col])
        else:
            df_dt["Quantidade"] = 1
        if dt_reg_col:
            df_dt["Região"] = df_dt[dt_reg_col].astype(str)
        else:
            df_dt["Região"] = "Não informado"
        if dt_prod_col:
            df_dt["Produto"] = df_dt[dt_prod_col].astype(str)
        else:
            df_dt["Produto"] = "Não informado"
        df_dt = df_dt.dropna(subset=["Data"]).copy()
    else:
        df_dt = pd.DataFrame(
            [
                {"Data": "2025-01-15", "Região": "Sudeste", "Produto": "Notebook", "Quantidade": 2, "ValorTotal": 7000},
                {"Data": "2025-01-16", "Região": "Sul", "Produto": "Impressora", "Quantidade": 1, "ValorTotal": 1200},
                {"Data": "2025-02-03", "Região": "Nordeste", "Produto": "Monitor", "Quantidade": 3, "ValorTotal": 2400},
                {"Data": "2025-02-10", "Região": "Centro-Oeste", "Produto": "Teclado", "Quantidade": 5, "ValorTotal": 750},
                {"Data": "2025-03-01", "Região": "Sudeste", "Produto": "Mouse", "Quantidade": 10, "ValorTotal": 1000},
                {"Data": "2025-03-12", "Região": "Sul", "Produto": "Notebook", "Quantidade": 1, "ValorTotal": 3600},
                {"Data": "2025-03-25", "Região": "Nordeste", "Produto": "Impressora", "Quantidade": 2, "ValorTotal": 2200},
            ]
        )
        df_dt["Data"] = pd.to_datetime(df_dt["Data"])
        df_dt["Mês"] = df_dt["Data"].dt.to_period("M").astype(str)

    col_dt1, col_dt2 = st.columns(2)

    with col_dt1:
        chart_title("Evolução do Valor Total por Mês")
        df_mes = df_dt.groupby("Mês", as_index=False)["ValorTotal"].sum().sort_values("Mês")
        fig_mes = px.line(
            df_mes,
            x="Mês",
            y="ValorTotal",
            markers=True,
            template="plotly_dark",
            color_discrete_sequence=[COLORS["Ciano"]],
        )
        fig_mes.update_traces(line=dict(width=4), marker=dict(size=9))
        fig_mes.update_layout(height=340, margin=dict(t=20, b=20, l=20, r=20), showlegend=False, font=dict(size=12))
        fig_mes.update_yaxes(title_text="Valor Total (R$)")
        fig_mes.update_xaxes(title_text="Mês")
        st.plotly_chart(fig_mes, use_container_width=True)

    with col_dt2:
        chart_title("Valor Total por Região")
        df_regiao = df_dt.groupby("Região", as_index=False)["ValorTotal"].sum().sort_values("ValorTotal", ascending=True)
        fig_regiao_dt = px.scatter(
            df_regiao,
            x="Região",
            y="ValorTotal",
            template="plotly_dark",
            color="Região",
            size="ValorTotal",
            size_max=55,
            color_discrete_sequence=[COLORS["Coral"], COLORS["Ciano"], COLORS["Amarelo"], COLORS["Verde Limao"]],
        )
        fig_regiao_dt.update_layout(height=340, margin=dict(t=20, b=20, l=20, r=20), showlegend=False, font=dict(size=12))
        fig_regiao_dt.update_xaxes(title_text="Região")
        fig_regiao_dt.update_yaxes(title_text="Valor Total (R$)")
        st.plotly_chart(fig_regiao_dt, use_container_width=True)

    col_dt3, col_dt4 = st.columns(2)

    with col_dt3:
        chart_title("Quantidade por Produto")
        df_produto = df_dt.groupby("Produto", as_index=False)["Quantidade"].sum().sort_values("Quantidade", ascending=True)
        fig_produto = px.bar(
            df_produto,
            x="Quantidade",
            y="Produto",
            orientation="h",
            template="plotly_dark",
            color="Produto",
            color_discrete_sequence=[COLORS["Roxo"], COLORS["Amarelo"], COLORS["Ciano"], COLORS["Coral"]],
        )
        fig_produto.update_layout(height=340, margin=dict(t=20, b=20, l=20, r=20), showlegend=False, font=dict(size=12))
        fig_produto.update_xaxes(title_text="Quantidade")
        fig_produto.update_yaxes(title_text="Produto")
        st.plotly_chart(fig_produto, use_container_width=True)


# =========================================================
# TELA 4: PÓS-GRADUAÇÃO
# =========================================================
elif tela == "Pós-Graduação":
    df_stricto_real = DATASETS.get("pos_stricto", pd.DataFrame()).copy()
    df_lato_real = DATASETS.get("pos_lato", pd.DataFrame()).copy()

    col_programa = _find_col(df_stricto_real, ["programa"])
    col_situacao = _find_col(df_stricto_real, ["situacao"])
    col_nivel = _find_col(df_stricto_real, ["nivel"])
    col_masc = _find_col(df_stricto_real, ["masculino"])
    col_fem = _find_col(df_stricto_real, ["feminino"])
    col_total = _find_col(df_stricto_real, ["total"])

    if not df_stricto_real.empty:
        if col_total:
            df_stricto_real["_total"] = _to_number(df_stricto_real[col_total])
        elif col_masc and col_fem:
            df_stricto_real["_total"] = _to_number(df_stricto_real[col_masc]) + _to_number(df_stricto_real[col_fem])
        else:
            df_stricto_real["_total"] = 0

        if col_nivel:
            nivel_up = df_stricto_real[col_nivel].astype(str).str.upper()
            mask_mes = nivel_up.str.contains("MESTR", na=False)
            mask_dou = nivel_up.str.contains("DOUT", na=False)
        else:
            mask_mes = pd.Series([False] * len(df_stricto_real))
            mask_dou = pd.Series([False] * len(df_stricto_real))

        if col_situacao:
            sit_up = df_stricto_real[col_situacao].astype(str).str.upper()
            mask_tit = sit_up.str.contains("TITUL", na=False)
            mask_des = sit_up.str.contains("DESIST", na=False)
            mask_mat = sit_up.str.contains("MATRIC", na=False)
        else:
            mask_tit = pd.Series([False] * len(df_stricto_real))
            mask_des = pd.Series([False] * len(df_stricto_real))
            mask_mat = pd.Series([True] * len(df_stricto_real))

        kpi_prog = int(df_stricto_real[col_programa].nunique()) if col_programa else 12
        kpi_mes = int(df_stricto_real.loc[mask_mes, col_programa].nunique()) if col_programa else 8
        kpi_dou = int(df_stricto_real.loc[mask_dou, col_programa].nunique()) if col_programa else 4
        kpi_mat_mes = float(df_stricto_real.loc[mask_mes & mask_mat, "_total"].sum())
        kpi_tit_mes = float(df_stricto_real.loc[mask_mes & mask_tit, "_total"].sum())
        kpi_mat_dou = float(df_stricto_real.loc[mask_dou & mask_mat, "_total"].sum())
        kpi_tit_dou = float(df_stricto_real.loc[mask_dou & mask_tit, "_total"].sum())
        total_tit = float(df_stricto_real.loc[mask_tit, "_total"].sum())
        total_des = float(df_stricto_real.loc[mask_des, "_total"].sum())
        kpi_indice_tit = (total_tit / (total_tit + total_des) * 100.0) if (total_tit + total_des) > 0 else 0.0
    else:
        kpi_prog, kpi_mes, kpi_dou = 12, 8, 4
        kpi_mat_mes, kpi_tit_mes, kpi_mat_dou, kpi_tit_dou = 245, 60, 88, 18
        kpi_indice_tit = 92.0

    col_lato_unidade = _find_col(df_lato_real, ["unidade"])
    col_lato_matric = _find_col(df_lato_real, ["alunos_matriculados_2025"])
    col_lato_egressos = _find_col(df_lato_real, ["egressos_ano_2025"])
    col_lato_natureza = _find_col(df_lato_real, ["natureza"])

    if not df_lato_real.empty:
        lato_programas = int(len(df_lato_real))
        lato_matric = float(_to_number(df_lato_real[col_lato_matric]).sum()) if col_lato_matric else 1200
        lato_tit = float(_to_number(df_lato_real[col_lato_egressos]).sum()) if col_lato_egressos else 950
        lato_idx = (lato_tit / lato_matric * 100.0) if lato_matric > 0 else 0.0
    else:
        lato_programas, lato_matric, lato_tit, lato_idx = 35, 1200, 950, 86.0

    tipo_pos = st.selectbox("Selecione a Categoria:", ["Stricto Sensu", "Lato Sensu"])

    st.markdown("### Indicadores de Desempenho vs. Ano Anterior")

    if tipo_pos == "Stricto Sensu":
        # --- KPIs Stricto Sensu ---
        kpi_cols = st.columns(8)
        with kpi_cols[0]: kpi_card_delta("Nº de Programas", _format_int(kpi_prog), 0.0, COLORS["Amarelo"])
        with kpi_cols[1]: kpi_card_delta("Nº de Mestrados", _format_int(kpi_mes), 0.0, COLORS["Ciano"])
        with kpi_cols[2]: kpi_card_delta("Alunos Matriculados - Mestrado", _format_int(kpi_mat_mes), 0.0, COLORS["Ciano"])
        with kpi_cols[3]: kpi_card_delta("Alunos Titulados - Mestrado", _format_int(kpi_tit_mes), 0.0, COLORS["Ciano"])
        with kpi_cols[4]: kpi_card_delta("Nº de Doutorados", _format_int(kpi_dou), 0.0, COLORS["Coral"])
        with kpi_cols[5]: kpi_card_delta("Alunos Matriculados - Doutorado", _format_int(kpi_mat_dou), 0.0, COLORS["Coral"])
        with kpi_cols[6]: kpi_card_delta("Alunos Titulados - Doutorado", _format_int(kpi_tit_dou), 0.0, COLORS["Coral"])
        with kpi_cols[7]: kpi_card_delta("índice de Titulação", f"{kpi_indice_tit:.1f}%", 0.0, COLORS["Amarelo"])
        
        st.markdown("<br>", unsafe_allow_html=True)

        # --- Gráficos lado a lado (Stricto Sensu) ---
        col_s1, col_s2 = st.columns(2)
        col_s3, col_s4 = st.columns(2)

        with col_s1:
            chart_title("Evolução da Quantidade de Alunos por Unidade")
            df_unidade = pd.DataFrame({
                "Ano": [2023, 2024, 2025] * 6,
                "Unidade": ["Recife"]*3 + ["Garanhuns"]*3 + ["Petrolina"]*3 + ["Recife"]*3 + ["Garanhuns"]*3 + ["Petrolina"]*3,
                "Nível": ["Mestrado"]*9 + ["Doutorado"]*9,
                "Quantidade": [150, 160, 170, 50, 55, 60, 40, 42, 45, 70, 80, 88, 10, 12, 15, 8, 10, 12]
            })
            fig = px.line(
                df_unidade,
                x='Ano',
                y='Quantidade',
                color='Unidade',
                line_dash='Nível',
                markers=True,
                template='plotly_dark',
                # sequência de cores coordenada para unidades
                color_discrete_sequence=[STRICTO['Unidade_1'], STRICTO['Unidade_2'], STRICTO['Unidade_3'], STRICTO['Homens'], STRICTO['Mulheres']]
            )
            # Forçar Recife em Coral e manter as demais unidades com uma sequência coerente
            fig.update_traces(selector=dict(name='Recife, Mestrado'), line=dict(color=COLORS['Coral']))
            fig.update_traces(selector=dict(name='Recife, Doutorado'), line=dict(color=COLORS['Coral'], dash='dash'))
            fig.update_traces(selector=dict(name='Garanhuns, Mestrado'), line=dict(color='#26DFD0'))
            fig.update_traces(selector=dict(name='Garanhuns, Doutorado'), line=dict(color='#26DFD0', dash='dash'))
            fig.update_traces(selector=dict(name='Petrolina, Mestrado'), line=dict(color='#FFD700'))
            fig.update_traces(selector=dict(name='Petrolina, Doutorado'), line=dict(color='#FFD700', dash='dash'))
            fig.update_layout(xaxis_title="Ano", yaxis_title="Quantidade de alunos")
            st.plotly_chart(fig, use_container_width=True)

        with col_s2:
            chart_title("Alunos por Curso")
            df_genero = pd.DataFrame({
                "Curso": ["Biotecnologia", "Eng. de Software", "Saúde Pública"] * 4,
                "Nível": ["Mestrado"]*6 + ["Doutorado"]*6,
                "Gênero": ["Homens", "Mulheres", "Homens", "Mulheres", "Homens", "Mulheres"] * 2,
                "Alunos": [25, 35, 40, 20, 30, 45, 12, 22, 18, 16, 15, 24]
            })
            curso_genero = st.selectbox("Selecione o Curso:", df_genero["Curso"].unique(), key="stricto_genero_curso")
            df_genero_filtrado = df_genero[df_genero["Curso"] == curso_genero]
            fig = px.bar(
                df_genero_filtrado,
                x="Nível",
                y="Alunos",
                color="Gênero",
                barmode="group",
                template='plotly_dark'
            )
            # Forçar cores por gênero
            fig.update_traces(marker_line_width=0)
            try:
                fig.for_each_trace(lambda t: t.update(marker_color=STRICTO.get(t.name, t.marker.color)))
            except Exception:
                pass
            fig.update_layout(xaxis_title="Nível", yaxis_title="Quantidade de alunos")
            st.plotly_chart(fig, use_container_width=True)

        with col_s3:
            chart_title("Evolução Quantidade De Alunos Por Programa")
            # Construir mock com dimensões: Ano, Curso, Nível, Gênero, Status, Quantidade
            cursos = ["Biotecnologia", "Eng. de Software", "Saúde Pública"]
            niveis = ["Mestrado", "Doutorado"]
            generos = ["Homens", "Mulheres"]
            statuses = ["Titulado", "Desistente"]
            anos = [2023, 2024, 2025]

            rows = []
            for curso in cursos:
                for nivel in niveis:
                    for genero in generos:
                        for status in statuses:
                            # base para criar números plausíveis
                            base = 40 if status == "Titulado" else 4
                            if nivel == "Doutorado":
                                base = int(base * 0.5)
                            if curso == "Eng. de Software":
                                base = int(base * 1.1)
                            if genero == "Mulheres":
                                base = int(base * 1.05)
                            for i, ano in enumerate(anos):
                                qtd = int(base + i * (5 if status == "Titulado" else 0) + (2 if nivel == "Mestrado" else 0))
                                rows.append({"Ano": ano, "Curso": curso, "Nível": nivel, "Gênero": genero, "Status": status, "Quantidade": qtd})

            df_status = pd.DataFrame(rows)
            curso_selecionado = st.selectbox("Selecione o Curso:", df_status["Curso"].unique(), key="stricto_curso")
            df_status_filtrado = df_status[df_status["Curso"] == curso_selecionado]

            # Renderizar sempre os subplots (Mestrado/Doutorado) sem selector — títulos curtos e cores definidas
            niveis_ord = ["Mestrado", "Doutorado"]
            status_ord = ["Titulado", "Desistente"]
            anos_ord = sorted(df_status_filtrado['Ano'].unique())

            # Títulos curtos para evitar sobreposição
            subplot_titles = []
            for nivel in niveis_ord:
                for status in status_ord:
                    subplot_titles.append(f"{nivel} - {status}")

            fig = make_subplots(rows=len(niveis_ord), cols=len(status_ord),
                                subplot_titles=subplot_titles,
                                shared_xaxes=True, shared_yaxes=False,
                                vertical_spacing=0.18, horizontal_spacing=0.14)

            # Escolha de cores combinantes a partir da paleta fornecida: Ciano e Coral para contraste
            color_homens = '#00FFFF'   # Ciano
            color_mulheres = COLORS['Coral'] # Coral (usar a cor definida no dicionário COLORS)

            for i, nivel in enumerate(niveis_ord):
                for j, status in enumerate(status_ord):
                    r = i + 1
                    c = j + 1
                    sub = df_status_filtrado[(df_status_filtrado['Nível'] == nivel) & (df_status_filtrado['Status'] == status)]
                    pivot = sub.groupby(['Ano', 'Gênero'])['Quantidade'].sum().reset_index().pivot(index='Ano', columns='Gênero', values='Quantidade').reindex(anos_ord).fillna(0)

                    homens_vals = pivot.get('Homens', pd.Series([0]*len(anos_ord), index=anos_ord)).tolist()
                    mulheres_vals = pivot.get('Mulheres', pd.Series([0]*len(anos_ord), index=anos_ord)).tolist()

                    # Mostrar legenda apenas na primeira célula para evitar duplicação — mostrar ambas as entradas
                    show_legend_for_first = (i == 0 and j == 0)
                    fig.add_trace(go.Bar(x=anos_ord, y=homens_vals, name='Homens', marker_color=color_homens, showlegend=show_legend_for_first), row=r, col=c)
                    fig.add_trace(go.Bar(x=anos_ord, y=mulheres_vals, name='Mulheres', marker_color=color_mulheres, showlegend=show_legend_for_first), row=r, col=c)

            fig.update_layout(template='plotly_dark', barmode='group', height=600, margin=dict(t=120, b=40))
            fig.update_annotations(font_size=11)
            fig.update_yaxes(title_text='Quantidade')
            fig.update_xaxes(title_text='Ano')
            fig.update_layout(legend=dict(title='Gênero', orientation='v', x=1.02, y=0.95))
            st.plotly_chart(fig, use_container_width=True)

        with col_s4:
            chart_title("Titulados/Desistentes (Gênero)")
            # Restaurar gráfico simples: barras empilhadas por Gênero com Titulado/Desistente
            df_gen_status = df_status[df_status["Curso"] == curso_selecionado].groupby(["Gênero", "Status"])['Quantidade'].sum().reset_index()
            df_pivot = df_gen_status.pivot(index='Gênero', columns='Status', values='Quantidade').fillna(0).reset_index()
            # Garantir colunas na ordem esperada
            if 'Titulado' in df_pivot.columns and 'Desistente' in df_pivot.columns:
                df_melt = df_pivot.melt(id_vars='Gênero', value_vars=['Titulado', 'Desistente'], var_name='variable', value_name='value')
            else:
                df_melt = df_gen_status.melt(id_vars='Gênero', value_vars=['Status', 'Quantidade'])
            # Mapear cores de Titulado/Desistente a partir da paleta STRICTO
            fig = px.bar(
                df_melt,
                x='Gênero',
                y='value',
                color='variable',
                barmode='stack',
                template='plotly_dark',
                color_discrete_map={'Titulado': STRICTO['Titulado'], 'Desistente': STRICTO['Desistente']}
            )
            fig.update_layout(yaxis_title='Quantidade')
            fig.update_traces(marker_line_width=0)
            st.plotly_chart(fig, use_container_width=True)

    else: # Lato Sensu
        # --- KPIs Lato Sensu ---
        kpi_cols = st.columns(4)
        with kpi_cols[0]: kpi_card_delta("Nº de Programas", _format_int(lato_programas), 0.0, COLORS["Coral"])
        with kpi_cols[1]: kpi_card_delta("Alunos Matriculados", _format_int(lato_matric), 0.0, COLORS["Amarelo"])
        with kpi_cols[2]: kpi_card_delta("Alunos Titulados", _format_int(lato_tit), 0.0, COLORS["Verde Limao"])
        with kpi_cols[3]: kpi_card_delta("Índice de Titulação", f"{lato_idx:.1f}%", 0.0, COLORS["Ciano"])
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # --- Gráficos Lado a Lado ---
        col1, col2 = st.columns(2)

        with col1:
            chart_title("Visão Geral dos Cursos")
            if not df_lato_real.empty:
                col_lato_curso = _find_col(df_lato_real, ["denominacao", "pasta_do_curso"])
                col_lato_modal = _find_col(df_lato_real, ["modalidade"])
                show_cols = [c for c in [col_lato_curso, col_lato_natureza, col_lato_unidade, col_lato_modal] if c]
                df_tabela = df_lato_real[show_cols].rename(
                    columns={
                        col_lato_curso: "Curso",
                        col_lato_natureza: "Natureza",
                        col_lato_unidade: "Unidade",
                        col_lato_modal: "Modalidade",
                    }
                )
            else:
                df_tabela = pd.DataFrame(
                    {
                        "Curso": ["Gestão de Projetos", "Análise de Dados", "Marketing Digital", "Direito Aplicado"],
                        "Natureza": ["Privado", "Público", "Privado", "Público"],
                        "Unidade": ["Recife", "Garanhuns", "Recife", "Petrolina"],
                        "Modalidade": ["EAD", "Presencial", "Híbrido", "Presencial"],
                    }
                )
            st.dataframe(df_tabela, use_container_width=True)

            chart_title("Nº de Cursos por Grande Área de Conhecimento")
            col_lato_area = _find_col(df_lato_real, ["grande_area_e_area_de_conhecimento", "grande_area"])
            if not df_lato_real.empty and col_lato_area:
                df_area = _counts_df(df_lato_real[col_lato_area].fillna("Não informado").astype(str), "Área", "Cursos")
            else:
                df_area = pd.DataFrame({"Área": ["Saúde", "Tecnologia", "Gestão", "Direito"], "Cursos": [10, 8, 12, 5]})
            fig_area = px.bar(df_area, x="Área", y="Cursos", color="Área", template='plotly_dark')
            fig_area.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor=COLORS['Card'])
            st.plotly_chart(fig_area, use_container_width=True)

        with col2:
            chart_title("Nº de Cursos por Unidade, Natureza e Modalidade")
            col_lato_modal = _find_col(df_lato_real, ["modalidade"])
            if not df_lato_real.empty and col_lato_unidade and col_lato_natureza and col_lato_modal:
                df_exemplo = (
                    df_lato_real.groupby([col_lato_unidade, col_lato_natureza, col_lato_modal], as_index=False)
                    .size()
                    .rename(
                        columns={
                            col_lato_unidade: "Unidade",
                            col_lato_natureza: "Natureza",
                            col_lato_modal: "Modalidade",
                            "size": "Nº de Cursos",
                        }
                    )
                )
            else:
                df_exemplo = pd.DataFrame(
                    {
                        "Unidade": ["Recife", "Recife", "Recife", "Recife", "Garanhuns", "Garanhuns", "Garanhuns", "Garanhuns", "Petrolina", "Petrolina", "Petrolina", "Petrolina"],
                        "Natureza": ["Público", "Privado", "Público", "Privado", "Público", "Privado", "Público", "Privado", "Público", "Privado", "Público", "Privado"],
                        "Modalidade": ["Presencial", "Presencial", "EAD", "EAD", "Presencial", "Presencial", "EAD", "EAD", "Presencial", "Presencial", "EAD", "EAD"],
                        "Nº de Cursos": [12, 10, 8, 6, 9, 7, 5, 4, 7, 6, 4, 3],
                    }
                )
            cores_natureza = {
                "Público": COLORS['Ciano'],
                "Privado": COLORS['Coral']
            }
            fig_h = px.bar(
                df_exemplo,
                x='Unidade',
                y='Nº de Cursos',
                color='Natureza',
                barmode='group',
                facet_col='Modalidade',
                category_orders={'Modalidade': ['Presencial', 'EAD'], 'Unidade': ['Recife', 'Garanhuns', 'Petrolina']},
                color_discrete_map=cores_natureza,
                template='plotly_dark'
            )
            fig_h.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor=COLORS['Card'],
                legend_title_text='Natureza',
                xaxis_title='Unidade',
                yaxis_title='Nº de Cursos'
            )
            fig_h.update_traces(textposition='outside', texttemplate='%{y}', opacity=1.0, marker_line_width=0)
            st.plotly_chart(fig_h, use_container_width=True)

# --- RODAPÉ ---
st.markdown("---")
st.markdown(f"<div style='text-align: center; color: grey;'>Observatório de Inteligência UPE - v1.0.0 (Filtro Atual: {ano_selected})</div>", unsafe_allow_html=True)