# Módulos do sistema de processamento de recebimentos

from .access_db import get_connection, get_connection_context, DatabaseConnectionError, test_connection, get_database_info
from .extractors import extract_all_data, ExtractionError, get_ordens, get_contas, get_fcaixa
from .processors import process_recebimentos
# from .exporters import export_to_excel  # Removido
from .auditor import DataAuditor, AuditError, AuditResult, AuditSummary

__all__ = [
    # Database
    'get_connection',
    'get_connection_context', 
    'DatabaseConnectionError',
    'test_connection',
    'get_database_info',
    
    # Extractors
    'extract_all_data',
    'ExtractionError',
    'get_ordens',
    'get_contas', 
    'get_fcaixa',
    
    # Processors
    'process_recebimentos',
    
    # Auditor
    'DataAuditor',
    'AuditError',
    'AuditResult',
    'AuditSummary'
]
