import pandas as pd
import logging
import sys
from datetime import datetime
from config import MDB_FILE, MDB_PASSWORD
from modules.access_db import get_connection
from modules.extractors import get_ordens, get_contas, get_fcaixa
from modules.processors import process_recebimentos
from modules.exporters import export_to_excel


def setup_logging():
    """Configura o sistema de logging"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('app.log', encoding='utf-8'),
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
            print(f"❌ Erro: {e}")
            return
        
        # Conecta e extrai dados
        logger.info("Conectando ao banco de dados...")
        try:
            conn = get_connection(MDB_FILE, MDB_PASSWORD)
            logger.info("Conexão com banco de dados estabelecida com sucesso")
        except Exception as e:
            logger.error(f"Erro ao conectar ao banco de dados: {e}")
            print(f"❌ Erro ao conectar ao banco de dados: {e}")
            print("Verifique se o arquivo .mdb existe e a senha está correta")
            return
        
        # Extrai dados
        logger.info("Extraindo dados das tabelas...")
        try:
            ordens_df = get_ordens(conn)
            contas_df = get_contas(conn)
            fcaixa_df = get_fcaixa(conn)
            logger.info(f"Dados extraídos: {len(ordens_df)} ordens, {len(contas_df)} contas, {len(fcaixa_df)} registros FCAIXA")
        except Exception as e:
            logger.error(f"Erro ao extrair dados: {e}")
            print(f"❌ Erro ao extrair dados do banco: {e}")
            return
        finally:
            conn.close()
            logger.info("Conexão com banco de dados fechada")

        # Processa recebimentos
        logger.info("Processando recebimentos...")
        try:
            recibos = process_recebimentos(ordens_df, contas_df, fcaixa_df, periodo)
            logger.info(f"Processamento concluído: {len(recibos)} registros processados")
        except Exception as e:
            logger.error(f"Erro no processamento: {e}")
            print(f"❌ Erro no processamento dos dados: {e}")
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
                    export_to_excel({periodo: df_periodo}, output_dir='data/recebimentos')
                    logger.info(f"Arquivo Excel gerado com sucesso")
                    print(f"✅ Arquivo gerado: data/recebimentos/Recebimentos_{periodo}.xlsx")
                except Exception as e:
                    logger.error(f"Erro ao exportar para Excel: {e}")
                    print(f"❌ Erro ao gerar arquivo Excel: {e}")
                    return
            else:
                logger.warning(f"Nenhum registro encontrado para o período {periodo}")
                print(f"⚠️ Nenhum registro encontrado para o período {periodo}")
        except Exception as e:
            logger.error(f"Erro ao filtrar por período: {e}")
            print(f"❌ Erro ao filtrar dados por período: {e}")
            return
        
        logger.info("Processamento concluído com sucesso")
        print("✅ Processamento concluído com sucesso!")
        
    except KeyboardInterrupt:
        logger.info("Aplicação interrompida pelo usuário")
        print("\n⚠️ Aplicação interrompida pelo usuário")
    except Exception as e:
        logger.error(f"Erro inesperado: {e}", exc_info=True)
        print(f"❌ Erro inesperado: {e}")
        print("Consulte o arquivo app.log para mais detalhes")


if __name__ == '__main__':
    main()
