import gspread
import pandas as pd
import streamlit as st
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from utils import clean_data

credentials = dict(st.secrets["gcp_service_account"])
gc = gspread.service_account_from_dict(credentials)

url_planilha = "https://docs.google.com/spreadsheets/d/1K2lhN2nfxej5N_5I8Sir2XAEx4Wc3uAxcfEbdijkkCk/edit?gid=469921862#gid=469921862"
planilha = gc.open_by_url(url_planilha)
abas = planilha.worksheets()

dfs_processados = []

for aba in abas:
    valores = aba.get_all_values()
    if len(valores) < 3:
        continue
        
    df_bruto = pd.DataFrame(valores)
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
    
    dfs_processados.append(df_bruto)

if dfs_processados:
    df_consolidado = pd.concat(dfs_processados, ignore_index=True)
    df_tratado = clean_data(df_consolidado)
    
    os.makedirs("data/processed/pesquisa/bolsistas_pq_dt", exist_ok=True)
    caminho_csv = "data/processed/pesquisa/bolsistas_pq_dt/bolsistas_2025.csv"
    df_tratado.to_csv(caminho_csv, index=False)
    print(f"Sucesso! {len(df_tratado)} registros de 2025 salvos em {caminho_csv}")
else:
    print("Nenhum dado encontrado nas abas da planilha de 2025.")