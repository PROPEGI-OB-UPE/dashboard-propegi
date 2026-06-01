import pandas as pd

def clean_data(df):
    """Aplica o tratamento sem perda de dados (Lossless Cleaning) centralizado."""
    
    # 1. Remove colunas que estejam 100% vazias
    df = df.dropna(axis=1, how='all')
    
    # 2. Padronização de todas as colunas de texto (Caixa alta e sem espaços extras)
    cols_texto = df.select_dtypes(include=['object']).columns
    for col in cols_texto:
        df[col] = df[col].astype(str).str.strip().str.upper()
        # Substitui textos que eram vazios ou apenas espaços por 'NÃO INFORMADO'
        df[col] = df[col].replace({'': 'NÃO INFORMADO', 'NAN': 'NÃO INFORMADO', 'NONE': 'NÃO INFORMADO'})
    
    # 3. Tratamento de colunas numéricas (Preencher vazios com 0)
    cols_numericas = df.select_dtypes(include=['float64', 'int64']).columns
    for col in cols_numericas:
        df[col] = df[col].fillna(0)
        
    return df