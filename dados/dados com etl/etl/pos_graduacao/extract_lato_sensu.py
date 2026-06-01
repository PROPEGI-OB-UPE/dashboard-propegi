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

url_planilha = "https://docs.google.com/spreadsheets/d/1_2UPjlAP4Q1FTMv2x_5KKPi8XKT6xWYP6w-yG9fVRYo/edit?gid=2121579566#gid=2121579566"
planilha = gc.open_by_url(url_planilha)
aba = planilha.sheet1 

valores = aba.get_all_values()
df_bruto = pd.DataFrame(valores)

# Define a Linha 3 (índice 2) como o cabeçalho real
cabecalhos = df_bruto.iloc[2].tolist()

# Trata as colunas em branco e garante nomes ÚNICOS
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

# Remove as linhas de título/cabeçalho (Linhas 0, 1 e 2)
df_bruto = df_bruto.iloc[3:].reset_index(drop=True)

# Remove as colunas vazias
colunas_validas = [col for col in df_bruto.columns if not col.startswith("COLUNA_VAZIA_")]
df_bruto = df_bruto[colunas_validas]

# --- TRANSFORMAÇÃO ---
df_tratado = clean_data(df_bruto)

# --- CARREGAMENTO ---
os.makedirs("data/processed/pos_graduacao", exist_ok=True)
caminho_csv = "data/processed/pos_graduacao/lato_sensu.csv"
df_tratado.to_csv(caminho_csv, index=False)

print(f"Sucesso! {len(df_tratado)} cursos lato sensu tratados e salvos em {caminho_csv}")



