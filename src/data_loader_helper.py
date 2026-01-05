# src/data_loader_helper.py
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
import re

class DataHelper:
    """Funções auxiliares para processamento de dados do ERP"""
    
    @staticmethod
    def clean_table_name(table_name: str) -> str:
        """Limpa o nome da tabela removendo prefixos"""
        # Remove prefixos comuns
        prefixes = ['dbo.', 'tbl_', 'tb_', 't_']
        for prefix in prefixes:
            if table_name.startswith(prefix):
                table_name = table_name[len(prefix):]
        return table_name
    
    @staticmethod
    def clean_column_name(column_name: str) -> str:
        """Limpa nome da coluna para uso em análise"""
        # Substitui caracteres especiais
        column_name = re.sub(r'[^\w]', '_', column_name)
        column_name = column_name.strip('_').lower()
        return column_name
    
    @staticmethod
    def detect_column_semantic_type(column_name: str, sample_data: pd.Series) -> str:
        """Detecta o tipo semântico de uma coluna"""
        col_name_lower = column_name.lower()
        
        # Padrões de IDs
        id_patterns = ['id', 'cod', 'code', 'key', 'numero', 'num', 'nro', 'chave']
        if any(pattern in col_name_lower for pattern in id_patterns):
            return 'id'
        
        # Padrões de data
        date_patterns = ['data', 'date', 'dt_', 'hora', 'time', 'periodo']
        if any(pattern in col_name_lower for pattern in date_patterns):
            return 'date'
        
        # Padrões monetários
        money_patterns = ['valor', 'preco', 'custo', 'total', 'vlr', 'venda', 'compra', 
                         'desconto', 'acrescimo', 'lucro', 'prejuizo']
        if any(pattern in col_name_lower for pattern in money_patterns):
            return 'currency'
        
        # Padrões de quantidade
        qty_patterns = ['quantidade', 'qtd', 'qtde', 'estoque', 'saldo', 'peso', 
                       'volume', 'medida']
        if any(pattern in col_name_lower for pattern in qty_patterns):
            return 'quantity'
        
        # Verifica conteúdo dos dados
        if len(sample_data) > 0:
            # Verifica se parece ser booleano
            unique_vals = sample_data.dropna().unique()
            if len(unique_vals) <= 3:
                if set(str(v).lower() for v in unique_vals).issubset(
                    {'0', '1', 'true', 'false', 'sim', 'não', 'yes', 'no'}):
                    return 'boolean'
            
            # Verifica se parece ser categórico
            if len(unique_vals) < 20:
                return 'categorical'
            
            # Verifica se parece ser numérico
            try:
                numeric_sample = pd.to_numeric(sample_data.dropna(), errors='coerce')
                if numeric_sample.notna().sum() > len(sample_data) * 0.7:  # 70% numérico
                    return 'numeric'
            except:
                pass
        
        return 'text'
    
    @staticmethod
    def find_potential_primary_keys(df: pd.DataFrame, max_candidates: int = 3) -> List[str]:
        """Encontra possíveis chaves primárias em uma tabela"""
        candidates = []
        
        for column in df.columns:
            # Verifica se a coluna tem valores únicos
            unique_count = df[column].nunique()
            null_count = df[column].isnull().sum()
            
            if unique_count == len(df) and null_count == 0:
                # Coluna com todos valores únicos e sem nulos - PK perfeita
                candidates.append({
                    'column': column,
                    'score': 1.0,
                    'reason': 'Valores únicos completos'
                })
            elif unique_count / len(df) > 0.9 and null_count == 0:
                # Alta unicidade - possível PK
                score = unique_count / len(df)
                candidates.append({
                    'column': column,
                    'score': score,
                    'reason': f'Alta unicidade ({score:.1%})'
                })
            elif 'id' in column.lower() or 'cod' in column.lower():
                # Nome sugere ser ID
                score = 0.5 + (unique_count / len(df) * 0.5)
                candidates.append({
                    'column': column,
                    'score': score,
                    'reason': f'Nome sugere ID com {unique_count/len(df):.1%} unicidade'
                })
        
        # Ordena por score e retorna top N
        candidates.sort(key=lambda x: x['score'], reverse=True)
        return [c['column'] for c in candidates[:max_candidates]]
    
    @staticmethod
    def suggest_data_types(df: pd.DataFrame) -> Dict[str, str]:
        """Sugere tipos de dados otimizados para cada coluna"""
        suggestions = {}
        
        for column in df.columns:
            col_data = df[column].dropna()
            
            if len(col_data) == 0:
                suggestions[column] = 'object'
                continue
            
            # Tenta detectar tipo
            try:
                # Tenta numérico
                numeric_data = pd.to_numeric(col_data, errors='coerce')
                if numeric_data.notna().sum() / len(col_data) > 0.9:  # 90% numérico
                    # Verifica se é inteiro
                    if all(numeric_data.dropna() == numeric_data.dropna().astype(int)):
                        # Verifica faixa para otimização
                        min_val = numeric_data.min()
                        max_val = numeric_data.max()
                        
                        if min_val >= 0:
                            if max_val < 256:
                                suggestions[column] = 'uint8'
                            elif max_val < 65536:
                                suggestions[column] = 'uint16'
                            elif max_val < 4294967296:
                                suggestions[column] = 'uint32'
                            else:
                                suggestions[column] = 'uint64'
                        else:
                            if min_val >= -128 and max_val < 128:
                                suggestions[column] = 'int8'
                            elif min_val >= -32768 and max_val < 32768:
                                suggestions[column] = 'int16'
                            elif min_val >= -2147483648 and max_val < 2147483648:
                                suggestions[column] = 'int32'
                            else:
                                suggestions[column] = 'int64'
                    else:
                        suggestions[column] = 'float64'
                    continue
            except:
                pass
            
            # Tenta datetime
            try:
                datetime_data = pd.to_datetime(col_data, errors='coerce')
                if datetime_data.notna().sum() / len(col_data) > 0.7:  # 70% datas
                    suggestions[column] = 'datetime64[ns]'
                    continue
            except:
                pass
            
            # Tenta booleano
            unique_vals = col_data.unique()
            if len(unique_vals) <= 3:
                str_vals = set(str(v).lower() for v in unique_vals)
                if str_vals.issubset({'0', '1', 'true', 'false', 'sim', 'não', 'yes', 'no'}):
                    suggestions[column] = 'bool'
                    continue
            
            # Categórico para poucos valores únicos
            if len(unique_vals) < 50 and len(col_data) > 100:
                suggestions[column] = 'category'
                continue
            
            # Padrão como string
            suggestions[column] = 'object'
        
        return suggestions
    
    @staticmethod
    def optimize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
        """Otimiza DataFrame reduzindo uso de memória"""
        df_opt = df.copy()
        
        for column in df_opt.columns:
            col_type = df_opt[column].dtype
            
            # Otimiza numéricos
            if col_type in ['int64', 'float64']:
                col_min = df_opt[column].min()
                col_max = df_opt[column].max()
                
                if 'int' in str(col_type):
                    if col_min >= 0:
                        if col_max < 256:
                            df_opt[column] = df_opt[column].astype('uint8')
                        elif col_max < 65536:
                            df_opt[column] = df_opt[column].astype('uint16')
                        elif col_max < 4294967296:
                            df_opt[column] = df_opt[column].astype('uint32')
                    else:
                        if col_min >= -128 and col_max < 128:
                            df_opt[column] = df_opt[column].astype('int8')
                        elif col_min >= -32768 and col_max < 32768:
                            df_opt[column] = df_opt[column].astype('int16')
                else:  # float
                    # Tenta converter para float32 se precisão permitir
                    df_opt[column] = df_opt[column].astype('float32')
            
            # Converte para categórico se apropriado
            elif col_type == 'object':
                unique_ratio = df_opt[column].nunique() / len(df_opt)
                if unique_ratio < 0.5:  # Menos de 50% valores únicos
                    df_opt[column] = df_opt[column].astype('category')
        
        return df_opt
    
    @staticmethod
    def find_common_columns(tables_info: Dict[str, Dict]) -> Dict[str, List[str]]:
        """Encontra colunas comuns entre múltiplas tabelas"""
        column_occurrences = {}
        
        # Conta ocorrências de cada coluna
        for table_name, info in tables_info.items():
            columns = info.get('columns', [])
            for column in columns:
                col_clean = DataHelper.clean_column_name(column)
                if col_clean not in column_occurrences:
                    column_occurrences[col_clean] = []
                column_occurrences[col_clean].append(table_name)
        
        # Filtra colunas que aparecem em múltiplas tabelas
        common_columns = {}
        for column, tables in column_occurrences.items():
            if len(tables) > 1:
                common_columns[column] = {
                    'tables': tables,
                    'count': len(tables),
                    'is_id_like': any(x in column for x in ['id', 'cod', 'key'])
                }
        
        # Ordena por frequência
        sorted_common = dict(sorted(
            common_columns.items(), 
            key=lambda x: (x[1]['count'], x[1]['is_id_like']), 
            reverse=True
        ))
        
        return sorted_common