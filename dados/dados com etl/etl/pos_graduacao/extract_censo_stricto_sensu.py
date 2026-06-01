import gspread
import pandas as pd
import streamlit as st
import os
import sys

# Sobe um nível para importar o utils.py
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils import clean_data

# --- EXTRAÇÃO ---
credentials = dict(st.secrets["gcp_service_account"])
gc = gspread.service_account_from_dict(credentials)

url_planilha = "https://docs.google.com/spreadsheets/d/1dNUdspFeRn001aVGb2kg8ws0KK-Tq0S9ftx-5VvKn20/edit?gid=436283352#gid=436283352"
planilha = gc.open_by_url(url_planilha)
aba = planilha.sheet1 

# Puxa todos os valores brutos (matriz) em vez de dicionários
valores = aba.get_all_values()
df_bruto = pd.DataFrame(valores)

# Define a Linha 2 (índice 1) como o cabeçalho real
cabecalhos = df_bruto.iloc[1].tolist()

# Trata as colunas em branco (geradas por células mescladas)
cabecalhos_tratados = []
for i, col in enumerate(cabecalhos):
    col_nome = str(col).strip()
    if col_nome == "":
        cabecalhos_tratados.append(f"COLUNA_VAZIA_{i}")
    else:
        cabecalhos_tratados.append(col_nome)

df_bruto.columns = cabecalhos_tratados

# Remove as linhas de cabeçalho da visualização de dados (Linhas 0 e 1)
df_bruto = df_bruto.iloc[2:].reset_index(drop=True)

# Remove as colunas vazias inúteis
colunas_validas = [col for col in df_bruto.columns if not col.startswith("COLUNA_VAZIA_")]
df_bruto = df_bruto[colunas_validas]

# --- TRANSFORMAÇÃO ---
df_tratado = clean_data(df_bruto)

# --- CARREGAMENTO ---
os.makedirs("data/processed/pos_graduacao", exist_ok=True)
caminho_csv = "data/processed/pos_graduacao/censo_stricto_sensu.csv"
df_tratado.to_csv(caminho_csv, index=False)

print(f"Sucesso! {len(df_tratado)} registros extraídos e salvos em {caminho_csv}")

