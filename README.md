# Analytics ERP

Este projeto é uma ferramenta de análise de dados para sistemas ERP (Enterprise Resource Planning). Ele automatiza a descoberta de relacionamentos entre tabelas de dados, analisa esquemas de CSVs e fornece visualizações interativas para entender a estrutura do banco de dados.

## Estrutura do Projeto

```
analytics_erp/
├── data/
│   ├── raw/                    # CSVs originais (368 arquivos)
│   ├── processed/              # Dados processados
│   ├── metadata/               # Metadados e schema
│   └── relationships/          # Relacionamentos descobertos
├── src/
│   ├── relationship_miner.py   # Mineração automática de relacionamentos
│   ├── schema_analyzer.py      # Análise de schema dos CSVs
│   ├── data_loader.py          # Carregamento otimizado
│   ├── data_loader_helper.py   # Helpers para carregamento
│   └── dashboard.py            # Visualização de relacionamentos
├── tests/                      # Testes unitários
├── app.py                      # Aplicação principal
├── pyproject.toml              # Configuração do projeto
├── requirements.txt            # Dependências
└── README.md                   # Este arquivo
```

## Funcionalidades

- **Análise de Schema**: Analisa automaticamente os esquemas dos arquivos CSV.
- **Mineração de Relacionamentos**: Descobre relacionamentos entre tabelas baseados em chaves estrangeiras e padrões de dados.
- **Carregamento Otimizado**: Carrega dados de forma eficiente, suportando grandes volumes.
- **Dashboard Interativo**: Visualiza os relacionamentos descobertos em uma interface web.

## Instalação

1. Clone o repositório:
   ```
   git clone <url-do-repositorio>
   cd analytics_erp
   ```

2. Instale as dependências:
   ```
   pip install -r requirements.txt
   ```

3. Execute a aplicação:
   ```
   python app.py
   ```

## Uso

- Coloque os arquivos CSV na pasta `data/raw/`.
- Execute `python src/schema_analyzer.py` para analisar os esquemas.
- Execute `python src/relationship_miner.py` para minerar relacionamentos.
- Execute `python src/dashboard.py` para visualizar os resultados.

## Contribuição

Contribuições são bem-vindas! Por favor, abra uma issue ou envie um pull request.

## Licença

Este projeto está sob a licença MIT.