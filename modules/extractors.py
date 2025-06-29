# Arquivo: modules/extractors.py

import pandas as pd
import logging
from typing import List, Dict, Any, Tuple


class ExtractionError(Exception):
    """Exceção personalizada para erros de extração de dados"""
    pass


def validate_required_columns(df: pd.DataFrame, table_name: str, expected_columns: List[str]) -> bool:
    """
    Valida se o DataFrame contém todas as colunas esperadas.
    
    Args:
        df: DataFrame a ser validado
        table_name: Nome da tabela para mensagens de erro
        expected_columns: Lista de colunas esperadas
        
    Returns:
        bool: True se todas as colunas estiverem presentes
        
    Raises:
        ExtractionError: Se alguma coluna estiver faltando
    """
    missing_columns = [col for col in expected_columns if col not in df.columns]
    
    if missing_columns:
        error_msg = f"Colunas faltando na tabela {table_name}: {missing_columns}"
        logging.error(error_msg)
        logging.error(f"Colunas encontradas: {list(df.columns)}")
        raise ExtractionError(error_msg)
    
    logging.info(f"✅ Validação de colunas da tabela {table_name} passou")
    return True


def get_ordens(conn) -> pd.DataFrame:
    """
    Extrai dados da tabela ORDEMS usando SQL parametrizado.
    
    Args:
        conn: Conexão com banco de dados
        
    Returns:
        pd.DataFrame: Dados extraídos da tabela ORDEMS
        
    Raises:
        ExtractionError: Se houver erro na extração
    """
    try:
        # Define colunas esperadas (usando nomes reais da tabela)
        expected_columns = [
            'CODIGO', 'COD_CLIENTE', 'SAIDA', 'V_MAO', 'V_PECAS', 
            'V_DESLOCA', 'V_TERCEIRO', 'V_OUTROS', 'APARELHO', 'MODELO'
        ]
        
        # Query como string simples para compatibilidade com pyodbc
        query = """
        SELECT
            CODIGO,
            COD_CLIENTE,
            SAIDA,
            V_MAO,
            V_PECAS,
            V_DESLOCA,
            V_TERCEIRO,
            V_OUTROS,
            APARELHO,
            MODELO
        FROM ORDEMS
        """
        
        logging.info("Iniciando extração da tabela ORDEMS...")
        
        # Executa query usando pandas
        df = pd.read_sql(query, conn)
        
        # Valida colunas
        validate_required_columns(df, 'ORDEMS', expected_columns)
        
        # Log detalhado da extração
        logging.info(f"✅ Extração ORDEMS concluída: {len(df)} registros")
        logging.info(f"   Colunas extraídas: {list(df.columns)}")
        
        # Log de estatísticas básicas
        if not df.empty:
            logging.info(f"   Período: {df['SAIDA'].min()} a {df['SAIDA'].max()}")
            logging.info(f"   Valor total médio (mão de obra): {df['V_MAO'].mean():.2f}")
            logging.info(f"   Valor total médio (peças): {df['V_PECAS'].mean():.2f}")
        
        return df
        
    except Exception as e:
        error_msg = f"Erro na extração da tabela ORDEMS: {e}"
        logging.error(error_msg)
        raise ExtractionError(error_msg)


def get_contas(conn) -> pd.DataFrame:
    """
    Extrai dados da tabela CONTAS usando SQL parametrizado.
    
    Args:
        conn: Conexão com banco de dados
        
    Returns:
        pd.DataFrame: Dados extraídos da tabela CONTAS
        
    Raises:
        ExtractionError: Se houver erro na extração
    """
    try:
        # Define colunas esperadas
        expected_columns = ['CODIGO', 'REFERENCIA', 'VALOR', 'PAGO', 'DATA_PGTO', 'COD_CLIENTE', 'ECF_CARTAO', 'ECF_DINHEIRO', 'ECF_TROCO']
        
        # Query como string simples para compatibilidade com pyodbc
        query = """
        SELECT
            CODIGO,
            REFERENCIA,
            VALOR,
            PAGO,
            DATA_PGTO,
            COD_CLIENTE,
            ECF_CARTAO,
            ECF_DINHEIRO,
            ECF_TROCO
        FROM CONTAS
        """
        
        logging.info("Iniciando extração da tabela CONTAS...")
        
        # Executa query
        df = pd.read_sql(query, conn)
        
        # Valida colunas
        validate_required_columns(df, 'CONTAS', expected_columns)
        
        # Log detalhado da extração
        logging.info(f"✅ Extração CONTAS concluída: {len(df)} registros")
        logging.info(f"   Colunas extraídas: {list(df.columns)}")
        
        # Log de estatísticas básicas
        if not df.empty:
            logging.info(f"   Referências únicas: {df['REFERENCIA'].nunique()}")
            logging.info(f"   Registros pagos: {len(df[df['PAGO'] == 'S'])}")
            logging.info(f"   Registros pendentes: {len(df[df['PAGO'] == 'N'])}")
            logging.info(f"   Valor total: {df['VALOR'].sum():.2f}")
        
        return df
        
    except Exception as e:
        error_msg = f"Erro na extração da tabela CONTAS: {e}"
        logging.error(error_msg)
        raise ExtractionError(error_msg)


