# app.py - VERSÃO CORRIGIDA
import streamlit as st
import pandas as pd
from pathlib import Path
import sys

# Configuração
st.set_page_config(
    page_title="ERP Analytics",
    page_icon="📊",
    layout="wide"
)

# Título
st.title("📊 ERP Analytics Explorer")
st.markdown("""
Ferramenta para análise de dados de ERP exportados em CSV.
""")

def main():
    # Sidebar
    with st.sidebar:
        st.header("Configuração")
        
        data_path = st.text_input(
            "Caminho dos CSVs:",
            value="data/raw"
        )
        
        max_tables = st.slider(
            "Máximo de tabelas para analisar:",
            min_value=10,
            max_value=100,
            value=30
        )
        
        st.divider()
        
        if st.button("🔄 Limpar Cache", type="secondary"):
            if 'analyzer' in st.session_state:
                del st.session_state.analyzer
            if 'tables_info' in st.session_state:
                del st.session_state.tables_info
            if 'miner' in st.session_state:
                del st.session_state.miner
            st.success("Cache limpo!")
    
    # Inicializa sessão
    if 'analyzer' not in st.session_state:
        st.session_state.analyzer = None
    if 'tables_info' not in st.session_state:
        st.session_state.tables_info = None
    
    # Botão para análise
    if st.button("🔍 Analisar Estrutura do ERP", type="primary"):
        with st.spinner("Analisando tabelas CSV..."):
            try:
                # Importa dinamicamente para evitar problemas
                sys.path.insert(0, str(Path(__file__).parent / "src"))
                from schema_analyzer import ERPSchemaAnalyzer
                
                analyzer = ERPSchemaAnalyzer(data_path)
                tables_info = analyzer.analyze_all_tables(max_tables=max_tables)
                
                st.session_state.analyzer = analyzer
                st.session_state.tables_info = tables_info
                
                st.success(f"✅ Análise concluída! {len(tables_info)} tabelas analisadas.")
                
            except Exception as e:
                st.error(f"Erro na análise: {str(e)}")
                st.info("Verifique se existem arquivos CSV na pasta especificada.")
    
    # Se já tem dados analisados
    if st.session_state.analyzer and st.session_state.tables_info:
        analyzer = st.session_state.analyzer
        tables_info = st.session_state.tables_info
        
        # Abas principais
        tab1, tab2, tab3 = st.tabs([
            "📋 Visão Geral", 
            "🔗 Relacionamentos", 
            "🔍 Explorar Tabelas"
        ])
        
        with tab1:
            show_overview(tables_info)
        
        with tab2:
            show_relationships(tables_info)
        
        with tab3:
            explore_tables(tables_info)
    else:
        st.info("👈 Configure o caminho dos CSVs e clique em 'Analisar Estrutura do ERP' para começar.")

def show_overview(tables_info: dict):
    """Mostra visão geral das tabelas"""
    
    st.header("📈 Estatísticas Gerais")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Tabelas", len(tables_info))
    
    with col2:
        total_rows = sum(info.get('total_rows', 0) 
                        for info in tables_info.values() 
                        if isinstance(info.get('total_rows'), int))
        st.metric("Registros", f"{total_rows:,}")
    
    with col3:
        total_cols = sum(len(info.get('columns', [])) 
                        for info in tables_info.values())
        avg_cols = total_cols / len(tables_info) if tables_info else 0
        st.metric("Colunas (média)", f"{avg_cols:.1f}")
    
    with col4:
        # Conta tabelas com erro
        error_count = sum(1 for info in tables_info.values() 
                         if 'error' in info)
        st.metric("Tabelas com erro", error_count)
    
    # Tabelas maiores
    st.subheader("📊 Top 10 Tabelas por Volume")
    
    size_data = []
    for name, info in tables_info.items():
        if 'total_rows' in info and isinstance(info['total_rows'], int):
            size_data.append({
                'Tabela': name,
                'Registros': info['total_rows'],
                'Colunas': len(info.get('columns', [])),
                'Status': 'OK' if 'error' not in info else 'Erro'
            })
    
    if size_data:
        df_size = pd.DataFrame(size_data)
        df_size = df_size.sort_values('Registros', ascending=False).head(10)
        
        # Mostra como tabela
        st.dataframe(df_size, use_container_width=True)
        
        # Gráfico de barras
        try:
            import plotly.express as px
            fig = px.bar(df_size, x='Tabela', y='Registros',
                        title="Top 10 Tabelas por Volume de Dados",
                        color='Status')
            st.plotly_chart(fig, use_container_width=True)
        except:
            st.info("Instale plotly para ver gráficos: `pip install plotly`")
    
    # Distribuição por prefixo
    st.subheader("📁 Distribuição por Tipo")
    
    # Agrupa por prefixos comuns
    categories = {
        'Clientes': ['cliente', 'clientes'],
        'Produtos': ['produto', 'produtos', 'item'],
        'Vendas': ['venda', 'pedido', 'orcamento'],
        'Financeiro': ['financeiro', 'conta', 'pagamento', 'recebimento'],
        'Estoque': ['estoque', 'inventario', 'almox'],
        'Compras': ['compra', 'fornecedor'],
        'Relatórios': ['rpt', 'relatorio', 'report']
    }
    
    category_counts = {cat: 0 for cat in categories.keys()}
    category_counts['Outros'] = 0
    
    for table_name in tables_info.keys():
        table_lower = table_name.lower()
        categorized = False
        
        for category, keywords in categories.items():
            if any(keyword in table_lower for keyword in keywords):
                category_counts[category] += 1
                categorized = True
                break
        
        if not categorized:
            category_counts['Outros'] += 1
    
    # Mostra distribuição
    cat_df = pd.DataFrame({
        'Categoria': list(category_counts.keys()),
        'Quantidade': list(category_counts.values())
    }).sort_values('Quantidade', ascending=False)
    
    st.dataframe(cat_df, use_container_width=True)

