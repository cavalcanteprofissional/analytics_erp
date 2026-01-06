# app.py - VERSÃO CORRIGIDA (sem psutil)
import streamlit as st
import pandas as pd
from pathlib import Path
import sys
import os
import platform
from datetime import datetime

# Configuração da página
st.set_page_config(
    page_title="ERP Analytics Pro",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Adiciona src ao path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# CSS customizado
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1E3A8A;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #374151;
        margin-top: 1.5rem;
        margin-bottom: 1rem;
        border-bottom: 2px solid #E5E7EB;
        padding-bottom: 0.5rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #F3F4F6;
        border-radius: 5px 5px 0px 0px;
        gap: 1px;
        padding: 10px 16px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #4F46E5;
        color: white;
    }
    .success-box {
        background-color: #D1FAE5;
        border-left: 5px solid #10B981;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
    .warning-box {
        background-color: #FEF3C7;
        border-left: 5px solid #F59E0B;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
    .info-box {
        background-color: #DBEAFE;
        border-left: 5px solid #3B82F6;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
    .error-box {
        background-color: #FEE2E2;
        border-left: 5px solid #EF4444;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Título principal
st.markdown('<h1 class="main-header">📊 ERP Analytics Pro</h1>', unsafe_allow_html=True)
st.markdown("""
<div class="info-box">
<strong>🚀 Sistema de Análise Inteligente de Dados de ERP</strong><br>
Analise automaticamente 368 tabelas, descubra relacionamentos e gere diagramas ER.
</div>
""", unsafe_allow_html=True)

def main():
    """Função principal do aplicativo"""
    
    # Sidebar
    with st.sidebar:
        # Logo ou ícone
        st.markdown("""
        <div style="text-align: center; margin-bottom: 2rem;">
            <div style="font-size: 3rem;">📊</div>
            <h3>ERP Analytics</h3>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("### ⚙️ Configuração")
        
        # Configuração de paths
        data_path = st.text_input(
            "📁 Caminho dos CSVs:",
            value="data/raw",
            help="Pasta onde estão os arquivos CSV exportados do ERP"
        )
        
        # Verifica se a pasta existe
        if not Path(data_path).exists():
            st.markdown('<div class="warning-box">', unsafe_allow_html=True)
            st.markdown(f"**Pasta não encontrada:** `{data_path}`")
            st.markdown('</div>', unsafe_allow_html=True)
            
            if st.button("📂 Criar pasta data/raw", use_container_width=True):
                Path("data/raw").mkdir(parents=True, exist_ok=True)
                st.success("✅ Pasta criada! Adicione seus CSVs.")
                st.rerun()
        
        # Configurações de análise
        st.markdown("---")
        st.markdown("### 🔧 Configurações de Análise")
        
        col1, col2 = st.columns(2)
        with col1:
            max_tables = st.slider(
                "Tabelas máx:",
                min_value=10,
                max_value=200,
                value=50,
                help="Número máximo de tabelas para analisar"
            )
        
        with col2:
            sample_size = st.slider(
                "Amostra:",
                min_value=100,
                max_value=10000,
                value=1000,
                step=100,
                help="Tamanho da amostra para análise inicial"
            )
        
        # Salva configurações
        st.session_state.max_tables = max_tables
        st.session_state.sample_size = sample_size
        
        # Botões de ação
        st.markdown("---")
        st.markdown("### ⚡ Ações Rápidas")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Limpar Cache", type="secondary", use_container_width=True):
                clear_cache()
        
        with col2:
            if st.button("📊 Sistema", type="secondary", use_container_width=True):
                show_system_info()
        
        # Informações do sistema
        st.markdown("---")
        st.markdown("### ℹ️ Sobre")
        st.caption(f"Python: {sys.version.split()[0]}")
        st.caption(f"Streamlit: {st.__version__}")
        st.caption(f"Pandas: {pd.__version__}")
        st.caption(f"Hora: {datetime.now().strftime('%H:%M:%S')}")
    
    # Inicialização do estado da sessão
    initialize_session_state()
    
    # Container principal
    main_container = st.container()
    
    with main_container:
        # Verifica se temos dados para análise
        if st.session_state.analyzer is None:
            show_welcome_screen(data_path)
        else:
            show_main_interface()
    
    # Rodapé
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    with col2:
        st.caption(f"**ERP Analytics Pro** © {datetime.now().year} | v1.0.0")

def initialize_session_state():
    """Inicializa todas as variáveis de estado da sessão"""
    if 'analyzer' not in st.session_state:
        st.session_state.analyzer = None
    if 'tables_info' not in st.session_state:
        st.session_state.tables_info = None
    if 'miner' not in st.session_state:
        st.session_state.miner = None
    if 'relationships' not in st.session_state:
        st.session_state.relationships = None
    if 'mermaid_code' not in st.session_state:
        st.session_state.mermaid_code = None
    if 'diagram_generator' not in st.session_state:
        st.session_state.diagram_generator = None
    if 'data_loader' not in st.session_state:
        st.session_state.data_loader = None
    if 'analysis_complete' not in st.session_state:
        st.session_state.analysis_complete = False
    if 'max_tables' not in st.session_state:
        st.session_state.max_tables = 50
    if 'sample_size' not in st.session_state:
        st.session_state.sample_size = 1000

def show_welcome_screen(data_path: str):
    """Tela inicial quando não há análise realizada"""
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown('<div class="info-box">', unsafe_allow_html=True)
        st.markdown("""
        ### 👋 Bem-vindo ao ERP Analytics Pro!
        
        **Recursos disponíveis:**
        
        ✅ **Análise Automática** - Descubra a estrutura do seu ERP  
        ✅ **Detecção de Relacionamentos** - Encontre FKs automaticamente  
        ✅ **Diagramas ER** - Visualize o banco de dados  
        ✅ **Exploração Inteligente** - Analise tabelas individualmente  
        
        **Próximos passos:**
        1. Certifique-se de que seus CSVs estão em `data/raw/`
        2. Clique no botão abaixo para iniciar a análise
        3. Explore os resultados nas abas
        """)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Botão principal
        if st.button("🚀 INICIAR ANÁLISE DO ERP", type="primary", use_container_width=True):
            with st.spinner("🔄 Analisando estrutura do ERP..."):
                try:
                    from schema_analyzer import ERPSchemaAnalyzer
                    
                    analyzer = ERPSchemaAnalyzer(data_path)
                    tables_info = analyzer.analyze_all_tables(
                        sample_size=st.session_state.sample_size,
                        max_tables=st.session_state.max_tables
                    )
                    
                    if tables_info:
                        st.session_state.analyzer = analyzer
                        st.session_state.tables_info = tables_info
                        st.session_state.analysis_complete = True
                        
                        st.success(f"✅ Análise concluída! {len(tables_info)} tabelas analisadas.")
                        st.rerun()
                    else:
                        st.error("❌ Nenhuma tabela encontrada. Verifique os arquivos CSV.")
                        
                except Exception as e:
                    st.error(f"❌ Erro na análise: {str(e)}")
                    st.info("""
                    **Solução de problemas:**
                    1. Verifique se existem arquivos CSV na pasta
                    2. Verifique permissões de leitura
                    3. Tente com menos tabelas (ajuste o slider)
                    """)
        
        # Se houver arquivos, mostra preview
        if Path(data_path).exists():
            csv_files = list(Path(data_path).glob("*.csv"))
            if csv_files:
                st.markdown("---")
                st.markdown("### 📁 Arquivos Encontrados")
                
                files_df = pd.DataFrame([
                    {
                        "Arquivo": f.name,
                        "Tamanho (KB)": f"{f.stat().st_size / 1024:.1f}",
                        "Modificação": pd.Timestamp(f.stat().st_mtime, unit='s').strftime('%d/%m %H:%M')
                    }
                    for f in csv_files[:10]  # Mostra apenas 10
                ])
                
                st.dataframe(files_df, width='stretch', hide_index=True)
                
                if len(csv_files) > 10:
                    st.caption(f"... e mais {len(csv_files) - 10} arquivos")
            else:
                st.markdown('<div class="warning-box">', unsafe_allow_html=True)
                st.markdown(f"Nenhum arquivo CSV encontrado em `{data_path}`")
                st.markdown('</div>', unsafe_allow_html=True)

def show_main_interface():
    """Interface principal após análise"""
    
    # Header com métricas
    show_metrics_header()
    
    # Abas principais
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📋 Visão Geral", 
        "🔗 Relacionamentos", 
        "📊 Diagrama ER", 
        "🔍 Explorar Tabelas",
        "⚙️ Configurações"
    ])
    
    with tab1:
        show_overview()
    
    with tab2:
        show_relationships()
    
    with tab3:
        show_er_diagrams()
    
    with tab4:
        explore_tables()
    
    with tab5:
        show_settings()

def show_metrics_header():
    """Mostra header com métricas"""
    
    tables_info = st.session_state.tables_info
    
    if not tables_info:
        return
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📊 Tabelas", len(tables_info))
    
    with col2:
        total_rows = sum(
            info.get('total_rows', 0) 
            for info in tables_info.values() 
            if isinstance(info.get('total_rows'), int)
        )
        st.metric("📈 Registros", f"{total_rows:,}")
    
    with col3:
        error_count = sum(1 for info in tables_info.values() if 'error' in info)
        if error_count > 0:
            st.metric("⚠️ Com Erro", error_count, delta_color="inverse")
        else:
            st.metric("✅ Sem Erro", "0")
    
    with col4:
        if 'relationships' in st.session_state and st.session_state.relationships:
            rel_count = len(st.session_state.relationships)
            st.metric("🔗 Relacionamentos", rel_count)
        else:
            st.metric("🔗 Relacionamentos", "0")

def show_overview():
    """Mostra visão geral das tabelas"""
    
    tables_info = st.session_state.tables_info
    
    st.markdown('<h3 class="sub-header">📈 Estatísticas Gerais</h3>', unsafe_allow_html=True)
    
    # Gráfico de distribuição
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Distribuição por tamanho
        size_data = []
        for name, info in tables_info.items():
            if 'total_rows' in info and isinstance(info['total_rows'], int):
                size_data.append({
                    'Tabela': name,
                    'Registros': info['total_rows'],
                    'Colunas': len(info.get('columns', [])),
                    'Categoria': categorize_table(name)
                })
        
        if size_data:
            df_size = pd.DataFrame(size_data)
            
            # Top 10 maiores
            st.markdown("**📊 Top 10 Tabelas por Volume**")
            top_10 = df_size.nlargest(10, 'Registros')
            
            # Gráfico de barras
            try:
                import plotly.express as px
                
                fig = px.bar(
                    top_10,
                    x='Tabela',
                    y='Registros',
                    color='Categoria',
                    title="Top 10 Tabelas",
                    hover_data=['Colunas'],
                    color_discrete_sequence=px.colors.qualitative.Set3
                )
                fig.update_layout(height=400, showlegend=True)
                st.plotly_chart(fig, use_container_width=True)
                
            except ImportError:
                # Fallback para tabela
                st.dataframe(top_10[['Tabela', 'Registros', 'Colunas', 'Categoria']], 
                           width='stretch', hide_index=True)
    
    with col2:
        # Distribuição por categoria
        st.markdown("**📁 Distribuição por Categoria**")
        
        categories_count = {}
        for name in tables_info.keys():
            category = categorize_table(name)
            categories_count[category] = categories_count.get(category, 0) + 1
        
        cat_df = pd.DataFrame({
            'Categoria': list(categories_count.keys()),
            'Quantidade': list(categories_count.values())
        }).sort_values('Quantidade', ascending=False)
        
        # Tabela simples (evita plotly para evitar dependências extras)
        st.dataframe(cat_df, width='stretch', hide_index=True)
        
        # Estatísticas rápidas
        st.markdown("**📐 Estatísticas**")
        
        total_cols = sum(len(info.get('columns', [])) for info in tables_info.values())
        avg_cols = total_cols / len(tables_info) if tables_info else 0
        max_cols = max(len(info.get('columns', [])) for info in tables_info.values())
        
        stats_data = {
            'Métrica': ['Colunas (média)', 'Colunas (máx)', 'Tabelas analisadas'],
            'Valor': [f"{avg_cols:.1f}", str(max_cols), str(len(tables_info))]
        }
        stats_df = pd.DataFrame(stats_data)
        st.dataframe(stats_df, width='stretch', hide_index=True)
    
    # Tabela resumo completa
    st.markdown('<h3 class="sub-header">📋 Lista Completa de Tabelas</h3>', unsafe_allow_html=True)
    
    # Filtros
    col1, col2, col3 = st.columns(3)
    
    with col1:
        filter_search = st.text_input("🔎 Buscar tabela:", key="filter_search")
    
    with col2:
        filter_category = st.selectbox(
            "Categoria:",
            ["Todas"] + sorted(list(set(categorize_table(name) for name in tables_info.keys()))),
            key="filter_category"
        )
    
    with col3:
        sort_by = st.selectbox("Ordenar por:", ["Nome", "Registros ▼", "Colunas ▼"], key="sort_by")
    
    # Aplica filtros
    filtered_tables = []
    for name, info in tables_info.items():
        # Filtro busca
        if filter_search and filter_search.lower() not in name.lower():
            continue
        
        # Filtro categoria
        if filter_category != "Todas" and categorize_table(name) != filter_category:
            continue
        
        rows = info.get('total_rows', 0)
        filtered_tables.append({
            'Tabela': name,
            'Registros': rows if isinstance(rows, int) else 'N/A',
            'Colunas': len(info.get('columns', [])),
            'Categoria': categorize_table(name),
            'Status': '✅' if 'error' not in info else '❌'
        })
    
    # Ordena
    if sort_by == "Registros ▼":
        filtered_tables.sort(key=lambda x: x['Registros'] if isinstance(x['Registros'], int) else 0, reverse=True)
    elif sort_by == "Colunas ▼":
        filtered_tables.sort(key=lambda x: x['Colunas'], reverse=True)
    else:  # Nome
        filtered_tables.sort(key=lambda x: x['Tabela'])
    
    # Mostra tabela
    if filtered_tables:
        df_display = pd.DataFrame(filtered_tables)
        
        # Configura colunas
        column_config = {
            "Tabela": st.column_config.TextColumn(width="large"),
            "Registros": st.column_config.NumberColumn(format="%d"),
            "Colunas": st.column_config.NumberColumn(format="%d"),
            "Categoria": st.column_config.TextColumn(width="medium"),
            "Status": st.column_config.TextColumn(width="small")
        }
        
        st.dataframe(
            df_display,
            column_config=column_config,
            width='stretch',
            height=400,
            hide_index=True
        )
        
        # Botão de exportação
        if st.button("📥 Exportar para CSV", use_container_width=True):
            csv = df_display.to_csv(index=False)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            st.download_button(
                label="💾 Download CSV",
                data=csv,
                file_name=f"erp_tables_{timestamp}.csv",
                mime="text/csv"
            )
    else:
        st.info("Nenhuma tabela encontrada com os filtros atuais.")

# NO app.py, ATUALIZE A FUNÇÃO show_relationships:

def show_relationships():
    """Mostra relacionamentos entre tabelas"""
    
    tables_info = st.session_state.tables_info
    
    st.markdown('<h3 class="sub-header">🔗 Análise de Relacionamentos</h3>', unsafe_allow_html=True)
    
    # Botão para detectar relacionamentos
    if st.button("🔍 DETECTAR RELACIONAMENTOS", type="primary", use_container_width=True):
        with st.spinner("🔄 Analisando possíveis relacionamentos..."):
            try:
                from relationship_miner import RelationshipMiner
                
                # Cria minerador
                miner = RelationshipMiner(tables_info)
                
                # Minera relacionamentos
                relationships = miner.mine_relationships()
                
                # Salva na sessão
                st.session_state.miner = miner
                st.session_state.relationships = relationships
                
                # Mostra resumo
                summary = miner.get_relationships_summary()
                st.success(f"✅ {summary['total']} relacionamentos detectados!")
                
                # Mostra detalhes do resumo
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("🟢 Alta Confiança", summary.get('high_confidence', 0))
                with col2:
                    st.metric("🟡 Média Confiança", summary.get('medium_confidence', 0))
                with col3:
                    st.metric("🔴 Baixa Confiança", summary.get('low_confidence', 0))
                
                # Mostra por tipo
                if summary.get('by_type'):
                    st.markdown("**📊 Por Tipo:**")
                    for rel_type, count in summary['by_type'].items():
                        st.write(f"- {rel_type}: {count}")
                
            except Exception as e:
                st.error(f"❌ Erro na detecção: {str(e)}")
                import traceback
                st.code(traceback.format_exc())
    
    # Se já detectou relacionamentos
    if 'relationships' in st.session_state and st.session_state.relationships:
        relationships = st.session_state.relationships
        
        # Mostra estatísticas
        st.markdown("---")
        st.markdown("#### 📊 Estatísticas dos Relacionamentos")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            high_conf = sum(1 for r in relationships if r.get('confidence', 0) > 0.8)
            st.metric("🟢 Alta Confiança", high_conf)
        
        with col2:
            med_conf = sum(1 for r in relationships if 0.5 <= r.get('confidence', 0) <= 0.8)
            st.metric("🟡 Média Confiança", med_conf)
        
        with col3:
            low_conf = sum(1 for r in relationships if r.get('confidence', 0) < 0.5)
            st.metric("🔴 Baixa Confiança", low_conf)
        
        # Filtros
        st.markdown("---")
        st.markdown("#### 🔍 Filtrar Relacionamentos")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            min_confidence = st.slider(
                "Confiança mínima:",
                0.0, 1.0, 0.3, 0.1,
                help="Mostra apenas relacionamentos com confiança acima deste valor"
            )
        
        with col2:
            rel_type_filter = st.selectbox(
                "Tipo:",
                ["Todos"] + sorted(list(set(r.get('relationship_type', '') for r in relationships)))
            )
        
        with col3:
            search_term = st.text_input("Buscar tabela:", "")
        
        # Filtra relacionamentos
        filtered_rels = []
        for rel in relationships:
            # Filtro confiança
            if rel.get('confidence', 0) < min_confidence:
                continue
            
            # Filtro tipo
            if rel_type_filter != "Todos" and rel.get('relationship_type') != rel_type_filter:
                continue
            
            # Filtro busca
            if search_term:
                source = rel.get('source_table', '').lower()
                target = rel.get('target_table', '').lower()
                search_lower = search_term.lower()
                if search_lower not in source and search_lower not in target:
                    continue
            
            filtered_rels.append(rel)
        
        # Mostra resultados
        st.markdown(f"#### 📋 Relacionamentos Filtrados ({len(filtered_rels)})")
        
        if filtered_rels:
            # Ordena por confiança
            filtered_rels.sort(key=lambda x: x.get('confidence', 0), reverse=True)
            
            # Cria DataFrame para exibição
            display_data = []
            for rel in filtered_rels:
                confidence = rel.get('confidence', 0)
                
                # Determina ícone baseado na confiança
                if confidence > 0.8:
                    icon = "🟢"
                elif confidence > 0.5:
                    icon = "🟡"
                else:
                    icon = "🔴"
                
                display_data.append({
                    " ": icon,
                    "Origem": rel.get('source_table', ''),
                    "Destino": rel.get('target_table', ''),
                    "Coluna": rel.get('relationship_column', ''),
                    "Tipo": rel.get('relationship_type', ''),
                    "Confiança": f"{confidence:.1%}",
                    "Evidência": rel.get('evidence', '')[:50] + "..." if rel.get('evidence', '') else ''
                })
            
            # Cria DataFrame
            df_display = pd.DataFrame(display_data)
            
            # Mostra tabela
            st.dataframe(
                df_display,
                width='stretch',
                height=400,
                hide_index=True,
                column_config={
                    " ": st.column_config.TextColumn(width="small"),
                    "Origem": st.column_config.TextColumn(width="medium"),
                    "Destino": st.column_config.TextColumn(width="medium"),
                    "Coluna": st.column_config.TextColumn(width="medium"),
                    "Tipo": st.column_config.TextColumn(width="small"),
                    "Confiança": st.column_config.TextColumn(width="small"),
                    "Evidência": st.column_config.TextColumn(width="large")
                }
            )
            
            # Botões de exportação
            st.markdown("---")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("📥 Exportar CSV", use_container_width=True):
                    # Prepara dados para CSV
                    csv_data = []
                    for rel in filtered_rels:
                        csv_data.append({
                            'source_table': rel.get('source_table', ''),
                            'target_table': rel.get('target_table', ''),
                            'relationship_column': rel.get('relationship_column', ''),
                            'relationship_type': rel.get('relationship_type', ''),
                            'confidence': rel.get('confidence', 0),
                            'evidence': rel.get('evidence', '')
                        })
                    
                    df_csv = pd.DataFrame(csv_data)
                    csv_str = df_csv.to_csv(index=False)
                    
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    st.download_button(
                        label="💾 Download CSV",
                        data=csv_str,
                        file_name=f"erp_relationships_{timestamp}.csv",
                        mime="text/csv"
                    )
            
            with col2:
                if st.button("🔄 Redetectar", use_container_width=True):
                    # Limpa cache e redetecta
                    if 'miner' in st.session_state:
                        del st.session_state.miner
                    if 'relationships' in st.session_state:
                        del st.session_state.relationships
                    st.rerun()
            
            with col3:
                if st.button("📊 Visualizar Grafo", use_container_width=True):
                    # Tenta mostrar visualização gráfica
                    try:
                        import networkx as nx
                        import plotly.graph_objects as go
                        
                        # Cria grafo
                        G = nx.DiGraph()
                        
                        # Adiciona nós (tabelas)
                        tables_in_rels = set()
                        for rel in filtered_rels:
                            tables_in_rels.add(rel.get('source_table'))
                            tables_in_rels.add(rel.get('target_table'))
                        
                        for table in tables_in_rels:
                            G.add_node(table)
                        
                        # Adiciona arestas (relacionamentos)
                        for rel in filtered_rels:
                            source = rel.get('source_table')
                            target = rel.get('target_table')
                            confidence = rel.get('confidence', 0)
                            
                            # Define largura baseada na confiança
                            width = 1 + (confidence * 3)
                            
                            G.add_edge(source, target, 
                                      weight=confidence,
                                      label=rel.get('relationship_column', ''))
                        
                        # Layout do grafo
                        pos = nx.spring_layout(G, k=2, iterations=50)
                        
                        # Prepara dados para Plotly
                        edge_x, edge_y = [], []
                        for edge in G.edges():
                            x0, y0 = pos[edge[0]]
                            x1, y1 = pos[edge[1]]
                            edge_x.extend([x0, x1, None])
                            edge_y.extend([y0, y1, None])
                        
                        edge_trace = go.Scatter(
                            x=edge_x, y=edge_y,
                            line=dict(width=1, color='#888'),
                            hoverinfo='none',
                            mode='lines'
                        )
                        
                        node_x, node_y, node_text = [], [], []
                        for node in G.nodes():
                            x, y = pos[node]
                            node_x.append(x)
                            node_y.append(y)
                            node_text.append(node)
                        
                        node_trace = go.Scatter(
                            x=node_x, y=node_y,
                            mode='markers+text',
                            text=node_text,
                            textposition="top center",
                            marker=dict(
                                size=20,
                                color='#4F46E5',
                                line_width=2
                            ),
                            hoverinfo='text'
                        )
                        
                        fig = go.Figure(data=[edge_trace, node_trace],
                                       layout=go.Layout(
                                           title="Visualização de Relacionamentos",
                                           showlegend=False,
                                           hovermode='closest',
                                           margin=dict(b=20, l=5, r=5, t=40),
                                           xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                                           yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                                           height=500
                                       ))
                        
                        st.plotly_chart(fig, use_container_width=True)
                        
                    except ImportError:
                        st.info("Instale `plotly` e `networkx` para visualização gráfica")
            
            # Análise por tabela específica
            st.markdown("---")
            st.markdown("#### 🎯 Análise por Tabela")
            
            # Lista todas as tabelas envolvidas nos relacionamentos
            all_tables = set()
            for rel in relationships:
                all_tables.add(rel.get('source_table'))
                all_tables.add(rel.get('target_table'))
            
            selected_table = st.selectbox(
                "Selecione uma tabela para análise detalhada:",
                sorted(list(all_tables))
            )
            
            if selected_table:
                # Filtra relacionamentos da tabela selecionada
                table_rels = []
                for rel in relationships:
                    if (rel.get('source_table') == selected_table or 
                        rel.get('target_table') == selected_table):
                        table_rels.append(rel)
                
                if table_rels:
                    # Divide em referências (outgoing) e referenciados (incoming)
                    outgoing = [r for r in table_rels if r.get('source_table') == selected_table]
                    incoming = [r for r in table_rels if r.get('target_table') == selected_table]
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown(f"**→ Referências ({len(outgoing)})**")
                        for rel in outgoing[:5]:  # Limita a 5
                            confidence = rel.get('confidence', 0)
                            icon = "🟢" if confidence > 0.8 else "🟡" if confidence > 0.5 else "🔴"
                            
                            st.markdown(f"""
                            {icon} **{rel.get('target_table')}**  
                            `{rel.get('relationship_column', '?')}`  
                            *{rel.get('relationship_type', '')}* ({confidence:.1%})
                            """)
                    
                    with col2:
                        st.markdown(f"**← É Referenciada ({len(incoming)})**")
                        for rel in incoming[:5]:  # Limita a 5
                            confidence = rel.get('confidence', 0)
                            icon = "🟢" if confidence > 0.8 else "🟡" if confidence > 0.5 else "🔴"
                            
                            st.markdown(f"""
                            {icon} **{rel.get('source_table')}**  
                            `{rel.get('relationship_column', '?')}`  
                            *{rel.get('relationship_type', '')}* ({confidence:.1%})
                            """)
                    
                    # Sugestões de análise
                    if outgoing or incoming:
                        st.markdown("#### 💡 Sugestões de Análise")
                        
                        if outgoing:
                            st.write("✅ **Tabelas referenciadas:** Esta tabela parece ser uma tabela **mestre**")
                        
                        if incoming:
                            st.write("✅ **Referências recebidas:** Esta tabela parece ser uma tabela **transacional**")
                        
                        if not outgoing and not incoming:
                            st.write("ℹ️ **Isolada:** Esta tabela não tem relacionamentos detectados")
                else:
                    st.info("Nenhum relacionamento detectado para esta tabela.")
        
        else:
            st.info("Nenhum relacionamento encontrado com os filtros atuais.")
            
            if min_confidence > 0:
                st.write(f"**Dica:** Reduza a confiança mínima (atualmente {min_confidence}) para ver mais relacionamentos.")
    
    else:
        # Se não detectou ainda
        st.markdown('<div class="info-box">', unsafe_allow_html=True)
        st.markdown("""
        ### 🔍 Relacionamentos Não Detectados
        
        Para descobrir relacionamentos entre suas tabelas:
        
        1. **Clique no botão acima** para iniciar a detecção
        2. **Aguarde** enquanto o sistema analisa os nomes das colunas
        3. **Explore** os relacionamentos encontrados
        
        **O que será analisado:**
        - Nomes de colunas que parecem chaves estrangeiras
        - Padrões comuns em ERPs (ex: ClienteID, CodProduto)
        - Relacionamentos baseados em dados comuns
        """)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Mostra exemplo do que será detectado
        if st.session_state.tables_info:
            st.markdown("#### 👀 Exemplo do que será analisado:")
            
            # Pega algumas tabelas de exemplo
            example_tables = list(st.session_state.tables_info.keys())[:5]
            
            for table in example_tables:
                info = st.session_state.tables_info[table]
                if 'columns' in info:
                    # Mostra colunas que parecem ser chaves
                    id_columns = []
                    for col in info['columns'][:5]:  # Primeiras 5 colunas
                        col_lower = col.lower()
                        if any(kw in col_lower for kw in ['id', 'cod', 'code', 'key']):
                            id_columns.append(col)
                    
                    if id_columns:
                        st.write(f"**{table}:** {', '.join(id_columns)}")

def show_er_diagrams():
    """Mostra diagramas ER gerados automaticamente"""
    
    st.markdown('<h3 class="sub-header">📊 Diagrama de Entidade-Relacionamento</h3>', unsafe_allow_html=True)
    
    tables_info = st.session_state.tables_info
    
    if 'relationships' not in st.session_state:
        st.markdown('<div class="info-box">', unsafe_allow_html=True)
        st.markdown("""
        **Diagrama não disponível**
        
        Para gerar diagramas ER:
        1. Primeiro detecte relacionamentos na aba anterior
        2. Retorne aqui para visualizar o diagrama
        """)
        st.markdown('</div>', unsafe_allow_html=True)
        return
    
    relationships = st.session_state.relationships
    
    # Configurações
    with st.expander("⚙️ Configurações do Diagrama", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            max_tables = st.slider(
                "Máx. tabelas:",
                5, 30, 10,
                help="Número máximo de tabelas no diagrama"
            )
        
        with col2:
            min_confidence = st.slider(
                "Confiança mínima:",
                0.0, 1.0, 0.6, 0.1
            )
    
    # Botão para gerar
    if st.button("🔄 GERAR DIAGRAMA ER", type="primary", use_container_width=True):
        with st.spinner("🖼️ Gerando diagrama..."):
            try:
                # Tenta importar módulos
                try:
                    from diagram_generator import ERDiagramGenerator
                    
                    generator = ERDiagramGenerator(relationships, tables_info)
                    mermaid_code = generator.generate_mermaid_er_diagram(max_tables)
                    
                    st.session_state.mermaid_code = mermaid_code
                    st.session_state.diagram_generator = generator
                    
                    st.success("✅ Diagrama gerado com sucesso!")
                    
                except ImportError:
                    # Fallback: gera diagrama simples
                    st.session_state.mermaid_code = generate_simple_mermaid(relationships, tables_info, max_tables)
                    st.success("✅ Diagrama simples gerado!")
                
            except Exception as e:
                st.error(f"❌ Erro ao gerar diagrama: {str(e)}")
    
    # Se tem diagrama gerado
    if 'mermaid_code' in st.session_state and st.session_state.mermaid_code:
        mermaid_code = st.session_state.mermaid_code
        
        # Abas para diferentes visualizações
        tab1, tab2 = st.tabs(["👁️ Visualização", "📝 Código"])
        
        with tab1:
            # Renderiza Mermaid
            try:
                # HTML simples para Mermaid
                mermaid_html = f"""
                <div class="mermaid">
                {mermaid_code}
                </div>
                <script src="https://cdn.jsdelivr.net/npm/mermaid@10.6.1/dist/mermaid.min.js"></script>
                <script>
                    mermaid.initialize({{startOnLoad: true, theme: 'default'}});
                </script>
                """
                
                st.components.v1.html(mermaid_html, height=600, scrolling=True)
                
            except:
                st.info("""
                **Visualização alternativa:**
                
                Para ver o diagrama interativo:
                1. Copie o código da aba "📝 Código"
                2. Cole em https://mermaid.live/
                3. Visualize online
                """)
        
        with tab2:
            # Mostra código
            st.code(mermaid_code, language="mermaid")
            
            # Contadores
            lines = mermaid_code.split('\n')
            table_count = sum(1 for line in lines if '{' in line and '}' in line and 'erDiagram' not in line)
            rel_count = sum(1 for line in lines if '--' in line and 'erDiagram' not in line)
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Tabelas no diagrama", table_count)
            with col2:
                st.metric("Relacionamentos", rel_count)
            
            # Botão de download
            if st.button("💾 Download Código Mermaid", use_container_width=True):
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                st.download_button(
                    label="📥 Download .mmd",
                    data=mermaid_code,
                    file_name=f"er_diagram_{timestamp}.mmd",
                    mime="text/plain"
                )
    
    else:
        st.info("👈 Gere o diagrama primeiro usando o botão acima")

def explore_tables():
    """Permite explorar tabelas individualmente"""
    
    tables_info = st.session_state.tables_info
    
    st.markdown('<h3 class="sub-header">🔍 Explorador de Tabelas</h3>', unsafe_allow_html=True)
    
    # Barra de busca
    search_term = st.text_input("🔎 Buscar tabela por nome:", "")
    
    # Filtra tabelas
    filtered_tables = []
    for name, info in tables_info.items():
        if search_term and search_term.lower() not in name.lower():
            continue
        
        filtered_tables.append((name, info))
    
    # Ordena por nome
    filtered_tables.sort(key=lambda x: x[0])
    
    # Mostra lista em cards
    st.markdown(f"#### 📄 Tabelas ({len(filtered_tables)})")
    
    if not filtered_tables:
        st.info("Nenhuma tabela encontrada com o termo de busca.")
        return
    
    # Paginação simples
    items_per_page = 12
    total_pages = max(1, (len(filtered_tables) + items_per_page - 1) // items_per_page)
    
    page = st.number_input("Página:", 1, total_pages, 1, key="explore_page")
    start_idx = (page - 1) * items_per_page
    end_idx = min(start_idx + items_per_page, len(filtered_tables))
    
    # Cria grid de cards
    cols = st.columns(3)
    for idx, (table_name, info) in enumerate(filtered_tables[start_idx:end_idx]):
        col_idx = idx % 3
        with cols[col_idx]:
            with st.container(border=True):
                # Header do card
                st.markdown(f"**{table_name}**")
                
                # Informações básicas
                rows = info.get('total_rows', 'N/A')
                cols_count = len(info.get('columns', []))
                category = categorize_table(table_name)
                
                st.caption(f"📊 Registros: {rows if isinstance(rows, int) else rows:,}")
                st.caption(f"🗂️ Colunas: {cols_count}")
                st.caption(f"🏷️ {category}")
                
                # Status
                if 'error' in info:
                    st.error(f"Erro: {info['error'][:50]}...")
                else:
                    st.success("✅ OK")
                
                # Botão para detalhes
                if st.button("🔍 Analisar", key=f"analyze_{table_name}_{idx}", use_container_width=True):
                    st.session_state.selected_table = table_name
                    st.rerun()
    
    # Controle de paginação
    if total_pages > 1:
        st.caption(f"Página {page} de {total_pages} • {len(filtered_tables)} tabelas")
    
    # Se uma tabela foi selecionada
    if 'selected_table' in st.session_state and st.session_state.selected_table:
        table_name = st.session_state.selected_table
        info = tables_info.get(table_name, {})
        
        st.markdown("---")
        show_table_details(table_name, info)

def show_table_details(table_name: str, info: dict):
    """Mostra detalhes de uma tabela específica"""
    
    st.markdown(f'<h3 class="sub-header">📋 {table_name}</h3>', unsafe_allow_html=True)
    
    # Botão de voltar
    if st.button("← Voltar para lista", key="back_to_list"):
        if 'selected_table' in st.session_state:
            del st.session_state.selected_table
        st.rerun()
    
    # Métricas rápidas
    col1, col2, col3 = st.columns(3)
    
    with col1:
        rows = info.get('total_rows', 'N/A')
        display_rows = f"{rows:,}" if isinstance(rows, int) else rows
        st.metric("📊 Registros", display_rows)
    
    with col2:
        st.metric("🗂️ Colunas", len(info.get('columns', [])))
    
    with col3:
        status = "✅ OK" if 'error' not in info else "❌ Erro"
        st.metric("📈 Status", status)
    
    # Se houve erro
    if 'error' in info:
        st.error(f"**Erro:** {info['error']}")
        return
    
    # Abas de detalhes
    tab1, tab2 = st.tabs(["🗂️ Estrutura", "👀 Amostra"])
    
    with tab1:
        # Lista de colunas
        if 'columns' in info and info['columns']:
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
            st.dataframe(cols_df, width='stretch', height=400, hide_index=True)
        else:
            st.info("Nenhuma informação de colunas disponível")
    
    with tab2:
        # Dados de amostra
        if 'sample_data' in info and info['sample_data']:
            sample_df = pd.DataFrame(info['sample_data'])
            st.dataframe(sample_df, width='stretch', height=400)
            
            # Informações da amostra
            st.caption(f"Amostra de {len(sample_df)} registros")
        else:
            st.info("Nenhuma amostra disponível")

def show_settings():
    """Configurações do sistema"""
    
    st.markdown('<h3 class="sub-header">⚙️ Configurações</h3>', unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["Sistema", "Avançado"])
    
    with tab1:
        st.markdown("#### 🔧 Configurações Gerais")
        
        col1, col2 = st.columns(2)
        
        with col1:
            cache_enabled = st.toggle("Usar cache", value=True, 
                                     help="Melhora performance em análises repetidas")
            st.session_state.use_cache = cache_enabled
            
            auto_refresh = st.toggle("Auto-refresh", value=False,
                                    help="Atualiza automaticamente quando arquivos mudam")
        
        with col2:
            dark_mode = st.toggle("Modo escuro", value=False)
            show_help = st.toggle("Mostrar dicas", value=True)
        
        st.markdown("---")
        
        # Botões de ação
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔄 Reiniciar Análise", type="secondary", use_container_width=True):
                clear_cache(full=True)
                st.success("✅ Análise reiniciada! Recarregue a página.")
        
        with col2:
            if st.button("🗑️ Limpar Dados", type="secondary", use_container_width=True):
                if st.button("⚠️ Confirmar exclusão", type="primary"):
                    clear_cache(full=True)
                    # Também limpa dados processados
                    import shutil
                    if Path("data/processed").exists():
                        shutil.rmtree("data/processed")
                    st.success("✅ Todos os dados foram limpos!")
    
    with tab2:
        st.markdown("#### ⚡ Configurações Avançadas")
        
        col1, col2 = st.columns(2)
        
        with col1:
            chunk_size = st.selectbox(
                "Tamanho do chunk:",
                [1000, 5000, 10000, 50000],
                index=1,
                help="Tamanho dos chunks para leitura de arquivos grandes"
            )
            
            st.session_state.chunk_size = chunk_size
        
        with col2:
            encoding = st.selectbox(
                "Codificação:",
                ["utf-8", "latin-1", "cp1252", "iso-8859-1"],
                index=0,
                help="Codificação dos arquivos CSV"
            )
            
            st.session_state.encoding = encoding
        
        st.markdown("---")
        
        # Informações técnicas
        st.markdown("#### 🖥️ Informações Técnicas")
        
        info_data = {
            "Item": ["Python", "Streamlit", "Pandas", "Sistema", "Arquitetura", "Diretório"],
            "Valor": [
                sys.version.split()[0],
                st.__version__,
                pd.__version__,
                platform.system(),
                platform.machine(),
                os.getcwd()
            ]
        }
        
        info_df = pd.DataFrame(info_data)
        st.dataframe(info_df, width='stretch', hide_index=True)

def clear_cache(full: bool = False):
    """Limpa o cache da sessão"""
    
    keys_to_clear = [
        'miner', 'relationships', 'mermaid_code', 
        'diagram_generator', 'selected_table'
    ]
    
    if full:
        keys_to_clear.extend(['analyzer', 'tables_info', 'analysis_complete'])
    
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]
    
    st.success("✅ Cache limpo com sucesso!")

def show_system_info():
    """Mostra informações do sistema"""
    
    st.markdown('<h3 class="sub-header">🖥️ Informações do Sistema</h3>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Python", sys.version.split()[0])
    
    with col2:
        st.metric("Streamlit", st.__version__)
    
    with col3:
        st.metric("Pandas", pd.__version__)
    
    # Informações detalhadas
    with st.expander("📊 Detalhes do Sistema"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Sistema Operacional**")
            st.write(f"SO: {platform.system()} {platform.release()}")
            st.write(f"Versão: {platform.version()}")
            st.write(f"Arquitetura: {platform.machine()}")
            st.write(f"Processador: {platform.processor()}")
        
        with col2:
            st.write("**Python e Ambiente**")
            st.write(f"Python: {sys.version}")
            st.write(f"Executável: {sys.executable}")
            st.write(f"Plataforma: {platform.platform()}")
            st.write(f"Diretório: {os.getcwd()}")
        
        # Informações do projeto
        st.markdown("---")
        st.markdown("**📁 Projeto ERP Analytics**")
        
        project_info = {
            "Tabelas analisadas": len(st.session_state.tables_info) if st.session_state.tables_info else 0,
            "Relacionamentos": len(st.session_state.relationships) if 'relationships' in st.session_state else 0,
            "Última análise": datetime.now().strftime("%d/%m/%Y %H:%M"),
            "Modo": "Desenvolvimento" if __name__ == "__main__" else "Produção"
        }
        
        for key, value in project_info.items():
            st.write(f"**{key}:** {value}")

def categorize_table(table_name: str) -> str:
    """Categoriza tabela baseada no nome"""
    
    table_lower = table_name.lower()
    
    if any(kw in table_lower for kw in ['cliente', 'clientes']):
        return "👥 Clientes"
    elif any(kw in table_lower for kw in ['produto', 'produtos', 'item', 'prod']):
        return "📦 Produtos"
    elif any(kw in table_lower for kw in ['pedido', 'venda', 'orcamento', 'vendas']):
        return "💰 Vendas"
    elif any(kw in table_lower for kw in ['fornecedor', 'compra']):
        return "🏭 Compras"
    elif any(kw in table_lower for kw in ['estoque', 'inventario', 'almox', 'deposito']):
        return "📊 Estoque"
    elif any(kw in table_lower for kw in ['funcionario', 'folha', 'rh', 'colaborador']):
        return "👨‍💼 Pessoal"
    elif any(kw in table_lower for kw in ['financeiro', 'conta', 'pagamento', 'recebimento', 'titulo']):
        return "💳 Financeiro"
    elif any(kw in table_lower for kw in ['nota', 'nfe', 'nfisc', 'fiscal']):
        return "📄 Fiscal"
    elif any(kw in table_lower for kw in ['rpt', 'relatorio', 'report']):
        return "📈 Relatórios"
    elif any(kw in table_lower for kw in ['movimento', 'transacao', 'lancamento']):
        return "🔄 Transações"
    else:
        return "📁 Outros"

def generate_simple_mermaid(relationships: list, tables_info: dict, max_tables: int = 10) -> str:
    """Gera código Mermaid simples (fallback)"""
    
    # Seleciona tabelas principais
    table_scores = {}
    for table, info in tables_info.items():
        score = info.get('total_rows', 0) / 1000
        if any(kw in table.lower() for kw in ['cliente', 'produto', 'pedido', 'venda']):
            score += 5
        table_scores[table] = score
    
    # Top N tabelas
    top_tables = sorted(table_scores.items(), key=lambda x: x[1], reverse=True)[:max_tables]
    top_table_names = [table for table, _ in top_tables]
    
    # Gera código Mermaid
    mermaid_code = "erDiagram\n"
    
    # Adiciona tabelas
    for table in top_table_names:
        mermaid_code += f"    {table} {{\n"
        mermaid_code += f"        string id\n"
        mermaid_code += f"        string nome\n"
        mermaid_code += f"    }}\n"
    
    # Adiciona relacionamentos
    added_rels = set()
    for rel in relationships:
        source = rel.get('source_table')
        target = rel.get('target_table')
        
        if source in top_table_names and target in top_table_names:
            rel_key = (source, target)
            if rel_key not in added_rels and rel.get('confidence', 0) > 0.6:
                mermaid_code += f"    {source} ||--o{{ {target} : \"via {rel.get('relationship_column', 'id')}\"\n"
                added_rels.add(rel_key)
    
    return mermaid_code

if __name__ == "__main__":
    main()