def get_fcaixa(conn) -> pd.DataFrame:
    """
    Extrai dados da tabela FCAIXA usando SQL parametrizado.
    
    Args:
        conn: Conexão com banco de dados
        
    Returns:
        pd.DataFrame: Dados extraídos da tabela FCAIXA
        
    Raises:
        ExtractionError: Se houver erro na extração
    """
    try:
        # Define colunas esperadas
        expected_columns = ['CODIGO', 'DIA', 'RECEITA', 'COD_CONTA', 'FORMA']
        
        # Query como string simples para compatibilidade com pyodbc
        query = """
        SELECT
            CODIGO,
            DIA,
            RECEITA,
            COD_CONTA,
            FORMA
        FROM FCAIXA
        """
        
        logging.info("Iniciando extração da tabela FCAIXA...")
        
        # Executa query
        df = pd.read_sql(query, conn)
        
        # Valida colunas
        validate_required_columns(df, 'FCAIXA', expected_columns)
        
        # Log detalhado da extração
        logging.info(f"✅ Extração FCAIXA concluída: {len(df)} registros")
        logging.info(f"   Colunas extraídas: {list(df.columns)}")
        
        # Log de estatísticas básicas
        if not df.empty:
            logging.info(f"   Período: {df['DIA'].min()} a {df['DIA'].max()}")
            logging.info(f"   Receita total: {df['RECEITA'].sum():.2f}")
            
            # Estatísticas por forma de pagamento
            formas_pgto = df['FORMA'].value_counts()
            logging.info(f"   Formas de pagamento: {dict(formas_pgto)}")
        
        return df
        
    except Exception as e:
        error_msg = f"Erro na extração da tabela FCAIXA: {e}"
        logging.error(error_msg)
        raise ExtractionError(error_msg)


def get_extraction_summary(ordens_df: pd.DataFrame, contas_df: pd.DataFrame, fcaixa_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Gera um resumo da extração de dados para auditoria.
    
    Args:
        ordens_df: DataFrame da tabela ORDEMS
        contas_df: DataFrame da tabela CONTAS
        fcaixa_df: DataFrame da tabela FCAIXA
        
    Returns:
        dict: Resumo da extração
    """
    try:
        summary = {
            'timestamp': pd.Timestamp.now(),
            'tables': {
                'ORDEMS': {
                    'records': len(ordens_df),
                    'columns': list(ordens_df.columns),
                    'date_range': {
                        'min': ordens_df['SAIDA'].min() if not ordens_df.empty else None,
                        'max': ordens_df['SAIDA'].max() if not ordens_df.empty else None
                    }
                },
                'CONTAS': {
                    'records': len(contas_df),
                    'columns': list(contas_df.columns),
                    'unique_references': contas_df['REFERENCIA'].nunique() if not contas_df.empty else 0
                },
                'FCAIXA': {
                    'records': len(fcaixa_df),
                    'columns': list(fcaixa_df.columns),
                    'unique_orders': fcaixa_df['CODIGO'].nunique() if not fcaixa_df.empty else 0
                }
            },
            'total_records': len(ordens_df) + len(contas_df) + len(fcaixa_df)
        }
        
        logging.info("📊 RESUMO DA EXTRAÇÃO:")
        logging.info(f"   Total de registros: {summary['total_records']}")
        logging.info(f"   ORDEMS: {summary['tables']['ORDEMS']['records']} registros")
        logging.info(f"   CONTAS: {summary['tables']['CONTAS']['records']} registros")
        logging.info(f"   FCAIXA: {summary['tables']['FCAIXA']['records']} registros")
        
        return summary
        
    except Exception as e:
        logging.error(f"Erro ao gerar resumo da extração: {e}")
        return {}


def extract_all_data(conn) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Extrai dados de todas as tabelas necessárias.
    
    Args:
        conn: Conexão com banco de dados
        
    Returns:
        tuple: (ordens_df, contas_df, fcaixa_df)
        
    Raises:
        ExtractionError: Se houver erro em qualquer extração
    """
    try:
        logging.info("🚀 Iniciando extração completa de dados...")
        
        # Extrai dados de todas as tabelas
        ordens_df = get_ordens(conn)
        contas_df = get_contas(conn)
        fcaixa_df = get_fcaixa(conn)
        
        # Gera resumo para auditoria
        summary = get_extraction_summary(ordens_df, contas_df, fcaixa_df)
        
        logging.info("✅ Extração completa concluída com sucesso!")
        
        return ordens_df, contas_df, fcaixa_df
        
    except Exception as e:
        error_msg = f"Erro na extração completa de dados: {e}"
        logging.error(error_msg)
        raise ExtractionError(error_msg)