def show_relationships(tables_info: dict):
    """Mostra relacionamentos entre tabelas"""
    
    st.header("🔗 Análise de Relacionamentos")
    
    if st.button("🔄 Detectar Relacionamentos", type="primary"):
        with st.spinner("Analisando possíveis relacionamentos..."):
            try:
                sys.path.insert(0, str(Path(__file__).parent / "src"))
                from relationship_miner import RelationshipMiner
                
                miner = RelationshipMiner(tables_info)
                relationships = miner.mine_relationships()
                
                st.session_state.miner = miner
                st.session_state.relationships = relationships
                
                st.success(f"✅ {len(relationships)} relacionamentos detectados!")
                
            except Exception as e:
                st.error(f"Erro na detecção: {str(e)}")
    
    if 'relationships' in st.session_state:
        relationships = st.session_state.relationships
        
        # Filtros
        col1, col2 = st.columns(2)
        
        with col1:
            min_confidence = st.slider("Confiança mínima:", 0.0, 1.0, 0.3, 0.1)
        
        with col2:
            show_type = st.selectbox(
                "Tipo de relacionamento:",
                ["Todos", "foreign_key_by_name", "erp_pattern"]
            )
        
        # Filtra relacionamentos
        filtered_rels = [
            r for r in relationships 
            if r.get('confidence', 0) >= min_confidence
        ]
        
        if show_type != "Todos":
            filtered_rels = [r for r in filtered_rels 
                           if r.get('relationship_type') == show_type]
        
        st.metric("Relacionamentos filtrados", len(filtered_rels))
        
        # Tabela de relacionamentos
        if filtered_rels:
            rels_df = pd.DataFrame(filtered_rels)
            
            # Seleciona colunas para mostrar
            if not rels_df.empty:
                available_cols = rels_df.columns.tolist()
                display_cols = ['source_table', 'target_table', 'relationship_type', 
                              'confidence']
                display_cols = [c for c in display_cols if c in available_cols]
                
                st.dataframe(
                    rels_df[display_cols].sort_values('confidence', ascending=False),
                    use_container_width=True,
                    height=400
                )
        
        # Análise por tabela
        st.subheader("🔍 Relacionamentos por Tabela")
        
        all_tables = list(tables_info.keys())
        selected_table = st.selectbox("Selecione uma tabela:", all_tables)
        
        if selected_table and 'miner' in st.session_state:
            miner = st.session_state.miner
            
            # Obtém relacionamentos da tabela
            table_rels = []
            for rel in relationships:
                if rel.get('source_table') == selected_table or \
                   rel.get('target_table') == selected_table:
                    table_rels.append(rel)
            
            if table_rels:
                # Divide em referências e referenciados
                outgoing = [r for r in table_rels 
                          if r.get('source_table') == selected_table]
                incoming = [r for r in table_rels 
                          if r.get('target_table') == selected_table]
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**Referencia ({len(outgoing)})**")
                    for rel in outgoing[:10]:  # Limita a 10
                        st.caption(
                            f"→ **{rel.get('target_table')}** "
                            f"(via `{rel.get('relationship_column', '?')}`) "
                            f"[{rel.get('confidence', 0):.1%}]"
                        )
                
                with col2:
                    st.write(f"**É Referenciada ({len(incoming)})**")
                    for rel in incoming[:10]:  # Limita a 10
                        st.caption(
                            f"← **{rel.get('source_table')}** "
                            f"(via `{rel.get('relationship_column', '?')}`) "
                            f"[{rel.get('confidence', 0):.1%}]"
                        )
            else:
                st.info("Nenhum relacionamento detectado para esta tabela.")
    else:
        st.info("Clique em 'Detectar Relacionamentos' para começar a análise.")

