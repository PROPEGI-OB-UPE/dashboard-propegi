import os
import pandas as pd
import warnings

# Ignorar alertas do pandas para manter o terminal limpo
warnings.filterwarnings('ignore')

def executar_etl_dt():
    # Caminhos baseados na raiz onde o script será executado
    DIRETORIO_ATUAL = os.path.dirname(os.path.abspath(__file__))
    ARQUIVO_ORIGEM = "Dashboard Projetos - Agência de Inovação UPE.xlsx"
    
    # Destino exato solicitado para o dashboard consumir
    PASTA_DESTINO = os.path.join(DIRETORIO_ATUAL, "data", "processed", "desenvolvimento-tecnologico")
    os.makedirs(PASTA_DESTINO, exist_ok=True)
    
    caminho_arquivo = os.path.join(DIRETORIO_ATUAL, ARQUIVO_ORIGEM)
    
    if not os.path.exists(caminho_arquivo):
        print(f"❌ Arquivo não encontrado: {caminho_arquivo}")
        return

    print("Iniciando extração e tratamento dos dados de Desenvolvimento Tecnológico...")
    
    try:
        xls = pd.ExcelFile(caminho_arquivo)
        dfs_validos = []
        
        for aba in xls.sheet_names:
            df = pd.read_excel(xls, sheet_name=aba)
            
            # 1. Tratamento base: Remove linhas e colunas 100% vazias
            df = df.dropna(axis=0, how='all').dropna(axis=1, how='all')
            
            # 2. Ignora abas totalmente vazias ou a aba de 'Dashboard' 
            # (A aba Dashboard contém matrizes visuais soltas que corromperiam o formato tabular do CSV)
            if df.empty or aba.lower() == 'dashboard':
                continue
                
            # 3. Tratamento de cabeçalhos: remove espaços extras e quebras de linha
            df.columns = [str(col).strip().replace('\n', ' ') for col in df.columns]
            
            # 4. Limpeza de texto dentro da tabela: remove quebras de linha e espaços excedentes
            df = df.map(lambda x: str(x).strip().replace('\n', ' ') if isinstance(x, str) else x)
            
            # 5. Adiciona marcador indicando de qual aba a linha veio
            df['ABA_ORIGEM'] = aba
            dfs_validos.append(df)
            
        if dfs_validos:
            # Concatena todas as abas tratadas em uma única tabela
            df_final = pd.concat(dfs_validos, ignore_index=True)
            
            # 6. Padronização de tipagem de dados nas colunas numéricas essenciais
            colunas_numericas = ['Receita', 'Total de Bolsas', 'TRL', 'Ano']
            for col in colunas_numericas:
                if col in df_final.columns:
                    # Converte para numérico, transformando erros/textos em branco (NaN) e depois em 0
                    df_final[col] = pd.to_numeric(df_final[col], errors='coerce').fillna(0)
            
            # 7. Geração do arquivo CSV na pasta processada
            caminho_saida = os.path.join(PASTA_DESTINO, "desenvolvimento_tecnologico_processado.csv")
            df_final.to_csv(caminho_saida, index=False, encoding='utf-8-sig')
            
            print(f"✅ ETL Concluído! Arquivo gerado com sucesso.")
            print(f"📍 Caminho: {caminho_saida}")
            print(f"📊 Total de registros processados: {len(df_final)}")
        else:
            print("⚠️ Nenhuma aba com dados estruturados foi encontrada para extração.")
            
    except Exception as e:
        print(f"❌ Erro na execução do ETL: {e}")

if __name__ == "__main__":
    executar_etl_dt()