# Arquivo: modules/access_db.py

import pyodbc
import logging
from typing import Optional
from contextlib import contextmanager


class DatabaseConnectionError(Exception):
    """Exceção personalizada para erros de conexão com banco de dados"""
    pass


def get_connection(mdb_file: str, password: str):
    """
    Conecta ao .mdb/.accdb usando ODBC.
    
    Args:
        mdb_file: Caminho para o arquivo .mdb/.accdb
        password: Senha do banco de dados
        
    Returns:
        pyodbc.Connection: Conexão com o banco de dados
        
    Raises:
        DatabaseConnectionError: Se houver erro na conexão
    """
    try:
        conn_str = (
            r"DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};"
            rf"DBQ={mdb_file};"
            rf"PWD={password};"
        )
        
        logging.info(f"Tentando conectar ao banco: {mdb_file}")
        connection = pyodbc.connect(conn_str)
        logging.info("Conexão estabelecida com sucesso")
        
        return connection
        
    except pyodbc.Error as e:
        error_msg = str(e)
        logging.error(f"Erro pyodbc na conexão: {error_msg}")
        
        # Identifica tipos específicos de erro
        if "authentication" in error_msg.lower() or "password" in error_msg.lower():
            raise DatabaseConnectionError(
                f"Erro de autenticação: Senha incorreta ou usuário não autorizado. "
                f"Detalhes: {error_msg}"
            )
        elif "driver" in error_msg.lower() or "microsoft access driver" in error_msg.lower():
            raise DatabaseConnectionError(
                f"Driver ODBC não encontrado: Microsoft Access Driver (*.mdb, *.accdb) "
                f"não está instalado. Instale o Microsoft Access Database Engine. "
                f"Detalhes: {error_msg}"
            )
        elif "file" in error_msg.lower() or "path" in error_msg.lower():
            raise DatabaseConnectionError(
                f"Arquivo não encontrado ou inacessível: {mdb_file}. "
                f"Verifique se o arquivo existe e tem permissões de leitura. "
                f"Detalhes: {error_msg}"
            )
        elif "locked" in error_msg.lower() or "exclusive" in error_msg.lower():
            raise DatabaseConnectionError(
                f"Arquivo bloqueado: O banco de dados está sendo usado por outro processo. "
                f"Feche outros programas que possam estar usando o arquivo. "
                f"Detalhes: {error_msg}"
            )
        else:
            raise DatabaseConnectionError(
                f"Erro de conexão com o banco de dados: {error_msg}"
            )
            
    except Exception as e:
        logging.error(f"Erro inesperado na conexão: {e}")
        raise DatabaseConnectionError(
            f"Erro inesperado ao conectar ao banco de dados: {e}"
        )


@contextmanager
def get_connection_context(mdb_file: str, password: str):
    """
    Context manager para conexão com banco de dados.
    Garante que a conexão seja fechada automaticamente.
    
    Args:
        mdb_file: Caminho para o arquivo .mdb/.accdb
        password: Senha do banco de dados
        
    Yields:
        pyodbc.Connection: Conexão com o banco de dados
        
    Raises:
        DatabaseConnectionError: Se houver erro na conexão
    """
    connection = None
    try:
        connection = get_connection(mdb_file, password)
        yield connection
        
    except Exception as e:
        logging.error(f"Erro durante uso da conexão: {e}")
        raise
        
    finally:
        if connection:
            try:
                connection.close()
                logging.info("Conexão fechada com sucesso")
            except Exception as e:
                logging.warning(f"Erro ao fechar conexão: {e}")


def test_connection(mdb_file: str, password: str) -> bool:
    """
    Testa a conexão com o banco de dados sem executar queries.
    
    Args:
        mdb_file: Caminho para o arquivo .mdb/.accdb
        password: Senha do banco de dados
        
    Returns:
        bool: True se a conexão for bem-sucedida, False caso contrário
    """
    try:
        with get_connection_context(mdb_file, password) as conn:
            # Testa se a conexão está ativa
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            cursor.close()
            logging.info("Teste de conexão bem-sucedido")
            return True
            
    except Exception as e:
        logging.error(f"Teste de conexão falhou: {e}")
        return False


def get_database_info(mdb_file: str, password: str) -> Optional[dict]:
    """
    Obtém informações sobre o banco de dados.
    
    Args:
        mdb_file: Caminho para o arquivo .mdb/.accdb
        password: Senha do banco de dados
        
    Returns:
        dict: Informações do banco ou None se houver erro
    """
    try:
        with get_connection_context(mdb_file, password) as conn:
            cursor = conn.cursor()
            
            # Lista as tabelas disponíveis
            tables = []
            for table_info in cursor.tables():
                if table_info.table_type == 'TABLE':
                    tables.append(table_info.table_name)
            
            cursor.close()
            
            return {
                "file_path": mdb_file,
                "tables": tables,
                "table_count": len(tables)
            }
            
    except Exception as e:
        logging.error(f"Erro ao obter informações do banco: {e}")
        return None