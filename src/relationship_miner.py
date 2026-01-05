# src/relationship_miner.py
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
from typing import Dict, List, Set, Any
import re

class RelationshipMiner:
    def __init__(self, tables_info: Dict):
        """
        Inicializa o minerador com informações das tabelas
        
        Args:
            tables_info: Dicionário com informações das tabelas
                        (do ERPSchemaAnalyzer.tables_info)
        """
        self.tables_info = tables_info
        self.graph = nx.DiGraph()
        self.relationships_found = []
        
    def mine_relationships(self) -> List[Dict]:
        """Minera relacionamentos usando múltiplas estratégias"""
        
        # 1. Baseado em nomenclatura
        naming_rels = self._find_relationships_by_naming()
        
        # 2. Baseado em padrões do ERP
        pattern_rels = self._find_relationships_by_erp_patterns()
        
        # 3. Baseado em dados (valores em comum) - opcional se tiver acesso a dados
        data_rels = []  # Inicializa vazio
        
        # Combina todos
        all_relationships = naming_rels + pattern_rels + data_rels
        
        # Remove duplicatas
        unique_rels = self._deduplicate_relationships(all_relationships)
        
        # Calcula confiança
        for rel in unique_rels:
            rel['confidence'] = self._calculate_confidence(rel)
        
        self.relationships_found = unique_rels
        return unique_rels
    
    def _find_relationships_by_naming(self) -> List[Dict]:
        """Encontra relacionamentos baseados em nomes de colunas"""
        relationships = []
        
        for table_name, info in self.tables_info.items():
            columns = info.get('columns', [])
            
            for column in columns:
                col_lower = column.lower()
                
                # Verifica se coluna referencia outra tabela
                for other_table in self.tables_info:
                    if other_table == table_name:
                        continue
                    
                    other_lower = other_table.lower()
                    
                    # Padrões comuns: TabelaID, IdTabela, CodTabela, etc.
                    patterns = [
                        f"{other_lower}id",
                        f"id{other_lower}",
                        f"{other_lower}_id",
                        f"id_{other_lower}",
                        f"cod{other_lower}",
                        f"{other_lower}cod",
                    ]
                    
                    if any(pattern in col_lower for pattern in patterns):
                        relationships.append({
                            'source_table': table_name,
                            'source_column': column,
                            'target_table': other_table,
                            'relationship_type': 'foreign_key_by_name',
                            'evidence': f"Nome da coluna '{column}' referencia tabela '{other_table}'"
                        })
        
        return relationships
    
    def _find_relationships_by_erp_patterns(self) -> List[Dict]:
        """Usa padrões conhecidos de ERPs para inferir relacionamentos"""
        relationships = []
        
        # Padrões comuns em ERPs de moda/confecção
        erp_patterns = {
            # Clientes
            ('cliente', 'pedido'): {'column_pattern': 'cliente', 'confidence': 0.9},
            ('cliente', 'venda'): {'column_pattern': 'cliente', 'confidence': 0.9},
            ('cliente', 'notafiscal'): {'column_pattern': 'cliente', 'confidence': 0.8},
            
            # Produtos
            ('produto', 'pedidoitem'): {'column_pattern': 'produto', 'confidence': 0.9},
            ('produto', 'item'): {'column_pattern': 'produto', 'confidence': 0.9},
            ('produto', 'estoque'): {'column_pattern': 'produto', 'confidence': 0.8},
            
            # Fornecedores
            ('fornecedor', 'compra'): {'column_pattern': 'fornecedor', 'confidence': 0.9},
            ('fornecedor', 'notafiscalcompra'): {'column_pattern': 'fornecedor', 'confidence': 0.8},
            
            # Vendedores/Funcionários
            ('vendedor', 'venda'): {'column_pattern': 'vendedor', 'confidence': 0.8},
            ('funcionario', 'folha'): {'column_pattern': 'funcionario', 'confidence': 0.9},
            
            # Financeiro
            ('contabanco', 'lancamento'): {'column_pattern': 'conta', 'confidence': 0.8},
            ('planoconta', 'lancamento'): {'column_pattern': 'planoconta', 'confidence': 0.8},
        }
        
        # Normaliza nomes das tabelas para busca
        table_names_lower = {name.lower(): name for name in self.tables_info.keys()}
        
        for (table1_pattern, table2_pattern), pattern_info in erp_patterns.items():
            # Encontra tabelas que correspondem aos padrões
            matching_tables1 = [name for name_lower, name in table_names_lower.items() 
                              if table1_pattern in name_lower]
            matching_tables2 = [name for name_lower, name in table_names_lower.items() 
                              if table2_pattern in name_lower]
            
            # Para cada combinação de tabelas que correspondem aos padrões
            for table1 in matching_tables1:
                for table2 in matching_tables2:
                    if table1 == table2:
                        continue
                    
                    # Procura coluna que corresponda ao padrão na tabela2
                    columns2 = self.tables_info[table2].get('columns', [])
                    
                    for column in columns2:
                        col_lower = column.lower()
                        pattern_lower = pattern_info['column_pattern'].lower()
                        
                        # Verifica se coluna contém o padrão
                        if pattern_lower in col_lower:
                            relationships.append({
                                'source_table': table2,
                                'target_table': table1,
                                'relationship_column': column,
                                'relationship_type': 'erp_pattern',
                                'confidence': pattern_info['confidence'],
                                'evidence': f"Padrão ERP: {table2}.{column} -> {table1}"
                            })
        
        return relationships
    
    def _identify_key_tables(self) -> Dict:
        """Identifica tabelas-chave do ERP"""
        key_tables = {}
        
        for table_name, info in self.tables_info.items():
            score = 0
            
            # Pontua baseado em:
            # 1. Nome da tabela (tabelas mestres)
            master_keywords = ['cliente', 'produto', 'fornecedor', 'funcionario', 
                             'vendedor', 'cidade', 'estado', 'pais']
            
            if any(keyword in table_name.lower() for keyword in master_keywords):
                score += 3
            
            # 2. Tamanho (tabelas mestres geralmente têm menos registros)
            row_count = info.get('total_rows', 0)
            if 100 < row_count < 1000000:  # Faixa típica de tabelas mestres
                score += 2
            
            if score > 0:
                key_tables[table_name] = {
                    'score': score,
                    'type': 'master' if score >= 3 else 'transaction'
                }
        
        return key_tables
    
    def build_relationship_graph(self):
        """Constrói grafo de relacionamentos"""
        self.graph = nx.DiGraph()
        
        for rel in self.relationships_found:
            if rel.get('confidence', 0) > 0.3:  # Limiar mais baixo inicialmente
                self.graph.add_edge(
                    rel.get('source_table', ''),
                    rel.get('target_table', ''),
                    weight=rel.get('confidence', 0),
                    column=rel.get('relationship_column', ''),
                    type=rel.get('relationship_type', 'unknown')
                )
        
        return self.graph
    
    def visualize_relationships(self):
        """Visualiza o grafo de relacionamentos"""
        if len(self.graph.nodes()) == 0:
            print("Grafo vazio. Execute build_relationship_graph() primeiro.")
            return None
        
        plt.figure(figsize=(15, 10))
        
        # Usa layout para melhor visualização
        pos = nx.spring_layout(self.graph, k=1, iterations=50)
        
        # Desenha nós com cores baseadas no tipo de tabela
        node_colors = []
        for node in self.graph.nodes():
            if any(keyword in node.lower() for keyword in ['cliente', 'produto', 'fornecedor']):
                node_colors.append('lightgreen')  # Tabelas mestres
            elif any(keyword in node.lower() for keyword in ['pedido', 'venda', 'compra']):
                node_colors.append('lightblue')   # Tabelas transacionais
            else:
                node_colors.append('lightgray')   # Outras
        
        nx.draw_networkx_nodes(self.graph, pos, node_size=500, 
                              node_color=node_colors, alpha=0.8)
        
        # Desenha arestas
        edges = self.graph.edges(data=True)
        edge_colors = [data.get('weight', 0.5) for _, _, data in edges]
        edge_widths = [data.get('weight', 0.5) * 3 for _, _, data in edges]
        
        nx.draw_networkx_edges(
            self.graph, pos, 
            edge_color=edge_colors,
            edge_cmap=plt.cm.Blues,
            width=edge_widths,
            arrows=True,
            arrowsize=15,
            alpha=0.6
        )
        
        # Labels
        nx.draw_networkx_labels(self.graph, pos, font_size=9, font_weight='bold')
        
        plt.title("Relacionamentos Descobertos no ERP", fontsize=14)
        plt.axis('off')
        plt.tight_layout()
        
        return plt
    
    def _deduplicate_relationships(self, relationships: List[Dict]) -> List[Dict]:
        """Remove relacionamentos duplicados"""
        seen = set()
        unique = []
        
        for rel in relationships:
            key = (rel.get('source_table'), rel.get('target_table'))
            
            if key not in seen:
                seen.add(key)
                unique.append(rel)
        
        return unique
    
    def _calculate_confidence(self, relationship: Dict) -> float:
        """Calcula confiança no relacionamento"""
        confidence = 0.0
        
        # Baseado no tipo de evidência
        evidence_weights = {
            'foreign_key_by_name': 0.8,
            'erp_pattern': 0.7,
            'data_overlap': 0.6,
            'implicit': 0.4
        }
        
        rel_type = relationship.get('relationship_type', 'implicit')
        confidence += evidence_weights.get(rel_type, 0.4)
        
        # Bonus por padrões de nome na coluna
        column = relationship.get('relationship_column', '').lower()
        if any(pattern in column for pattern in ['id', 'cod', 'key', 'ref']):
            confidence += 0.15
        
        # Bonus se tabela alvo for identificada como master
        target_table = relationship.get('target_table', '')
        key_tables = self._identify_key_tables()
        if target_table in key_tables and key_tables[target_table]['type'] == 'master':
            confidence += 0.1
        
        return min(confidence, 1.0)  # Limita a 1.0
    
    def get_relationships_by_table(self, table_name: str) -> Dict:
        """Retorna relacionamentos envolvendo uma tabela específica"""
        outgoing = [r for r in self.relationships_found 
                   if r.get('source_table') == table_name]
        incoming = [r for r in self.relationships_found 
                   if r.get('target_table') == table_name]
        
        return {
            'outgoing': outgoing,
            'incoming': incoming,
            'total': len(outgoing) + len(incoming)
        }
    
    def suggest_joins(self, table1: str, table2: str) -> List[Dict]:
        """Sugere possíveis joins entre duas tabelas"""
        suggestions = []
        
        # Procura relacionamentos diretos
        for rel in self.relationships_found:
            if (rel.get('source_table') == table1 and rel.get('target_table') == table2) or \
               (rel.get('source_table') == table2 and rel.get('target_table') == table1):
                suggestions.append({
                    'type': 'direct',
                    'confidence': rel.get('confidence', 0),
                    'column': rel.get('relationship_column', ''),
                    'direction': f"{rel.get('source_table')} -> {rel.get('target_table')}"
                })
        
        # Procura tabelas intermediárias
        if not suggestions:
            # Encontra caminhos no grafo
            try:
                paths = list(nx.all_simple_paths(self.graph, table1, table2, cutoff=2))
                for path in paths:
                    if len(path) == 3:  # A -> B -> C
                        suggestions.append({
                            'type': 'indirect',
                            'path': ' -> '.join(path),
                            'confidence': 0.5,  # Confiança menor para joins indiretos
                            'suggestion': f"Junte {table1} com {path[1]}, depois com {table2}"
                        })
            except:
                pass
        
        return sorted(suggestions, key=lambda x: x.get('confidence', 0), reverse=True)