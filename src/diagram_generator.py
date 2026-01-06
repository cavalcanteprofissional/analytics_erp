# src/diagram_generator.py
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
from typing import Dict, List, Optional
import io
import base64
from pathlib import Path

class ERDiagramGenerator:
    """Gera diagramas ER a partir dos relacionamentos descobertos"""
    
    def __init__(self, relationships: List[Dict], tables_info: Dict):
        self.relationships = relationships
        self.tables_info = tables_info
        self.graph = nx.DiGraph()
        
    def build_graph(self, min_confidence: float = 0.5):
        """Constrói grafo de relacionamentos"""
        self.graph.clear()
        
        # Adiciona nós (tabelas)
        for table_name in self.tables_info.keys():
            self.graph.add_node(table_name, 
                               size=self.tables_info[table_name].get('total_rows', 0))
        
        # Adiciona arestas (relacionamentos)
        for rel in self.relationships:
            if rel.get('confidence', 0) >= min_confidence:
                self.graph.add_edge(
                    rel.get('source_table'),
                    rel.get('target_table'),
                    label=rel.get('relationship_column', ''),
                    confidence=rel.get('confidence', 0),
                    type=rel.get('relationship_type', '')
                )
        
        return self.graph
    
    def generate_mermaid_er_diagram(self, max_tables: int = 20) -> str:
        """Gera código Mermaid.js para diagrama ER"""
        
        # Filtra tabelas principais
        tables = self._get_main_tables(max_tables)
        
        mermaid_code = "erDiagram\n"
        
        # Define tabelas e colunas
        for table in tables:
            info = self.tables_info.get(table, {})
            columns = info.get('columns', [])[:5]  # Limita a 5 colunas por tabela
            
            # Adiciona tabela
            mermaid_code += f"    {table} {{\n"
            
            # Adiciona colunas principais
            for col in columns[:3]:  # Primeiras 3 colunas
                col_type = info.get('dtypes', {}).get(col, 'string')
                mermaid_code += f"        {self._map_dtype_to_mermaid(col_type)} {col}\n"
            
            mermaid_code += "    }\n"
        
        # Adiciona relacionamentos
        added_rels = set()
        for rel in self.relationships:
            if rel.get('confidence', 0) > 0.6:
                source = rel.get('source_table')
                target = rel.get('target_table')
                
                if source in tables and target in tables:
                    rel_key = (source, target)
                    if rel_key not in added_rels:
                        rel_type = self._determine_mermaid_relation(rel)
                        mermaid_code += f"    {source} {rel_type} {target} : \"{rel.get('relationship_column', '')}\"\n"
                        added_rels.add(rel_key)
        
        return mermaid_code
    
    def _get_main_tables(self, max_tables: int) -> List[str]:
        """Seleciona tabelas principais para o diagrama"""
        # Ordena por importância (tamanho, nome, etc.)
        scored_tables = []
        
        for table, info in self.tables_info.items():
            score = 0
            
            # Pontua por tamanho
            rows = info.get('total_rows', 0)
            if rows > 0:
                score += min(rows / 1000, 10)  # Normaliza
            
            # Pontua por ser tabela mestre
            if any(keyword in table.lower() for keyword in 
                  ['cliente', 'produto', 'fornecedor', 'funcionario', 'cidade']):
                score += 5
            
            # Pontua por número de colunas
            score += len(info.get('columns', [])) / 10
            
            scored_tables.append((table, score))
        
        # Ordena e pega top N
        scored_tables.sort(key=lambda x: x[1], reverse=True)
        return [table for table, _ in scored_tables[:max_tables]]
    
    def _map_dtype_to_mermaid(self, dtype: str) -> str:
        """Mapeia tipo pandas para tipo Mermaid"""
        dtype_str = str(dtype).lower()
        
        if 'int' in dtype_str or 'float' in dtype_str:
            return 'INT'
        elif 'date' in dtype_str or 'time' in dtype_str:
            return 'DATETIME'
        elif 'bool' in dtype_str:
            return 'BOOLEAN'
        else:
            return 'VARCHAR(255)'
    
    def _determine_mermaid_relation(self, rel: Dict) -> str:
        """Determina tipo de relacionamento para Mermaid"""
        rel_type = rel.get('relationship_type', '')
        
        if 'foreign_key' in rel_type:
            return '|o--o{'
        elif 'many' in rel_type.lower():
            return '}o--o{'
        else:
            return '||--o{'  # One-to-many padrão
    
    def generate_graphviz_dot(self) -> str:
        """Gera código DOT para Graphviz"""
        dot_code = 'digraph ER_Diagram {\n'
        dot_code += '    rankdir=LR;\n'
        dot_code += '    node [shape=record, style=filled, fillcolor=lightblue];\n'
        dot_code += '    edge [fontsize=10];\n\n'
        
        # Adiciona tabelas como nós
        for table, info in self.tables_info.items():
            columns = info.get('columns', [])[:5]
            col_str = '\\n'.join([f'{col}' for col in columns[:3]])
            
            dot_code += f'    "{table}" [label="{{{table}|{col_str}}}"];\n'
        
        dot_code += '\n'
        
        # Adiciona relacionamentos
        for rel in self.relationships:
            if rel.get('confidence', 0) > 0.5:
                source = rel.get('source_table')
                target = rel.get('target_table')
                col = rel.get('relationship_column', '')
                conf = rel.get('confidence', 0)
                
                if source in self.tables_info and target in self.tables_info:
                    # Define cor baseada na confiança
                    color = self._confidence_to_color(conf)
                    dot_code += f'    "{source}" -> "{target}" '
                    dot_code += f'[label="{col}", color="{color}", fontcolor="{color}"];\n'
        
        dot_code += '}\n'
        return dot_code
    
    def _confidence_to_color(self, confidence: float) -> str:
        """Converte confiança para cor"""
        if confidence > 0.8:
            return "darkgreen"
        elif confidence > 0.6:
            return "orange"
        else:
            return "red"
    
    def save_diagram_files(self, output_dir: str = "diagrams"):
        """Salva vários formatos de diagrama"""
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        # Salva Mermaid
        mermaid_code = self.generate_mermaid_er_diagram()
        mermaid_file = output_path / "er_diagram.mmd"
        mermaid_file.write_text(mermaid_code, encoding='utf-8')
        
        # Salva Graphviz DOT
        dot_code = self.generate_graphviz_dot()
        dot_file = output_path / "er_diagram.dot"
        dot_file.write_text(dot_code, encoding='utf-8')
        
        # Tenta gerar imagem se Graphviz estiver instalado
        try:
            import graphviz
            dot = graphviz.Source(dot_code)
            dot.render(output_path / "er_diagram", format='png', cleanup=True)
            dot.render(output_path / "er_diagram", format='svg', cleanup=True)
        except:
            pass
        
        return {
            'mermaid': str(mermaid_file),
            'dot': str(dot_file),
            'png': str(output_path / "er_diagram.png") if (output_path / "er_diagram.png").exists() else None
        }