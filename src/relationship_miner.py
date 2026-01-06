# src/relationship_miner.py - VERSÃO CORRIGIDA
import pandas as pd
import networkx as nx
from typing import Dict, List, Any
import re

class RelationshipMiner:
    def __init__(self, tables_info: Dict):
        """
        Minera relacionamentos entre tabelas do ERP
        
        Args:
            tables_info: Dicionário com informações das tabelas
        """
        self.tables_info = tables_info
        self.graph = nx.DiGraph()
        self.relationships_found = []
        
    def mine_relationships(self) -> List[Dict]:
        """Minera relacionamentos usando múltiplas estratégias"""
        
        # Limpa resultados anteriores
        self.relationships_found = []
        
        # 1. Baseado em nomenclatura de colunas
        naming_rels = self._find_relationships_by_naming()
        
        # 2. Baseado em padrões do ERP
        pattern_rels = self._find_relationships_by_erp_patterns()
        
        # 3. Baseado em dados comuns (se disponível)
        data_rels = self._find_relationships_by_data_sampling()
        
        # Combina todos os relacionamentos
        all_relationships = naming_rels + pattern_rels + data_rels
        
        # Remove duplicatas
        unique_rels = self._deduplicate_relationships(all_relationships)
        
        # Calcula confiança para cada relacionamento
        for rel in unique_rels:
            rel['confidence'] = self._calculate_confidence(rel)
        
        self.relationships_found = unique_rels
        return unique_rels
    
    def _find_relationships_by_naming(self) -> List[Dict]:
        """Encontra relacionamentos baseados em nomes de colunas"""
        relationships = []
        
        # Para cada tabela
        for table_name, info in self.tables_info.items():
            if 'error' in info:
                continue
                
            columns = info.get('columns', [])
            
            # Para cada coluna na tabela
            for column in columns:
                col_lower = column.lower()
                
                # Verifica se a coluna referencia outra tabela
                for other_table in self.tables_info:
                    if other_table == table_name:
                        continue
                    
                    other_lower = other_table.lower()
                    
                    # Padrões comuns de chaves estrangeiras
                    patterns = [
                        # Padrão: TabelaID (ex: ClienteID)
                        f"{other_lower}id",
                        f"{other_lower}_id",
                        f"id{other_lower}",
                        f"id_{other_lower}",
                        # Padrão: CodTabela (ex: CodCliente)
                        f"cod{other_lower}",
                        f"cod_{other_lower}",
                        f"{other_lower}cod",
                        # Padrão: TabelaCodigo (ex: ClienteCodigo)
                        f"{other_lower}codigo",
                        f"{other_lower}code",
                    ]
                    
                    # Verifica se algum padrão corresponde
                    for pattern in patterns:
                        if pattern in col_lower:
                            relationships.append({
                                'source_table': table_name,
                                'target_table': other_table,
                                'relationship_column': column,
                                'relationship_type': 'foreign_key_by_name',
                                'evidence': f"Coluna '{column}' parece referenciar '{other_table}'"
                            })
                            break
        
        return relationships
    
    def _find_relationships_by_erp_patterns(self) -> List[Dict]:
        """Usa padrões conhecidos de ERPs para inferir relacionamentos"""
        relationships = []
        
        # Padrões comuns em ERPs (especialmente moda/confecção)
        common_patterns = [
            # Clientes
            (r'.*cliente.*', r'.*pedido.*', 'cliente', 0.9),
            (r'.*cliente.*', r'.*venda.*', 'cliente', 0.9),
            (r'.*cliente.*', r'.*orcamento.*', 'cliente', 0.8),
            
            # Produtos
            (r'.*produto.*', r'.*pedido.*item.*', 'produto', 0.9),
            (r'.*produto.*', r'.*item.*', 'produto', 0.8),
            (r'.*produto.*', r'.*estoque.*', 'produto', 0.7),
            
            # Fornecedores
            (r'.*fornecedor.*', r'.*compra.*', 'fornecedor', 0.9),
            (r'.*fornecedor.*', r'.*nota.*compra.*', 'fornecedor', 0.8),
            
            # Vendedores
            (r'.*vendedor.*', r'.*venda.*', 'vendedor', 0.8),
            (r'.*funcionario.*', r'.*venda.*', 'funcionario', 0.7),
            
            # Financeiro
            (r'.*conta.*', r'.*lancamento.*', 'conta', 0.8),
            (r'.*banco.*', r'.*movimento.*', 'banco', 0.7),
            
            # Pedidos
            (r'.*pedido.*', r'.*nota.*fiscal.*', 'pedido', 0.8),
            (r'.*pedido.*', r'.*entrega.*', 'pedido', 0.7),
        ]
        
        # Para cada padrão
        for pattern1, pattern2, column_pattern, base_confidence in common_patterns:
            # Encontra tabelas que correspondem aos padrões
            matching_tables1 = [t for t in self.tables_info.keys() 
                              if re.match(pattern1, t, re.IGNORECASE)]
            matching_tables2 = [t for t in self.tables_info.keys() 
                              if re.match(pattern2, t, re.IGNORECASE)]
            
            # Para cada combinação
            for table1 in matching_tables1:
                for table2 in matching_tables2:
                    if table1 == table2:
                        continue
                    
                    # Procura coluna que corresponda ao padrão
                    cols2 = self.tables_info[table2].get('columns', [])
                    for column in cols2:
                        col_lower = column.lower()
                        
                        # Verifica padrões na coluna
                        if (column_pattern in col_lower or 
                            f"id{column_pattern}" in col_lower or
                            f"{column_pattern}id" in col_lower):
                            
                            relationships.append({
                                'source_table': table2,  # Tabela que tem a FK
                                'target_table': table1,  # Tabela referenciada
                                'relationship_column': column,
                                'relationship_type': 'erp_pattern',
                                'confidence': base_confidence,
                                'evidence': f"Padrão ERP: {table2}.{column} -> {table1}"
                            })
        
        return relationships
    
    def _find_relationships_by_data_sampling(self) -> List[Dict]:
        """Tenta encontrar relacionamentos baseados em amostra de dados"""
        relationships = []
        
        # Limita a tabelas menores para performance
        small_tables = []
        for table, info in self.tables_info.items():
            if 'error' not in info and info.get('total_rows', 0) < 10000:
                small_tables.append(table)
        
        # Limita a 20 tabelas para performance
        small_tables = small_tables[:20]
        
        # Para cada par de tabelas
        for i, table1 in enumerate(small_tables):
            for table2 in small_tables[i+1:]:
                # Procura colunas com nomes similares
                cols1 = self.tables_info[table1].get('columns', [])
                cols2 = self.tables_info[table2].get('columns', [])
                
                for col1 in cols1:
                    for col2 in cols2:
                        # Se as colunas têm nomes similares
                        if (self._columns_match(col1, col2) and 
                            self._looks_like_id_column(col1) and 
                            self._looks_like_id_column(col2)):
                            
                            relationships.append({
                                'source_table': table1,
                                'target_table': table2,
                                'relationship_column': f"{col1} ↔ {col2}",
                                'relationship_type': 'data_pattern',
                                'confidence': 0.6,
                                'evidence': f"Colunas similares: {table1}.{col1} e {table2}.{col2}"
                            })
        
        return relationships
    
    def _columns_match(self, col1: str, col2: str) -> bool:
        """Verifica se duas colunas parecem ser a mesma"""
        col1_lower = col1.lower()
        col2_lower = col2.lower()
        
        # Se são exatamente iguais (ignorando case)
        if col1_lower == col2_lower:
            return True
        
        # Remove sufixos comuns
        col1_clean = re.sub(r'_(id|cod|code|key|num|nro)$', '', col1_lower)
        col2_clean = re.sub(r'_(id|cod|code|key|num|nro)$', '', col2_lower)
        
        # Se são similares após limpeza
        if col1_clean == col2_clean:
            return True
        
        # Se uma contém a outra
        if col1_clean in col2_clean or col2_clean in col1_clean:
            return True
        
        return False
    
    def _looks_like_id_column(self, column_name: str) -> bool:
        """Verifica se uma coluna parece ser uma chave"""
        col_lower = column_name.lower()
        
        id_keywords = ['id', 'cod', 'code', 'key', 'chave', 'numero', 'num', 'nro']
        
        # Verifica se contém palavra-chave de ID
        for keyword in id_keywords:
            if keyword in col_lower:
                return True
        
        # Verifica padrões comuns
        patterns = [r'.*id$', r'.*cod$', r'.*code$', r'id.*', r'cod.*']
        for pattern in patterns:
            if re.match(pattern, col_lower):
                return True
        
        return False
    
    def _deduplicate_relationships(self, relationships: List[Dict]) -> List[Dict]:
        """Remove relacionamentos duplicados"""
        seen = set()
        unique = []
        
        for rel in relationships:
            # Cria chave única
            key = (rel.get('source_table'), rel.get('target_table'), 
                  rel.get('relationship_column', ''))
            
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
            'data_pattern': 0.6,
            'implicit': 0.4
        }
        
        rel_type = relationship.get('relationship_type', 'implicit')
        confidence += evidence_weights.get(rel_type, 0.4)
        
        # Bonus por padrões específicos na coluna
        column = relationship.get('relationship_column', '').lower()
        
        # Bonus se coluna termina com ID
        if column.endswith('id') or '_id' in column:
            confidence += 0.1
        
        # Bonus se coluna começa com ID
        if column.startswith('id') or column.startswith('cod'):
            confidence += 0.1
        
        # Bonus se tabela alvo é claramente uma tabela mestre
        target = relationship.get('target_table', '').lower()
        if any(kw in target for kw in ['cliente', 'produto', 'fornecedor', 'funcionario']):
            confidence += 0.1
        
        # Limita a 1.0
        return min(confidence, 1.0)
    
    def get_relationships_summary(self) -> Dict:
        """Retorna resumo dos relacionamentos encontrados"""
        if not self.relationships_found:
            return {"total": 0}
        
        # Agrupa por tipo
        by_type = {}
        for rel in self.relationships_found:
            rel_type = rel.get('relationship_type', 'unknown')
            by_type[rel_type] = by_type.get(rel_type, 0) + 1
        
        # Conta por confiança
        high_conf = sum(1 for r in self.relationships_found if r.get('confidence', 0) > 0.8)
        medium_conf = sum(1 for r in self.relationships_found if 0.5 <= r.get('confidence', 0) <= 0.8)
        low_conf = sum(1 for r in self.relationships_found if r.get('confidence', 0) < 0.5)
        
        return {
            "total": len(self.relationships_found),
            "by_type": by_type,
            "high_confidence": high_conf,
            "medium_confidence": medium_conf,
            "low_confidence": low_conf
        }