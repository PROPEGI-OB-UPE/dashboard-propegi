import gspread
import pandas as pd
import streamlit as st
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from utils import clean_data

credentials = dict(st.secrets["gcp_service_account"])
gc = gspread.service_account_from_dict(credentials)

# Link extraído da imagem
url_planilha = "https://docs.google.com/spreadsheets/d/1s6EnBntBXJaoiowdPElsscWPq7JLUHZOJ-topXZ78s4/edit?gid=206859761#gid=206859761"
planilha = gc.open_by_url(url_planilha)
aba = planilha.sheet1 

valores = aba.get_all_values()
df_bruto = pd.DataFrame(valores)

# Para a planilha de 2024, o cabeçalho está na Linha 2 (índice 1) devido à linha mesclada
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

df_tratado = clean_data(df_bruto)

os.makedirs("data/processed/pesquisa/bolsistas_pq_dt", exist_ok=True)
caminho_csv = "data/processed/pesquisa/bolsistas_pq_dt/bolsistas_2024.csv"
df_tratado.to_csv(caminho_csv, index=False)

print(f"Sucesso! {len(df_tratado)} registros de 2024 salvos em {caminho_csv}")