def explore_tables(tables_info: dict):
    """Permite explorar tabelas individualmente"""
    
    st.header("🔍 Explorador de Tabelas")
    
    # Filtro e busca
    col1, col2 = st.columns(2)
    
    with col1:
        search_term = st.text_input("Buscar por nome:", "")
    
    with col2:
        min_rows = st.number_input("Mínimo de registros:", 0, 10000000, 0)
    
    # Filtra tabelas
    filtered_tables = []
    for name, info in tables_info.items():
        # Aplica filtro de busca
        if search_term and search_term.lower() not in name.lower():
            continue
        
        # Aplica filtro de tamanho
        row_count = info.get('total_rows', 0)
        if isinstance(row_count, int) and row_count < min_rows:
            continue
        
        filtered_tables.append({
            'nome': name,
            'registros': row_count,
            'colunas': len(info.get('columns', [])),
            'status': 'OK' if 'error' not in info else 'Erro',
            'tem_amostra': 'sample_size' in info
        })
    
    # Ordenação
    sort_by = st.selectbox("Ordenar por:", 
                          ["nome", "registros", "colunas"], 
                          index=1)
    sort_asc = st.checkbox("Ordem crescente", value=False)
    
    filtered_tables.sort(key=lambda x: x[sort_by], reverse=not sort_asc)
    
    # Mostra lista
    st.subheader(f"📄 Tabelas Disponíveis ({len(filtered_tables)})")
    
    if filtered_tables:
        df_tables = pd.DataFrame(filtered_tables)
        st.dataframe(
            df_tables, 
            use_container_width=True,
            height=300,
            column_config={
                "nome": "Tabela",
                "registros": st.column_config.NumberColumn(
                    "Registros",
                    format="%d"
                ),
                "colunas": "Colunas",
                "status": "Status",
                "tem_amostra": "Amostra"
            }
        )
        
        # Seleção para detalhes
        selected_table = st.selectbox(
            "Selecione uma tabela para ver detalhes:",
            [t['nome'] for t in filtered_tables]
        )
        
        if selected_table:
            show_table_details(tables_info[selected_table], selected_table)
    else:
        st.info("Nenhuma tabela encontrada com os filtros atuais.")

def show_table_details(info: dict, table_name: str):
    """Mostra detalhes de uma tabela específica"""
    
    st.subheader(f"📋 {table_name}")
    
    # Métricas rápidas
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Registros", info.get('total_rows', 'N/A'))
    
    with col2:
        st.metric("Colunas", len(info.get('columns', [])))
    
    with col3:
        if 'sample_size' in info:
            st.metric("Amostra", info['sample_size'])
        else:
            st.metric("Amostra", "N/A")
    
    with col4:
        status = "✅ OK" if 'error' not in info else "❌ Erro"
        st.metric("Status", status)
    
    # Se houve erro
    if 'error' in info:
        st.error(f"Erro ao ler tabela: {info['error']}")
        return
    
    # Abas de detalhes
    tab1, tab2, tab3 = st.tabs(["Colunas", "Amostra", "Estatísticas"])
    
    with tab1:
        # Lista de colunas com detalhes
        if 'columns' in info:
            cols_data = []
            for col in info['columns']:
                col_info = {
                    'Coluna': col,
                    'Tipo': info.get('dtypes', {}).get(col, '?'),
                    'Únicos': info.get('unique_values', {}).get(col, '?'),
                    'Nulos %': f"{info.get('null_percentage', {}).get(col, 0):.1f}%"
                }
                cols_data.append(col_info)
            
            cols_df = pd.DataFrame(cols_data)
            st.dataframe(cols_df, use_container_width=True)
    
    with tab2:
        # Mostra dados de amostra se disponível
        if 'sample_data' in info and info['sample_data']:
            sample_df = pd.DataFrame(info['sample_data'])
            st.dataframe(sample_df, use_container_width=True, height=300)
        else:
            st.info("Nenhuma amostra disponível para esta tabela.")
    
    with tab3:
        # Estatísticas básicas
        if 'unique_values' in info:
            st.write("**Distribuição de Valores Únicos:**")
            
            unique_vals = []
            for col, count in info['unique_values'].items():
                if isinstance(count, (int, float)):
                    unique_vals.append({
                        'Coluna': col,
                        'Valores Únicos': count,
                        'Tipo': info.get('dtypes', {}).get(col, '?')
                    })
            
            if unique_vals:
                unique_df = pd.DataFrame(unique_vals)
                unique_df = unique_df.sort_values('Valores Únicos', ascending=False)
                st.dataframe(unique_df, use_container_width=True)

if __name__ == "__main__":
    main()