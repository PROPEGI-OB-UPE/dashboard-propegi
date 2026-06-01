import gspread
import pandas as pd
import streamlit as st
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils import clean_data

# --- EXTRAÇÃO ---
credentials = dict(st.secrets["gcp_service_account"])
gc = gspread.service_account_from_dict(credentials)

url_planilha = "https://docs.google.com/spreadsheets/d/1KiNJ6ddvxdBe3-NdhXBl2bIsTGYzotxnB1AfaZSLKnM/edit?gid=993336669#gid=993336669t"
planilha = gc.open_by_url(url_planilha)
aba = planilha.sheet1 

df_bruto = pd.DataFrame(aba.get_all_records())

# --- TRANSFORMAÇÃO ---
df_tratado = clean_data(df_bruto)

# --- CARREGAMENTO ---
os.makedirs("data/processed/inovacao", exist_ok=True)
caminho_csv = "data/processed/inovacao/propriedade_intelectual.csv"
df_tratado.to_csv(caminho_csv, index=False)

