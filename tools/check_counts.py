from pathlib import Path
import pandas as pd

wb_path = Path(__file__).parent.parent.joinpath('Dashboard Projetos - Agência de Inovação UPE.xlsx')
df = pd.read_excel(wb_path, sheet_name='Dados dos Projetos')
df.columns = [str(c).strip() if c is not None else f'Col_{i}' for i, c in enumerate(df.columns)]

print('total rows:', len(df))
print('unique instituições (all):', int(df['Instituição'].nunique(dropna=True)))

if 'Vigente' in df.columns:
    print("unique instituições where Vigente == 'Vigente':", int(df[df['Vigente']=='Vigente']['Instituição'].nunique(dropna=True)))

if 'Receita' in df.columns:
    df['Receita'] = pd.to_numeric(df['Receita'], errors='coerce').fillna(0)
    print('unique instituciones with Receita>0:', int(df[df['Receita']>0]['Instituição'].nunique(dropna=True)))

if 'Ano' in df.columns:
    df['Ano'] = pd.to_numeric(df['Ano'], errors='coerce')
    for ymin in [2017,2018,2019,2020,2021,2022,2023]:
        subset = df[df['Ano']>=ymin]
        print(f"unique instituições com Ano>={ymin}:", int(subset['Instituição'].nunique(dropna=True)))

# check duplicates with different spellings
insts = df['Instituição'].dropna().astype(str).str.strip()
insts_upper = insts.str.upper()
print('unique normalized upper:', int(insts_upper.nunique()))

print('sample duplicates (different case/whitespace)')
from collections import defaultdict
m = defaultdict(list)
for orig in df['Instituição'].dropna().astype(str):
    m[orig.strip().upper()].append(orig)
count_diff = sum(1 for k,v in m.items() if len(set(v))>1)
print('normalized groups with >1 variants:', count_diff)
