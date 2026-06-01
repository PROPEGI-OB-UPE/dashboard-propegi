import gspread
import pandas as pd
import streamlit as st
import os
import sys

# Garante que o Python encontre o utils.py na mesma pasta
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils import clean_data

# --- EXTRAÇÃO ---
credentials = dict(st.secrets["gcp_service_account"])
gc = gspread.service_account_from_dict(credentials)

url_planilha = "https://docs.google.com/spreadsheets/d/1qTtas7yVoERgFKKDpOZtm69KWqOQo7p6XLF4PEhz1lw/edit?gid=260687429#gid=260687429"
planilha = gc.open_by_url(url_planilha)
aba = planilha.sheet1 

df_bruto = pd.DataFrame(aba.get_all_records())

# --- TRANSFORMAÇÃO (Usando a função centralizada) ---
df_tratado = clean_data(df_bruto)

# --- CARREGAMENTO ---
os.makedirs("data/processed/inovacao", exist_ok=True)
caminho_csv = "data/processed/inovacao/dashboard_inovacao.csv"
df_tratado.to_csv(caminho_csv, index=False)