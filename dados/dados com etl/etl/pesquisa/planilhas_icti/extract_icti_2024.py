import gspread
import pandas as pd
import streamlit as st
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from utils import clean_data

credentials = dict(st.secrets["gcp_service_account"])
gc = gspread.service_account_from_dict(credentials)

url_planilha = "https://docs.google.com/spreadsheets/d/1JNvUTYviqhdU1gOEVR8Y7hrITTkGJtbGM1OlPnyN5lU/edit?gid=1281280921#gid=1281280921"
planilha = gc.open_by_url(url_planilha)
aba = planilha.sheet1 

df_bruto = pd.DataFrame(aba.get_all_values())
cabecalhos = df_bruto.iloc[0].tolist()

cabecalhos_tratados = []
contagem_nomes = {}
for i, col in enumerate(cabecalhos):
    col_nome = str(col).strip()
    if col_nome == "": cabecalhos_tratados.append(f"COLUNA_VAZIA_{i}")
    else:
        contagem_nomes[col_nome] = contagem_nomes.get(col_nome, -1) + 1
        cabecalhos_tratados.append(f"{col_nome}_{contagem_nomes[col_nome]}" if contagem_nomes[col_nome] > 0 else col_nome)

df_bruto.columns = cabecalhos_tratados
df_bruto = df_bruto.iloc[1:].reset_index(drop=True)
df_bruto = df_bruto[[col for col in df_bruto.columns if not col.startswith("COLUNA_VAZIA_")]]

df_tratado = clean_data(df_bruto)
os.makedirs("data/processed/pesquisa/planilhas_icti", exist_ok=True)
df_tratado.to_csv("data/processed/pesquisa/planilhas_icti/icti_2024.csv", index=False)
print(f"Sucesso! {len(df_tratado)} registros salvos em icti_2024.csv")