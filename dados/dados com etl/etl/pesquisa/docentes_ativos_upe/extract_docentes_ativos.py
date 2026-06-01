import gspread
import pandas as pd
import streamlit as st
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from utils import clean_data

credentials = dict(st.secrets["gcp_service_account"])
gc = gspread.service_account_from_dict(credentials)

# 
url_planilha = "https://docs.google.com/spreadsheets/d/1_iCV3gQVwqncsfSEIuqFSUPSycHqLESUZ-iZXfepgIw/edit?gid=2113548866#gid=2113548866"
planilha = gc.open_by_url(url_planilha)
aba = planilha.sheet1 

valores = aba.get_all_values()
df_bruto = pd.DataFrame(valores)

# O cabeçalho real está na Linha 2 (índice 1)
cabecalhos = df_bruto.iloc[1].tolist()

cabecalhos_tratados = []
contagem_nomes = {}

for i, col in enumerate(cabecalhos):
    col_nome = str(col).strip()
    if col_nome == "":
        cabecalhos_tratados.append(f"COLUNA_VAZIA_{i}")
    else:
        if col_nome not in contagem_nomes:
            contagem_nomes[col_nome] = 0
            cabecalhos_tratados.append(col_nome)
        else:
            contagem_nomes[col_nome] += 1
            cabecalhos_tratados.append(f"{col_nome}_{contagem_nomes[col_nome]}")

df_bruto.columns = cabecalhos_tratados
df_bruto = df_bruto.iloc[2:].reset_index(drop=True)

colunas_validas = [col for col in df_bruto.columns if not col.startswith("COLUNA_VAZIA_")]
df_bruto = df_bruto[colunas_validas]

# Resolve o problema das células mescladas na primeira coluna (FUNÇÃO GERAL)
if len(df_bruto.columns) > 0:
    df_bruto.iloc[:, 0] = df_bruto.iloc[:, 0].replace('', None).ffill()

df_tratado = clean_data(df_bruto)

os.makedirs("data/processed/pesquisa/docentes_ativos_upe", exist_ok=True)
caminho_csv = "data/processed/pesquisa/docentes_ativos_upe/docentes_ativos.csv"
df_tratado.to_csv(caminho_csv, index=False)

print(f"Sucesso! {len(df_tratado)} registros salvos em {caminho_csv}")