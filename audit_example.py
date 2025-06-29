#!/usr/bin/env python3
"""
Exemplo de uso do módulo de auditoria
Compara dados CSV com dados gerados pela aplicação
"""

import os
import logging
from modules.auditor import DataAuditor, AuditError
from config import OUTPUT_DIR


def setup_logging():
    """Configura logging para o exemplo"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)


def main():
    """Função principal do exemplo de auditoria"""
    logger = setup_logging()
    
    try:
        logger.info("=== EXEMPLO DE AUDITORIA DE DADOS ===")
        
        # Configurações
        csv_file = "dados_para_auditoria.csv"  # Arquivo CSV para comparar
        generated_file = os.path.join(OUTPUT_DIR, "Recebimentos_2024-01.xlsx")  # Arquivo gerado pela aplicação
        audit_report = "relatorio_auditoria.xlsx"  # Relatório de saída
        
        # Verifica se os arquivos existem
        if not os.path.exists(csv_file):
            logger.error(f"Arquivo CSV não encontrado: {csv_file}")
            logger.info("Crie um arquivo CSV com os dados para auditoria")
            return
        
        if not os.path.exists(generated_file):
            logger.error(f"Arquivo gerado não encontrado: {generated_file}")
            logger.info("Execute a aplicação principal primeiro para gerar o arquivo Excel")
            return
        
        # Inicializa auditor
        auditor = DataAuditor(tolerance_percentage=0.01)  # 1% de tolerância
        
        # Define mapeamento de campos CSV -> Gerado
        # AJUSTE ESTE MAPEAMENTO CONFORME SEUS DADOS
        field_mappings = {
            # Exemplo de mapeamento - ajuste conforme necessário
            'numero_os': 'N° OS',
            'data_pagamento': 'DATA PGTO',
            'valor_total': 'VALOR TOTAL',
            'valor_pago': 'VALOR PAGO',
            'valor_devedor': 'DEVEDOR',
            'cartao': 'CARTÃO',
            'dinheiro': 'DINHEIRO',
            'pix': 'PIX',
            'troco': 'TROCO',
            'placa_veiculo': 'VEÍCULO (PLACA)',
            'codigo_cliente': 'CÓDIGO CLIENTE',
            'data_encerramento': 'DATA ENCERRAMENTO'
        }
        
        logger.info("Iniciando auditoria...")
        logger.info(f"CSV: {csv_file}")
        logger.info(f"Gerado: {generated_file}")
        logger.info(f"Campos mapeados: {len(field_mappings)}")
        
        # Executa auditoria
        summary, results = auditor.audit_data(
            csv_file_path=csv_file,
            generated_file_path=generated_file,
            field_mappings=field_mappings,
            key_field='N° OS'  # Campo chave para relacionar registros
        )
        
        # Exibe resumo
        logger.info("\n=== RESUMO DA AUDITORIA ===")
        logger.info(f"Total de registros: {summary.total_records}")
        logger.info(f"Registros coincidentes: {summary.matching_records}")
        logger.info(f"Registros divergentes: {summary.mismatched_records}")
        logger.info(f"Taxa de sucesso (registros): {(summary.matching_records/summary.total_records)*100:.2f}%")
        logger.info(f"Total de campos verificados: {summary.total_fields_checked}")
        logger.info(f"Campos coincidentes: {summary.matching_fields}")
        logger.info(f"Campos divergentes: {summary.mismatched_fields}")
        logger.info(f"Taxa de sucesso (campos): {(summary.matching_fields/summary.total_fields_checked)*100:.2f}%")
        
        # Exibe algumas divergências
        divergences = [r for r in results if not r.is_match]
        if divergences:
            logger.info(f"\n=== PRIMEIRAS 5 DIVERGÊNCIAS ===")
            for i, result in enumerate(divergences[:5]):
                logger.info(f"{i+1}. Campo: {result.field_name}")
                logger.info(f"   CSV: {result.csv_value}")
                logger.info(f"   Gerado: {result.generated_value}")
                logger.info(f"   Observação: {result.notes}")
                logger.info("")
        
        # Gera relatório detalhado
        logger.info("Gerando relatório detalhado...")
        auditor.generate_audit_report(summary, results, audit_report)
        
        logger.info(f"✅ Auditoria concluída!")
        logger.info(f"📊 Relatório salvo em: {audit_report}")
        
    except AuditError as e:
        logger.error(f"❌ Erro na auditoria: {e}")
    except Exception as e:
        logger.error(f"❌ Erro inesperado: {e}")
        logger.info("Verifique se os arquivos existem e o mapeamento está correto")


if __name__ == '__main__':
    main() 