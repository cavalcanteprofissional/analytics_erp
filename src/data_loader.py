# src/data_loader.py
import pandas as pd
import numpy as np
import dask.dataframe as dd
import pyarrow as pa
import pyarrow.parquet as pq
import os
import gc
from pathlib import Path
from typing import Dict, List, Optional, Union, Tuple
import pickle
import json
from datetime import datetime
import streamlit as st
import warnings
warnings.filterwarnings('ignore')

class ERPDataLoader:
    """Carregador otimizado para grandes volumes de dados do ERP"""
    
    def __init__(self, data_dir: str = "data/raw"):
        self.data_dir = Path(data_dir)
        self.cache_dir = Path("data/processed/cache")
        self.metadata_dir = Path("data/metadata")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Cache de DataFrames carregados
        self._data_cache = {}
        self._metadata_cache = {}
        
        # Configurações de performance
        self.chunk_size = 100000  # Para leitura em chunks
        self.sample_size = 10000  # Para amostras rápidas
        
        # Estatísticas
        self.stats = {
            'total_files': 0,
            'total_records': 0,
            'loaded_tables': {},
            'cache_hits': 0,
            'cache_misses': 0
        }
    
    def scan_data_directory(self) -> Dict:
        """Escaneia o diretório de dados e coleta metadados"""
        csv_files = list(self.data_dir.glob("*.csv"))
        self.stats['total_files'] = len(csv_files)
        
        file_info = {}
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for idx, csv_file in enumerate(csv_files):
            status_text.text(f"Escaneando {csv_file.name}...")
            
            try:
                # Método rápido para obter informações básicas
                file_size = csv_file.stat().st_size / (1024 * 1024)  # MB
                
                # Conta linhas de forma eficiente (sem carregar dados)
                row_count = self._count_csv_rows_fast(csv_file)
                
                file_info[csv_file.stem] = {
                    'file_path': str(csv_file),
                    'file_size_mb': round(file_size, 2),
                    'row_count': row_count,
                    'columns': self._get_csv_columns(csv_file),
                    'last_modified': datetime.fromtimestamp(csv_file.stat().st_mtime)
                }
                
                self.stats['total_records'] += row_count
                
            except Exception as e:
                file_info[csv_file.stem] = {
                    'file_path': str(csv_file),
                    'error': str(e)
                }
            
            progress_bar.progress((idx + 1) / len(csv_files))
        
        status_text.text("Escaneamento concluído!")
        
        # Salva metadados em cache
        self._save_metadata('file_info', file_info)
        
        return file_info
    
    def _count_csv_rows_fast(self, csv_path: Path) -> int:
        """Conta linhas de CSV de forma extremamente eficiente"""
        try:
            # Usa wc command no Linux/Mac (muito rápido)
            import subprocess
            result = subprocess.run(['wc', '-l', str(csv_path)], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                count = int(result.stdout.split()[0]) - 1  # Subtrai header
                return max(count, 0)
        except:
            pass
        
        # Fallback: conta em Python (mais lento)
        count = 0
        with open(csv_path, 'r', encoding='utf-8', errors='ignore') as f:
            # Pula BOM se existir
            bom = f.read(3)
            if bom != '\xef\xbb\xbf':
                f.seek(0)
            
            # Conta linhas
            for line in f:
                count += 1
        
        return count - 1  # Subtrai header
    
    def _get_csv_columns(self, csv_path: Path, nrows: int = 10) -> List[str]:
        """Obtém colunas de CSV de forma eficiente"""
        try:
            # Lê apenas o header
            df_sample = pd.read_csv(csv_path, nrows=nrows, low_memory=False)
            return list(df_sample.columns)
        except:
            # Fallback: lê primeira linha
            with open(csv_path, 'r', encoding='utf-8', errors='ignore') as f:
                header = f.readline().strip()
                return header.split(',')
    
    def load_table(self, table_name: str, 
                   use_cache: bool = True,
                   sample_only: bool = False,
                   sample_size: Optional[int] = None,
                   columns: Optional[List[str]] = None,
                   filters: Optional[Dict] = None) -> pd.DataFrame:
        """Carrega uma tabela com caching e otimizações"""
        
        cache_key = self._generate_cache_key(table_name, sample_only, sample_size, columns, filters)
        
        # Verifica cache
        if use_cache and cache_key in self._data_cache:
            self.stats['cache_hits'] += 1
            return self._data_cache[cache_key].copy()
        
        self.stats['cache_misses'] += 1
        file_info = self.get_file_info().get(table_name)
        
        if not file_info or 'error' in file_info:
            raise ValueError(f"Tabela {table_name} não encontrada ou com erro")
        
        file_path = file_info['file_path']
        
        # Se for tabela muito grande e sample_only=True, usa amostra
        if sample_only or (file_info['row_count'] > 1000000 and sample_size):
            df = self._load_sample(file_path, sample_size or self.sample_size, columns)
        else:
            df = self._load_full_table(file_path, columns, filters)
        
        # Aplica filtros se especificados
        if filters:
            df = self._apply_filters(df, filters)
        
        # Cache
        if use_cache:
            self._data_cache[cache_key] = df.copy()
        
        # Atualiza estatísticas
        self.stats['loaded_tables'][table_name] = {
            'rows_loaded': len(df),
            'columns_loaded': len(df.columns),
            'timestamp': datetime.now()
        }
        
        return df
    
    def _load_sample(self, file_path: str, sample_size: int, columns: List[str] = None) -> pd.DataFrame:
        """Carrega amostra representativa de tabela grande"""
        
        # Para amostras muito grandes, usa método mais eficiente
        if sample_size > 100000:
            # Lê em chunks e amostra
            chunks = []
            total_rows = self._count_csv_rows_fast(Path(file_path))
            chunk_reader = pd.read_csv(file_path, 
                                     chunksize=self.chunk_size,
                                     usecols=columns,
                                     low_memory=False)
            
            for chunk in chunk_reader:
                # Amostra proporcional do chunk
                if len(chunk) > 0:
                    chunk_sample = chunk.sample(
                        n=min(sample_size // 10, len(chunk)),
                        random_state=42
                    )
                    chunks.append(chunk_sample)
                
                if len(pd.concat(chunks, ignore_index=True)) >= sample_size:
                    break
            
            df = pd.concat(chunks, ignore_index=True).head(sample_size)
        
        else:
            # Para amostras menores, lê tudo e sampleia
            try:
                df = pd.read_csv(file_path, 
                               usecols=columns,
                               low_memory=False,
                               nrows=sample_size * 3)  # Lê mais para ter boa amostra
                
                if len(df) > sample_size:
                    df = df.sample(n=sample_size, random_state=42)
            
            except MemoryError:
                # Fallback: leitura em chunks
                df = pd.read_csv(file_path,
                               usecols=columns,
                               low_memory=False,
                               nrows=sample_size)
        
        return df
    
    def _load_full_table(self, file_path: str, 
                        columns: List[str] = None,
                        filters: Dict = None) -> pd.DataFrame:
        """Carrega tabela completa com otimizações"""
        
        # Primeiro verifica se existe versão Parquet (mais rápida)
        parquet_path = self._get_parquet_path(file_path)
        
        if parquet_path.exists():
            # Carrega de Parquet (muito mais rápido)
            return self._load_parquet(parquet_path, columns, filters)
        
        # Se não tem Parquet, converte e salva para uso futuro
        return self._load_and_convert_to_parquet(file_path, columns, filters)
    
    def _load_and_convert_to_parquet(self, csv_path: str, 
                                   columns: List[str] = None,
                                   filters: Dict = None) -> pd.DataFrame:
        """Carrega CSV e converte para Parquet para futuras leituras rápidas"""
        
        st.info(f"Convertendo {Path(csv_path).name} para Parquet (será mais rápido na próxima vez)...")
        
        # Lê CSV em chunks
        chunks = []
        chunk_reader = pd.read_csv(csv_path, 
                                 chunksize=self.chunk_size,
                                 usecols=columns,
                                 low_memory=False)
        
        for chunk in chunk_reader:
            if filters:
                chunk = self._apply_filters(chunk, filters)
            chunks.append(chunk)
        
        df = pd.concat(chunks, ignore_index=True)
        
        # Salva como Parquet
        parquet_path = self._get_parquet_path(csv_path)
        df.to_parquet(parquet_path, index=False, compression='snappy')
        
        # Salva metadados do schema
        self._save_schema_metadata(csv_path, df)
        
        return df
    
    def _load_parquet(self, parquet_path: Path, 
                     columns: List[str] = None,
                     filters: Dict = None) -> pd.DataFrame:
        """Carrega dados de arquivo Parquet"""
        
        # Lê apenas colunas necessárias
        df = pd.read_parquet(parquet_path, columns=columns)
        
        if filters:
            df = self._apply_filters(df, filters)
        
        return df
    
    def _apply_filters(self, df: pd.DataFrame, filters: Dict) -> pd.DataFrame:
        """Aplica filtros ao DataFrame"""
        for column, condition in filters.items():
            if column in df.columns:
                if isinstance(condition, tuple):
                    # Range filter: (min, max)
                    if len(condition) == 2:
                        df = df[(df[column] >= condition[0]) & 
                               (df[column] <= condition[1])]
                elif isinstance(condition, list):
                    # In filter: [value1, value2, ...]
                    df = df[df[column].isin(condition)]
                else:
                    # Equality filter
                    df = df[df[column] == condition]
        
        return df
    
    def _get_parquet_path(self, csv_path: str) -> Path:
        """Gera caminho para arquivo Parquet correspondente"""
        csv_name = Path(csv_path).stem
        return self.cache_dir / f"{csv_name}.parquet"
    
    def _generate_cache_key(self, table_name: str, sample_only: bool,
                          sample_size: Optional[int], 
                          columns: Optional[List[str]],
                          filters: Optional[Dict]) -> str:
        """Gera chave única para cache"""
        key_parts = [
            table_name,
            'sample' if sample_only else 'full',
            str(sample_size) if sample_size else 'nosample',
            ','.join(sorted(columns)) if columns else 'allcols',
            str(sorted(filters.items())) if filters else 'nofilters'
        ]
        return '_'.join(key_parts)
    
    def get_file_info(self) -> Dict:
        """Obtém informações dos arquivos (com cache)"""
        if 'file_info' in self._metadata_cache:
            return self._metadata_cache['file_info']
        
        cache_file = self.metadata_dir / 'file_info.pkl'
        if cache_file.exists():
            with open(cache_file, 'rb') as f:
                file_info = pickle.load(f)
                self._metadata_cache['file_info'] = file_info
                return file_info
        
        # Se não tem cache, escaneia
        return self.scan_data_directory()
    
    def _save_metadata(self, key: str, data: Dict):
        """Salva metadados em cache"""
        self._metadata_cache[key] = data
        cache_file = self.metadata_dir / f'{key}.pkl'
        
        with open(cache_file, 'wb') as f:
            pickle.dump(data, f)
    
    def _save_schema_metadata(self, csv_path: str, df: pd.DataFrame):
        """Salva metadados do schema para análise posterior"""
        schema_info = {
            'table_name': Path(csv_path).stem,
            'columns': list(df.columns),
            'dtypes': df.dtypes.astype(str).to_dict(),
            'row_count': len(df),
            'null_counts': df.isnull().sum().to_dict(),
            'unique_counts': {col: df[col].nunique() for col in df.columns},
            'memory_usage_mb': df.memory_usage(deep=True).sum() / (1024 * 1024)
        }
        
        schema_file = self.metadata_dir / f"{Path(csv_path).stem}_schema.json"
        with open(schema_file, 'w', encoding='utf-8') as f:
            json.dump(schema_info, f, indent=2, ensure_ascii=False, default=str)
    
    def get_table_schema(self, table_name: str) -> Dict:
        """Obtém schema detalhado de uma tabela"""
        schema_file = self.metadata_dir / f"{table_name}_schema.json"
        
        if schema_file.exists():
            with open(schema_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        # Se não tem schema salvo, carrega amostra e analisa
        df = self.load_table(table_name, sample_only=True, sample_size=1000)
        
        schema_info = {
            'table_name': table_name,
            'columns': list(df.columns),
            'dtypes': df.dtypes.astype(str).to_dict(),
            'sample_data': df.head(5).to_dict('records'),
            'null_percentage': (df.isnull().sum() / len(df) * 100).to_dict(),
            'unique_values': {col: df[col].nunique() for col in df.columns}
        }
        
        # Salva para uso futuro
        with open(schema_file, 'w', encoding='utf-8') as f:
            json.dump(schema_info, f, indent=2, ensure_ascii=False, default=str)
        
        return schema_info
    
    def get_tables_by_pattern(self, pattern: str) -> List[str]:
        """Retorna tabelas que correspondem ao padrão"""
        file_info = self.get_file_info()
        return [name for name in file_info.keys() if pattern.lower() in name.lower()]
    
    def get_tables_by_size(self, min_rows: int = 0, max_rows: int = None) -> List[str]:
        """Retorna tabelas filtradas por tamanho"""
        file_info = self.get_file_info()
        filtered = []
        
        for name, info in file_info.items():
            if 'row_count' in info and isinstance(info['row_count'], int):
                if info['row_count'] >= min_rows:
                    if max_rows is None or info['row_count'] <= max_rows:
                        filtered.append(name)
        
        return sorted(filtered, key=lambda x: file_info[x]['row_count'], reverse=True)
    
    def clear_cache(self, table_name: str = None):
        """Limpa cache de dados"""
        if table_name:
            # Remove apenas cache da tabela específica
            keys_to_remove = [k for k in self._data_cache.keys() 
                            if k.startswith(table_name)]
            for key in keys_to_remove:
                del self._data_cache[key]
        else:
            # Remove todo o cache
            self._data_cache.clear()
        
        gc.collect()
        st.success("Cache limpo!")
    
    def get_stats(self) -> Dict:
        """Retorna estatísticas de carregamento"""
        return self.stats
    
    def preload_frequent_tables(self, table_names: List[str]):
        """Pré-carrega tabelas frequentes em background"""
        import threading
        
        def preload_task():
            for table_name in table_names:
                try:
                    # Carrega amostra para cache
                    self.load_table(table_name, sample_only=True, sample_size=10000)
                except:
                    pass
        
        # Executa em thread separada
        thread = threading.Thread(target=preload_task, daemon=True)
        thread.start()