import pandas as pd
import logging
import sys
from datetime import datetime
from config import (
    MDB_FILE, MDB_PASSWORD, OUTPUT_DIR, LOG_LEVEL, LOG_FILE, 
    FILE_ENCODING, MAX_RECORDS, EXCEL_SETTINGS, FORMATTING,
    ConfigError, get_config_summary
)
from modules.access_db import get_connection_context, DatabaseConnectionError, test_connection, get_database_info
from modules.extractors import extract_all_data, ExtractionError
from modules.processors import process_recebimentos
from modules.exporters import export_to_excel
from modules.export_json import export_to_json


def setup_logging():
    """Configura o sistema de logging"""
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL.upper()),
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(LOG_FILE, encoding=FILE_ENCODING),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)


def validate_input(year: str, month: str) -> tuple[str, str]:
    """
    Valida e formata os inputs de ano e mês
    
    Args:
        year: Ano informado pelo usuário
        month: Mês informado pelo usuário
        
    Returns:
        tuple: (ano_validado, mes_validado)
        
    Raises:
        ValueError: Se os valores não forem válidos
    """
    # Remove espaços e valida se são números
    year = year.strip()
    month = month.strip()
    
    if not year.isdigit() or not month.isdigit():
        raise ValueError("Ano e mês devem ser números válidos")
    
    year_int = int(year)
    month_int = int(month)
    
    # Validação de ano (entre 2000 e 2100)
    if year_int < 2000 or year_int > 2100:
        raise ValueError("Ano deve estar entre 2000 e 2100")
    
    # Validação de mês (entre 1 e 12)
    if month_int < 1 or month_int > 12:
        raise ValueError("Mês deve estar entre 1 e 12")
    
    # Formata mês com zero à esquerda
    month_formatted = f"{month_int:02d}"
    
    return year, month_formatted


