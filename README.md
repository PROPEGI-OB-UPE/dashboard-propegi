# Observatório de Inteligência PROPEGI - UPE

Painel de Gestão Estratégica desenvolvido para a **Pró-Reitoria de Pesquisa, Pós-Graduação e Inovação (PROPEGI)** da Universidade de Pernambuco (UPE). Este dashboard interativo visa centralizar, visualizar e monitorar os principais indicadores de desempenho (KPIs) acadêmicos e financeiros da instituição.

---

## Objetivo

Fornecer à alta gestão e aos coordenadores da PROPEGI uma ferramenta de Business Intelligence para tomada de decisão baseada em dados, permitindo o acompanhamento em tempo real da evolução de bolsas, captação de recursos, produção intelectual e situação dos programas de pós-graduação.

## Funcionalidades por Módulo

O dashboard é dividido em cinco painéis principais, acessíveis pelo menu de navegação lateral:

*   **Visão Geral:** KPIs globais da Pró-Reitoria, painéis de acompanhamento de metas institucionais e resumo executivo de fomento captado e entregas científicas.
*   **Pesquisa:** 
    *   Acompanhamento de Bolsas (PIBIC, PIBITI, PIBIC-EM).
    *   Evolução e ranking de Grupos de Pesquisa por Área de Conhecimento e Unidade.
    *   Perfil de pesquisadores e alunos (cotistas vs. não cotistas, gênero).
    *   Monitoramento de Bolsistas de Produtividade (CNPq e FACEPE) e recursos de Editais APQ.
*   **Inovação:**
    *   Indicadores de Propriedade Intelectual (Evolução de Patentes e Softwares).
    *   Captação de recursos e formalização de convênios.
    *   Nível de Maturidade Tecnológica (TRL) dos projetos.
    *   Distribuição de projetos por Segmento, Natureza, Região e Setor (Público/Privado).
*   **Desenvolvimento Tecnológico:**
    *   Métricas de faturamento e status de projetos.
    *   Análise geográfica de atuação institucional.
*   **Pós-Graduação:**
    *   Desempenho dos programas Stricto Sensu (Mestrado e Doutorado) e Lato Sensu (Especializações).
    *   Índices de matrícula, titulação e evasão.
    *   Evolução demográfica de discentes por curso e unidade.

## Tecnologias Utilizadas

*   **[Python 3.9+](https://www.python.org/):** Linguagem principal de processamento.
*   **[Streamlit](https://streamlit.io/):** Framework para construção da interface web e componentes interativos.
*   **[Pandas](https://pandas.pydata.org/):** Biblioteca para manipulação, limpeza e agregação de dados (ETL).
*   **[Plotly (Express & Graph Objects)](https://plotly.com/python/):** Biblioteca para a geração de gráficos dinâmicos e interativos.

## Estrutura do Projeto

```text
dashboard-propegi/
├── data/
│   └── processed/                 # Bases de dados tratadas (CSV) divididas por área
│       ├── desenvolvimento-tecnologico/
│       ├── inovacao/
│       ├── pesquisa/
│       └── pos-graduacao/
├── utils/
│   └── data_loader.py             # Scripts utilitários para ingestão e limpeza dos dados
├── .streamlit/
│   └── config.toml                # Configurações de tema global (Dark Mode)
├── projeto.py                     # Arquivo principal do Dashboard (Frontend e Lógica)
└── requirements.txt               # Lista de dependências do Python
