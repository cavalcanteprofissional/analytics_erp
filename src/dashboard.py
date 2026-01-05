# src/dashboard.py
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from streamlit_agraph import agraph, Node, Edge, Config

class RelationshipDashboard:
    def __init__(self, miner: RelationshipMiner):
        self.miner = miner
        
    def render(self):
        st.title("🔗 Reconstrução de Relacionamentos do ERP")
        
        # Sidebar
        with st.sidebar:
            st.header("Configurações")
            
            confidence_threshold = st.slider(
                "Confiança mínima do relacionamento:",
                0.0, 1.0, 0.6, 0.1
            )
            
            max_relationships = st.slider(
                "Máximo de relacionamentos a mostrar:",
                10, 200, 50
            )
            
            view_type = st.selectbox(
                "Tipo de visualização:",
                ["Grafo Interativo", "Tabela", "Matriz", "Sunburst"]
            )
        
        # Filtra relacionamentos
        filtered_rels = [
            rel for rel in self.miner.relationships_found
            if rel.get('confidence', 0) >= confidence_threshold
        ][:max_relationships]
        
        # Mostra estatísticas
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Relacionamentos encontrados", len(filtered_rels))
        with col2:
            avg_confidence = sum(r.get('confidence', 0) for r in filtered_rels) / max(len(filtered_rels), 1)
            st.metric("Confiança média", f"{avg_confidence:.2%}")
        with col3:
            unique_tables = set()
            for rel in filtered_rels:
                unique_tables.add(rel.get('source_table'))
                unique_tables.add(rel.get('target_table'))
            st.metric("Tabelas relacionadas", len(unique_tables))
        
        # Visualização selecionada
        if view_type == "Grafo Interativo":
            self._render_interactive_graph(filtered_rels)
        elif view_type == "Tabela":
            self._render_relationship_table(filtered_rels)
        elif view_type == "Matriz":
            self._render_relationship_matrix(filtered_rels)
        else:
            self._render_sunburst_chart(filtered_rels)
        
        # Detalhes dos relacionamentos
        st.subheader("🔍 Explorar Relacionamentos")
        
        selected_table = st.selectbox(
            "Selecione uma tabela para ver detalhes:",
            sorted(list(unique_tables))
        )
        
        if selected_table:
            self._render_table_details(selected_table, filtered_rels)
    
    def _render_interactive_graph(self, relationships: List[Dict]):
        """Renderiza grafo interativo com Plotly"""
        
        # Prepara nós
        nodes = set()
        for rel in relationships:
            nodes.add(rel['source_table'])
            nodes.add(rel['target_table'])
        
        # Cria grafo Plotly
        fig = go.Figure()
        
        # Adiciona arestas
        edge_x = []
        edge_y = []
        edge_text = []
        
        for rel in relationships:
            # Aqui você implementaria a lógica para posicionar nós
            # Para simplificação, usaremos layout circular
            pass
        
        # Layout
        fig.update_layout(
            title='Grafo de Relacionamentos',
            showlegend=False,
            hovermode='closest',
            margin=dict(b=20,l=5,r=5,t=40),
            annotations=[],
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def _render_relationship_table(self, relationships: List[Dict]):
        """Renderiza tabela de relacionamentos"""
        
        df = pd.DataFrame(relationships)
        
        if not df.empty:
            # Seleciona colunas relevantes
            display_cols = ['source_table', 'target_table', 'relationship_type', 
                          'confidence', 'evidence']
            display_cols = [c for c in display_cols if c in df.columns]
            
            st.dataframe(
                df[display_cols].sort_values('confidence', ascending=False),
                use_container_width=True
            )
        else:
            st.info("Nenhum relacionamento encontrado com os critérios atuais.")
    
    def _render_table_details(self, table_name: str, relationships: List[Dict]):
        """Mostra detalhes de uma tabela específica"""
        
        # Relacionamentos onde a tabela é fonte
        outgoing = [r for r in relationships if r['source_table'] == table_name]
        
        # Relacionamentos onde a tabela é destino
        incoming = [r for r in relationships if r['target_table'] == table_name]
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🔗 Referencia (FK)")
            if outgoing:
                for rel in outgoing:
                    st.markdown(f"""
                    **→ {rel['target_table']}**  
                    Coluna: `{rel.get('relationship_column', 'N/A')}`  
                    Confiança: {rel.get('confidence', 0):.1%}  
                    Tipo: {rel.get('relationship_type', 'N/A')}
                    """)
            else:
                st.info("Nenhuma referência encontrada")
        
        with col2:
            st.subheader("📥 É Referenciada (PK)")
            if incoming:
                for rel in incoming:
                    st.markdown(f"""
                    **← {rel['source_table']}**  
                    Coluna: `{rel.get('relationship_column', 'N/A')}`  
                    Confiança: {rel.get('confidence', 0):.1%}  
                    Tipo: {rel.get('relationship_type', 'N/A')}
                    """)
            else:
                st.info("Nenhuma referência recebida")