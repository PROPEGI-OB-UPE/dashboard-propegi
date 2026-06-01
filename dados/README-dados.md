Instruções rápidas para inserir dados das coordenações

Onde colocar os arquivos:
- Coloque arquivos originais (Excel/CSV) em `dados/dados com etl/data/raw/`.
- Dados processados do ETL ficam em `dados/dados com etl/data/processed/`.
- Arquivos antigos ou cópias vão para `dados/dados com etl/data/archive/`.

Formato e convenções:
- Preferir CSVs quando possível (UTF-8, separador `,`).
- Nomeie arquivos com formato: `coordenacao_nome_tipo_YYYY.ext` (ex.: `pos_censo_2025.csv`).
- Datas: usar ISO `YYYY-MM-DD` ou colunas separadas `ano`, `mes`, `dia`.
- Colunas: manter cabeçalho na primeira linha; evitar células mescladas em Excel.

Passos para inserir dados:
1. Salve o arquivo original em `data/raw/`.
2. Execute o ETL correspondente (scripts em `dados/dados com etl/etl/`) ou solicite ao time de ETL.
3. Ao concluir, coloque a versão processada em `data/processed/`.

Contatos e notas:
- Se houver dúvidas sobre colunas esperadas, envie um print do cabeçalho para a equipe de dados.
- Não inclua arquivos com segredos em `data/` (ex.: arquivos `secrets.toml`).

Observação: esta organização foi criada pelo mantenedor do dashboard para facilitar o trabalho das coordenações.
