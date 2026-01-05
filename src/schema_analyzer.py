# src/schema_analyzer.py
import pandas as pd
import json
import os
from pathlib import Path
from typing import Dict, List, Any
import streamlit as st

class ERPSchemaAnalyzer:
    def __init__(self, csv_folder: str, metadata_file: str = None):
        self.csv_folder = Path(csv_folder)
        self.metadata_file = Path(metadata_file) if metadata_file else None
        self.metadata = self.load_metadata() if metadata_file else {}
        self.tables_info = {}
        
    def load_metadata(self) -> Dict:
        """Carrega o arquivo JSON de metadados"""
        if self.metadata_file and self.metadata_file.exists():
            with open(self.metadata_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def analyze_all_tables(self, sample_size: int = 1000, max_tables: int = 50) -> Dict:
        """Analisa todos os CSVs para extrair schema"""
        csv_files = list(self.csv_folder.glob("*.csv"))
        
        if not csv_files:
            st.error(f"Nenhum arquivo CSV encontrado em {self.csv_folder}")
            return {}
        
        if max_tables:
            csv_files = csv_files[:max_tables]
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for idx, csv_file in enumerate(csv_files):
            status_text.text(f"Analisando {csv_file.name} ({idx+1}/{len(csv_files)})...")
            
            try:
                # Usa amostra para performance
                df = pd.read_csv(csv_file, nrows=sample_size, low_memory=False)
                
                table_name = csv_file.stem
                
                self.tables_info[table_name] = {
                    'file_path': str(csv_file),
                    'total_rows': self.count_rows(csv_file),
                    'columns': list(df.columns),
                    'dtypes': df.dtypes.astype(str).to_dict(),
                    'sample_size': len(df),
                    'null_percentage': (df.isnull().sum() / len(df) * 100).to_dict(),
                    'unique_values': {col: df[col].nunique() for col in df.columns}
                }
                
                progress_bar.progress((idx + 1) / len(csv_files))
                
            except Exception as e:
                st.warning(f"Erro ao analisar {csv_file.name}: {str(e)}")
                self.tables_info[csv_file.stem] = {
                    'file_path': str(csv_file),
                    'error': str(e)
                }
        
        status_text.text("Análise concluída!")
        return self.tables_info
    
    def count_rows(self, csv_file: Path) -> int:
        """Conta linhas de forma eficiente"""
        try:
            # Método rápido para contar linhas
            with open(csv_file, 'r', encoding='utf-8', errors='ignore') as f:
                # Pula BOM se existir
                bom = f.read(3)
                if bom != '\xef\xbb\xbf':
                    f.seek(0)
                
                # Conta linhas (mais rápido que enumerate)
                count = 0
                buffer = f.read(8192)
                while buffer:
                    count += buffer.count('\n')
                    buffer = f.read(8192)
                
                return count - 1 if count > 0 else 0  # Subtrai header
        except Exception as e:
            return -1
    
    def get_table_info(self, table_name: str) -> Dict:
        """Obtém informações de uma tabela específica"""
        return self.tables_info.get(table_name, {})
    
    def get_tables_by_keyword(self, keyword: str) -> List[str]:
        """Retorna tabelas que contém keyword no nome"""
        keyword_lower = keyword.lower()
        return [name for name in self.tables_info.keys() 
                if keyword_lower in name.lower()]
    
    def categorize_tables(self) -> Dict[str, List[str]]:
        """Categoriza tabelas por domínio"""
        categories = {
            'clientes': ['cliente', 'clientes'],
            'produtos': ['produto', 'produtos', 'item', 'prod'],
            'vendas': ['venda', 'pedido', 'orcamento'],
            'financeiro': ['financeiro', 'conta', 'pagamento', 'recebimento', 'titulo'],
            'estoque': ['estoque', 'inventario', 'almox', 'deposito'],
            'compras': ['compra', 'fornecedor', 'cotacao'],
            'producao': ['producao', 'of', 'ordem', 'faccao'],
            'pessoal': ['funcionario', 'folha', 'rh', 'colaborador'],
            'notas_fiscais': ['nota', 'nfe', 'nfisc', 'fiscal'],
            'relatorios': ['rpt', 'relatorio', 'report']
        }
        
        result = {category: [] for category in categories.keys()}
        result['outros'] = []
        
        for table_name in self.tables_info.keys():
            table_lower = table_name.lower()
            categorized = False
            
            for category, keywords in categories.items():
                if any(keyword in table_lower for keyword in keywords):
                    result[category].append(table_name)
                    categorized = True
                    break
            
            if not categorized:
                result['outros'].append(table_name)
        
        return result