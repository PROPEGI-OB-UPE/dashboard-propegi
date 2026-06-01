import gspread
import pandas as pd
import streamlit as st
import os
import sys

# Sobe dois níveis (../../) para encontrar a pasta etl e o utils.py
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from utils import clean_data

credentials = dict(st.secrets["gcp_service_account"])
gc = gspread.service_account_from_dict(credentials)

# URL da planilha do Google Sheets
url_planilha = "Chttps://docs.google.com/spreadsheets/d/1cPINCzGi2bZk9D4K3BQl28X-lIYSh_PahEXbPtY_sdc/edit?gid=731792511#gid=731792511"
planilha = gc.open_by_url(url_planilha)
aba = planilha.sheet1 

valores = aba.get_all_values()
df_bruto = pd.DataFrame(valores)

# Assumindo que o cabeçalho principal está na primeira linha (índice 0). 
# Se estiver na segunda linha, mude para iloc[1] e o df_bruto.iloc[2:]
cabecalhos = df_bruto.iloc[0].tolist()

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

# Remove a linha de cabeçalho
df_bruto = df_bruto.iloc[1:].reset_index(drop=True)

# Remove as colunas vazias
colunas_validas = [col for col in df_bruto.columns if not col.startswith("COLUNA_VAZIA_")]
df_bruto = df_bruto[colunas_validas]

df_tratado = clean_data(df_bruto)

os.makedirs("data/processed/pesquisa/planilhas_apq", exist_ok=True)
caminho_csv = "data/processed/pesquisa/planilhas_apq/prestacao_contas_apq.csv"
df_tratado.to_csv(caminho_csv, index=False)

print(f"Sucesso! {len(df_tratado)} registros salvos em {caminho_csv}")