def main():
    """Função principal da aplicação"""
    logger = setup_logging()
    
    try:
        logger.info("Iniciando aplicação de processamento de recebimentos")
        
        # Exibe resumo das configurações
        config_summary = get_config_summary()
        logger.info(f"Configurações carregadas: {config_summary}")
        
        # Testa conexão com banco antes de prosseguir
        logger.info("Testando conexão com banco de dados...")
        if not test_connection(MDB_FILE, MDB_PASSWORD):
            print("[ERRO] Falha no teste de conexão com banco de dados")
            return
        
        # Obtém informações do banco
        db_info = get_database_info(MDB_FILE, MDB_PASSWORD)
        if db_info:
            logger.info(f"Banco de dados: {db_info['file_path']}")
            logger.info(f"Tabelas encontradas: {db_info['table_count']}")
            #logger.info(f"Lista de tabelas: {db_info['tables']}")
        
        # Pergunta mês e ano ao usuário
        year = input("Informe o ano (YYYY): ").strip()
        month = input("Informe o mês (MM): ").strip()
        
        # Valida inputs
        try:
            year_validated, month_validated = validate_input(year, month)
            periodo = f"{year_validated}-{month_validated}"
            logger.info(f"Período selecionado: {periodo}")
        except ValueError as e:
            logger.error(f"Erro na validação de input: {e}")
            print(f"[ERRO] Erro: {e}")
            return
        
        # Conecta e extrai dados usando context manager
        logger.info("Conectando ao banco de dados...")
        try:
            with get_connection_context(MDB_FILE, MDB_PASSWORD) as conn:
                logger.info("Conexão com banco de dados estabelecida com sucesso")
                
                # Extrai dados usando a nova função consolidada
                try:
                    ordens_df, contas_df, fcaixa_df = extract_all_data(conn)
                    
                    # Aplica limite de registros se configurado
                    if MAX_RECORDS > 0:
                        logger.info(f"Aplicando limite de {MAX_RECORDS} registros")
                        ordens_df = ordens_df.head(MAX_RECORDS)
                        contas_df = contas_df.head(MAX_RECORDS)
                        fcaixa_df = fcaixa_df.head(MAX_RECORDS)
                        
                except ExtractionError as e:
                    logger.error(f"Erro na extração de dados: {e}")
                    print(f"[ERRO] Erro na extração de dados: {e}")
                    return
                except Exception as e:
                    logger.error(f"Erro inesperado na extração: {e}")
                    print(f"[ERRO] Erro inesperado na extração: {e}")
                    return
                    
        except DatabaseConnectionError as e:
            logger.error(f"Erro de conexão com banco de dados: {e}")
            print(f"[ERRO] Erro de conexão com banco de dados: {e}")
            return
        except Exception as e:
            logger.error(f"Erro inesperado na conexão: {e}")
            print(f"[ERRO] Erro inesperado na conexão: {e}")
            return

        # Processa recebimentos
        logger.info("Processando recebimentos...")
        try:
            recibos = process_recebimentos(ordens_df, contas_df, fcaixa_df, periodo)
            logger.info(f"Processamento concluído: {len(recibos)} registros processados")
        except Exception as e:
            logger.error(f"Erro no processamento: {e}")
            print(f"[ERRO] Erro no processamento dos dados: {e}")
            return

        # Remove hora, mantendo apenas a data
        try:
            recibos['DATA PGTO'] = pd.to_datetime(recibos['DATA PGTO']).dt.date
            recibos['DATA ENCERRAMENTO'] = pd.to_datetime(recibos['DATA ENCERRAMENTO']).dt.date
        except Exception as e:
            logger.warning(f"Erro ao converter datas: {e}")

        # Reordena colunas
        column_order = [
            'N° OS', 'DATA PGTO', 'VALOR TOTAL', 'VALOR MÃO DE OBRA',
            'VALOR PEÇAS', 'DESCONTO', 'VALOR PAGO', 'DEVEDOR', 'CARTÃO', 'DINHEIRO',
            'PIX', 'TROCO', 'VEÍCULO (PLACA)', 'CÓDIGO CLIENTE', 'DATA ENCERRAMENTO'
        ]
        
        # Verifica se todas as colunas existem
        missing_columns = [col for col in column_order if col not in recibos.columns]
        if missing_columns:
            logger.warning(f"Colunas não encontradas: {missing_columns}")
            # Remove colunas que não existem da lista de ordenação
            column_order = [col for col in column_order if col in recibos.columns]
        
        recibos = recibos[column_order]

        # Filtra pelo período desejado baseado em DATA PGTO
        try:
            valid = recibos.dropna(subset=['DATA PGTO']).copy()
            valid['MES'] = valid['DATA PGTO'].astype(str).str.slice(0, 7)
            
            if periodo in valid['MES'].unique():
                df_periodo = valid[valid['MES'] == periodo].drop(columns='MES')
                logger.info(f"Encontrados {len(df_periodo)} registros para o período {periodo}")
                
                # Exporta para Excel
                try:
                    export_to_excel(
                        {periodo: df_periodo}, 
                        output_dir=OUTPUT_DIR,
                        border_theme='default'  # Pode ser alterado para 'corporate', 'dark', 'minimal'
                    )
                    logger.info(f"Arquivo Excel gerado com sucesso em {OUTPUT_DIR}")
                    print(f"[OK] Arquivo gerado: {OUTPUT_DIR}/Recebimentos_{periodo}.xlsx")
                    # Exporta também para JSON
                    try:
                        json_path = export_to_json(
                            df_periodo,
                            output_dir=OUTPUT_DIR,
                            filename=f"Recebimentos_{periodo}",
                            logger=logger
                        )
                        print(f"[OK] Arquivo JSON gerado: {json_path}")
                    except Exception as e:
                        logger.error(f"Erro ao exportar para JSON: {e}")
                        print(f"[ERRO] Erro ao gerar arquivo JSON: {e}")
                except Exception as e:
                    logger.error(f"Erro ao exportar para Excel: {e}")
                    print(f"[ERRO] Erro ao gerar arquivo Excel: {e}")
                    return
            else:
                logger.warning(f"Nenhum registro encontrado para o período {periodo}")
                print(f"[AVISO] Nenhum registro encontrado para o período {periodo}")
        except Exception as e:
            logger.error(f"Erro ao filtrar por período: {e}")
            print(f"[ERRO] Erro ao filtrar dados por período: {e}")
            return
        
        logger.info("Processamento concluído com sucesso")
        print("[OK] Processamento concluído com sucesso!")
        
    except KeyboardInterrupt:
        logger.info("Aplicação interrompida pelo usuário")
        print("\n[AVISO] Aplicação interrompida pelo usuário")
    except ConfigError as e:
        logger.error(f"Erro de configuração: {e}")
        print(f"[ERRO] Erro de configuração: {e}")
    except Exception as e:
        logger.error(f"Erro inesperado: {e}", exc_info=True)
        print(f"[ERRO] Erro inesperado: {e}")
        print("Consulte o arquivo app.log para mais detalhes")


if __name__ == '__main__':
    main()
