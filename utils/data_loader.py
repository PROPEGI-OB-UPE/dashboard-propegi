import pandas as pd
import streamlit as st
import os

# Define a raiz baseada onde está o utils/data_loader.py (uma pasta acima)
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

def carregar_csv(*caminho_partes):
    caminho_completo = os.path.join(BASE_DIR, *caminho_partes)
    if os.path.exists(caminho_completo):
        return pd.read_csv(caminho_completo)
    return pd.DataFrame()

@st.cache_data
def carregar_dados_docentes():
    return carregar_csv("data", "processed", "pesquisa", "DOCENTES-ATIVOS", "docentes_ativos.csv")

@st.cache_data
def carregar_dados_grupos_pesquisa():
    return carregar_csv("data", "processed", "pesquisa", "GRUPO-PESQUISA", "grupos_pesquisa.csv")

@st.cache_data
def carregar_dados_apq():
    return carregar_csv("data", "processed", "pesquisa", "PLANILHAS-APQ", "prestacao_contas_apq.csv")

@st.cache_data
def carregar_dados_icti():
    return carregar_csv("data", "processed", "pesquisa", "PLANILHAS-ICTI", "monitoramento_icti.csv")

@st.cache_data
def carregar_dados_bolsistas():
    pasta = os.path.join(BASE_DIR, "data", "processed", "pesquisa", "BOLSAS-PQ-DT")
    if not os.path.exists(pasta):
        return pd.DataFrame()
    arquivos = [os.path.join(pasta, f) for f in os.listdir(pasta) if f.endswith('.csv')]
    dfs = [pd.read_csv(arq) for arq in arquivos]
    return pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()