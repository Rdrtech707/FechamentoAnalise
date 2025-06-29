#!/usr/bin/env python3
"""
Auditoria Unificada Completa - Cartão e PIX
Combina auditoria de transações de cartão e PIX em um único relatório Excel
"""

import os
import logging
import pandas as pd
from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass
import re
from modules.auditor import DataAuditor, AuditError
from config import OUTPUT_DIR
from style_config import (
    COLUMN_WIDTHS, BORDER_CONFIGS, THEMES, 
    CURRENCY_FORMATS, DATE_FORMATS, CONTABEIS_COLS
)


@dataclass
class PixTransaction:
    """Representa uma transação PIX"""
    data: str
    valor: float
    descricao: str
    origem: str  # 'banco', 'cartao', 'recebimentos'
    identificador: Optional[str] = None
    referencia: Optional[str] = None


@dataclass
class AuditMatch:
    """Resultado de uma correspondência encontrada"""
    banco_transaction: PixTransaction
    recebimentos_transaction: Optional[PixTransaction] = None
    cartao_transaction: Optional[PixTransaction] = None
    match_type: str = "exato"
    confidence: float = 1.0
    notes: str = ""


def setup_logging():
    """Configura logging para a auditoria unificada"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)


def parse_cartao_csv(csv_file_path: str) -> pd.DataFrame:
    """
    Carrega e processa o CSV de transações de cartão
    """
    logger = logging.getLogger(__name__)
    
    try:
        logger.info(f"Carregando CSV de transações: {csv_file_path}")
        
        # Carrega o CSV
        df = pd.read_csv(csv_file_path, encoding='utf-8')
        
        # Processa a coluna de data
        df['Data e hora'] = pd.to_datetime(df['Data e hora'], format='%d %b, %Y · %H:%M')
        df['DATA_PGTO'] = df['Data e hora'].dt.date
        
        # Processa valores monetários
        df['Valor (R$)'] = df['Valor (R$)'].str.replace('"', '').str.replace('.', '').str.replace(',', '.').astype(float)
        df['Líquido (R$)'] = df['Líquido (R$)'].str.replace('"', '').str.replace('.', '').str.replace(',', '.').astype(float)
        
        # Cria colunas para auditoria
        df['TIPO_PAGAMENTO'] = df['Meio - Meio'].apply(lambda x: 'CARTÃO' if x in ['Crédito', 'Débito', 'Credito', 'Debito'] else 'PIX')
        df['VALOR_AUDITORIA'] = df['Valor (R$)']
        
        logger.info(f"CSV processado: {len(df)} transações")
        logger.info(f"Transações por tipo: {df['TIPO_PAGAMENTO'].value_counts().to_dict()}")
        
        return df
        
    except Exception as e:
        error_msg = f"Erro ao processar CSV de transações: {e}"
        logger.error(error_msg)
        raise AuditError(error_msg)


def load_banco_pix_csv(csv_path: str) -> List[PixTransaction]:
    """Carrega transações PIX do CSV do banco"""
    logger = logging.getLogger(__name__)
    logger.info(f"Carregando CSV do banco: {csv_path}")
    
    try:
        df = pd.read_csv(csv_path, encoding='utf-8')
        transactions = []
        
        for _, row in df.iterrows():
            descricao = str(row['Descrição']).strip()
            
            # Filtra apenas transferências recebidas pelo PIX
            if 'Transferência recebida' in descricao and 'Pix' in descricao:
                try:
                    valor = float(str(row['Valor']).replace(',', '.'))
                    data = str(row['Data']).strip()
                    
                    transaction = PixTransaction(
                        data=data,
                        valor=valor,
                        descricao=descricao,
                        origem='banco',
                        identificador=str(row['Identificador']).strip()
                    )
                    transactions.append(transaction)
                    
                except (ValueError, KeyError) as e:
                    logger.warning(f"Erro ao processar linha do banco: {e}")
                    continue
        
        logger.info(f"Carregadas {len(transactions)} transações PIX do banco")
        return transactions
        
    except Exception as e:
        logger.error(f"Erro ao carregar CSV do banco: {e}")
        return []


def load_recebimentos_excel(excel_path: str) -> List[PixTransaction]:
    """Carrega transações PIX da tabela de recebimentos"""
    logger = logging.getLogger(__name__)
    logger.info(f"Carregando Excel de recebimentos: {excel_path}")
    
    try:
        df = pd.read_excel(excel_path)
        transactions = []
        
        for _, row in df.iterrows():
            try:
                # Verifica se tem valor PIX
                valor_pix = row.get('PIX', 0)
                if pd.notna(valor_pix) and float(valor_pix) > 0:
                    data_pgto = str(row.get('DATA PGTO', '')).strip()
                    if data_pgto and data_pgto != 'nan':
                        transaction = PixTransaction(
                            data=data_pgto,
                            valor=float(valor_pix),
                            descricao=f"Recebimento PIX - OS: {row.get('N° OS', 'N/A')}",
                            origem='recebimentos',
                            referencia=str(row.get('N° OS', '')).strip()
                        )
                        transactions.append(transaction)
                        
            except (ValueError, KeyError) as e:
                logger.warning(f"Erro ao processar linha de recebimentos: {e}")
                continue
        
        logger.info(f"Carregadas {len(transactions)} transações PIX dos recebimentos")
        return transactions
        
    except Exception as e:
        logger.error(f"Erro ao carregar Excel de recebimentos: {e}")
        return []


def audit_cartao_transactions(cartao_df: pd.DataFrame, generated_df: pd.DataFrame) -> List[Dict]:
    """Executa auditoria de transações de cartão"""
    results = []
    
    for idx, cartao_row in cartao_df.iterrows():
        identificador = cartao_row['Identificador']
        valor_cartao = cartao_row['VALOR_AUDITORIA']
        data_cartao = cartao_row['DATA_PGTO']
        tipo_pagamento = cartao_row['TIPO_PAGAMENTO']
        
        # Procura registro correspondente por data
        matching_generated = generated_df[generated_df['DATA PGTO'] == data_cartao]
        
        if len(matching_generated) == 0:
            # Transação não encontrada
            results.append({
                'identificador': identificador,
                'data_cartao': data_cartao,
                'valor_cartao': valor_cartao,
                'tipo_pagamento': tipo_pagamento,
                'status': 'NÃO ENCONTRADA',
                'valor_gerado': None,
                'diferenca': None,
                'observacao': f'Data {data_cartao} não encontrada nos dados gerados'
            })
            continue
        
        # Procura por valor na coluna correspondente
        campo_procurado = 'CARTÃO' if tipo_pagamento == 'CARTÃO' else 'PIX'
        valor_encontrado = None
        
        for _, gen_row in matching_generated.iterrows():
            if campo_procurado in gen_row.index:
                valor_gen = gen_row[campo_procurado]
                if pd.notna(valor_gen) and abs(valor_gen - valor_cartao) <= (valor_cartao * 0.01):  # 1% tolerância
                    valor_encontrado = valor_gen
                    break
        
        if valor_encontrado is not None:
            # Valor encontrado
            diferenca = abs(valor_cartao - valor_encontrado)
            is_match = diferenca <= (valor_cartao * 0.01)
            
            results.append({
                'identificador': identificador,
                'data_cartao': data_cartao,
                'valor_cartao': valor_cartao,
                'tipo_pagamento': tipo_pagamento,
                'status': 'COINCIDENTE' if is_match else 'DIVERGENTE',
                'valor_gerado': valor_encontrado,
                'diferenca': diferenca,
                'observacao': f'Encontrado na coluna {campo_procurado}'
            })
        else:
            # Valor não encontrado
            results.append({
                'identificador': identificador,
                'data_cartao': data_cartao,
                'valor_cartao': valor_cartao,
                'tipo_pagamento': tipo_pagamento,
                'status': 'VALOR NÃO ENCONTRADO',
                'valor_gerado': None,
                'diferenca': None,
                'observacao': f'Valor {valor_cartao} não encontrado na coluna {campo_procurado} para a data {data_cartao}'
            })
    
    return results


def audit_pix_transactions(banco_transactions: List[PixTransaction], 
                          recebimentos_transactions: List[PixTransaction]) -> List[Dict]:
    """Executa auditoria de transações PIX"""
    results = []
    
    for banco_tx in banco_transactions:
        # Procura correspondência nos recebimentos
        encontrado = False
        for rec_tx in recebimentos_transactions:
            # Compara por valor (com tolerância de 1%)
            if abs(banco_tx.valor - rec_tx.valor) <= (banco_tx.valor * 0.01):
                encontrado = True
                results.append({
                    'data_banco': banco_tx.data,
                    'valor_banco': banco_tx.valor,
                    'descricao_banco': banco_tx.descricao,
                    'data_recebimentos': rec_tx.data,
                    'valor_recebimentos': rec_tx.valor,
                    'os_recebimentos': rec_tx.referencia,
                    'status': 'CORRESPONDÊNCIA ENCONTRADA',
                    'observacao': f'Valor R$ {banco_tx.valor:,.2f} encontrado nos recebimentos (OS: {rec_tx.referencia})'
                })
                break
        
        if not encontrado:
            results.append({
                'data_banco': banco_tx.data,
                'valor_banco': banco_tx.valor,
                'descricao_banco': banco_tx.descricao,
                'data_recebimentos': None,
                'valor_recebimentos': None,
                'os_recebimentos': None,
                'status': 'SEM CORRESPONDÊNCIA',
                'observacao': 'Transação do banco sem correspondência nos recebimentos'
            })
    
    return results


def generate_unified_report(cartao_results: List[Dict], pix_results: List[Dict], 
                           cartao_stats: Dict, recebimentos_transactions: List[PixTransaction],
                           output_file: str):
    """Gera relatório Excel unificado com formatação otimizada"""
    try:
        # Garante que a pasta existe
        pasta = os.path.dirname(output_file)
        if pasta and not os.path.exists(pasta):
            os.makedirs(pasta)

        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            # Configurações de estilo
            theme = THEMES['default']
            border_config = BORDER_CONFIGS['default']
            
            # Resumo Geral
            metricas = [
                '=== AUDITORIA DE CARTÃO ===',
                'Total de Transações',
                'Cartão Encontradas',
                'PIX Encontradas',
                'Não Encontradas',
                'Valores Coincidentes',
                'Valores Divergentes',
                'Taxa de Sucesso (%)',
                '',
                '=== AUDITORIA PIX ===',
                'Total Transações Banco',
                'Total Transações Recebimentos',
                'Correspondências Encontradas',
                'Sem Correspondência',
                'Taxa de Correspondência (%)',
                '',
                'Data da Auditoria'
            ]
            valores = [
                '',
                cartao_stats['total_transacoes'],
                cartao_stats['cartao_encontradas'],
                cartao_stats['pix_encontradas'],
                cartao_stats['nao_encontradas'],
                cartao_stats['valores_coincidentes'],
                cartao_stats['valores_divergentes'],
                f"{(cartao_stats['valores_coincidentes'] / cartao_stats['total_transacoes']) * 100:.2f}%" if cartao_stats['total_transacoes'] > 0 else "0%",
                '',
                '',
                len(pix_results),
                len(recebimentos_transactions),
                len([r for r in pix_results if r['status'] == 'CORRESPONDÊNCIA ENCONTRADA']),
                len([r for r in pix_results if r['status'] == 'SEM CORRESPONDÊNCIA']),
                f"{(len([r for r in pix_results if r['status'] == 'CORRESPONDÊNCIA ENCONTRADA']) / len(pix_results)) * 100:.2f}%" if pix_results else "0%",
                '',
                datetime.now().strftime('%d/%m/%Y %H:%M:%S')
            ]
            
            # Garante que as listas tenham o mesmo tamanho
            if len(metricas) != len(valores):
                diff = abs(len(metricas) - len(valores))
                if len(metricas) > len(valores):
                    valores += [''] * diff
                else:
                    metricas += [''] * diff
                    
            summary_data = {'Métrica': metricas, 'Valor': valores}
            summary_df = pd.DataFrame(summary_data)
            safe_to_excel(summary_df, writer, 'Resumo Geral', theme, border_config)

            # Auditoria de Cartão - Detalhes
            if cartao_results:
                cartao_df = pd.DataFrame(cartao_results)
                # Calcula diferença percentual apenas para linhas com diferença
                cartao_df['dif_percentual'] = cartao_df.apply(
                    lambda row: (row['diferenca'] / row['valor_cartao'] * 100) if row['diferenca'] is not None and row['valor_cartao'] and row['valor_cartao'] > 0 else None, axis=1)
                
                # Define colunas para exibição
                colunas_cartao = [
                    'identificador', 'data_cartao', 'tipo_pagamento', 'valor_cartao', 'valor_gerado',
                    'diferenca', 'dif_percentual', 'status', 'observacao'
                ]
                cartao_df = cartao_df[[c for c in colunas_cartao if c in cartao_df.columns]]
                
                if not cartao_df.empty:
                    safe_to_excel(cartao_df, writer, 'Cartão - Detalhes', theme, border_config)
                else:
                    empty_df = pd.DataFrame({'Mensagem': ['Nenhuma transação de cartão encontrada']})
                    safe_to_excel(empty_df, writer, 'Cartão - Detalhes', theme, border_config)
                
                # Divergências de Cartão
                divergencias_cartao = [r for r in cartao_results if r['status'] in ['DIVERGENTE', 'NÃO ENCONTRADA', 'VALOR NÃO ENCONTRADO']]
                if divergencias_cartao:
                    divergencias_df = pd.DataFrame(divergencias_cartao)
                    divergencias_df['dif_percentual'] = divergencias_df.apply(
                        lambda row: (row['diferenca'] / row['valor_cartao'] * 100) if row['diferenca'] is not None and row['valor_cartao'] and row['valor_cartao'] > 0 else None, axis=1)
                    divergencias_df = divergencias_df[[c for c in colunas_cartao if c in divergencias_df.columns]]
                    safe_to_excel(divergencias_df, writer, 'Cartão - Divergências', theme, border_config)
                else:
                    empty_df = pd.DataFrame({'Mensagem': ['Nenhuma divergência encontrada']})
                    safe_to_excel(empty_df, writer, 'Cartão - Divergências', theme, border_config)
            else:
                empty_df = pd.DataFrame({'Mensagem': ['Nenhuma transação de cartão encontrada']})
                safe_to_excel(empty_df, writer, 'Cartão - Detalhes', theme, border_config)

            # Auditoria PIX - Detalhes
            if pix_results:
                pix_df = pd.DataFrame(pix_results)
                safe_to_excel(pix_df, writer, 'PIX - Detalhes', theme, border_config)
                
                # PIX sem correspondência
                pix_sem_correspondencia = [r for r in pix_results if r['status'] == 'SEM CORRESPONDÊNCIA']
                if pix_sem_correspondencia:
                    pix_sem_df = pd.DataFrame(pix_sem_correspondencia)
                    safe_to_excel(pix_sem_df, writer, 'PIX - Sem Correspondência', theme, border_config)
                else:
                    empty_df = pd.DataFrame({'Mensagem': ['Nenhuma transação sem correspondência']})
                    safe_to_excel(empty_df, writer, 'PIX - Sem Correspondência', theme, border_config)
            else:
                empty_df = pd.DataFrame({'Mensagem': ['Nenhuma transação PIX encontrada']})
                safe_to_excel(empty_df, writer, 'PIX - Detalhes', theme, border_config)

    except Exception as e:
        logging.error(f"Erro ao gerar relatório: {e}")
        raise


def configure_worksheet_properties(worksheet, sheet_name):
    """Configura propriedades da planilha para melhor apresentação"""
    from openpyxl.worksheet.views import SheetView
    
    # Configura view da planilha usando a API correta
    if not hasattr(worksheet, 'sheet_view') or worksheet.sheet_view is None:
        worksheet.sheet_view = SheetView()
    
    # Configura propriedades da view
    worksheet.sheet_view.showGridLines = True
    worksheet.sheet_view.showRowColHeaders = True
    worksheet.sheet_view.zoomScale = 100
    worksheet.sheet_view.zoomScaleNormal = 100
    worksheet.sheet_view.zoomScalePageLayoutView = 100
    
    # Configura propriedades específicas por tipo de planilha
    if 'Detalhes' in sheet_name:
        # Para detalhes, ajusta zoom para melhor visualização
        worksheet.sheet_view.zoomScale = 90
    elif 'Divergências' in sheet_name or 'Sem Correspondência' in sheet_name:
        # Para divergências, zoom menor para ver mais dados
        worksheet.sheet_view.zoomScale = 85


def safe_to_excel(df, writer, sheet_name, theme, border_config):
    """Salva DataFrame no Excel com formatação segura e otimizada"""
    # Processa o DataFrame para evitar problemas
    df_processed = df.copy()
    
    # Preenche valores NaN
    df_processed = df_processed.fillna('')
    
    # Converte para string e trata valores que começam com "="
    for col in df_processed.columns:
        df_processed[col] = df_processed[col].astype(str).apply(
            lambda x: "'" + x if isinstance(x, str) and x.startswith('=') else x
        )
    
    # Remove linhas completamente vazias
    df_processed = df_processed.dropna(how='all')
    
    # Se o DataFrame ficou vazio, cria uma linha com mensagem
    if df_processed.empty:
        df_processed = pd.DataFrame({'Mensagem': ['Nenhum dado disponível para esta seção']})
    
    # Salva no Excel
    df_processed.to_excel(writer, sheet_name=sheet_name, index=False)
    
    # Obtém a planilha e aplica formatação
    worksheet = writer.sheets[sheet_name]
    apply_worksheet_formatting(worksheet, df_processed, theme, border_config)
    configure_worksheet_properties(worksheet, sheet_name)


def optimize_column_widths(worksheet, df):
    """Otimiza a largura das colunas baseada no conteúdo e configurações"""
    from openpyxl.utils import get_column_letter
    
    for col in range(1, len(df.columns) + 1):
        column_name = df.columns[col - 1]
        
        # Largura mínima baseada na configuração
        min_width = COLUMN_WIDTHS.get(column_name, COLUMN_WIDTHS['default'])
        
        # Calcula largura baseada no conteúdo
        header_length = len(str(column_name))
        max_content_length = header_length
        
        # Analisa o conteúdo das células
        for row in range(min(len(df), 100)):  # Limita a 100 linhas para performance
            try:
                cell_value = str(df.iloc[row, col - 1])
                # Remove caracteres especiais para cálculo mais preciso
                clean_value = cell_value.replace('R$', '').replace(',', '').replace('.', '')
                max_content_length = max(max_content_length, len(clean_value))
            except:
                continue
        
        # Aplica fatores de ajuste baseados no tipo de coluna
        if any(keyword in column_name.lower() for keyword in ['observacao', 'descricao', 'notes']):
            # Colunas de texto longo - largura maior
            content_width = max_content_length * 1.3
            max_width = 100
        elif any(keyword in column_name.lower() for keyword in ['valor', 'diferenca', 'percentual']):
            # Colunas numéricas - largura fixa para formatação
            content_width = max_content_length * 1.1
            max_width = 25
        elif 'data' in column_name.lower():
            # Colunas de data - largura fixa
            content_width = 15
            max_width = 20
        else:
            # Colunas padrão
            content_width = max_content_length * 1.2
            max_width = 50
        
        # Define largura final
        final_width = max(min_width, min(content_width, max_width))
        worksheet.column_dimensions[get_column_letter(col)].width = final_width


def apply_worksheet_formatting(worksheet, df, theme, border_config):
    """Aplica formatação uniforme à planilha com largura de colunas otimizada"""
    from openpyxl.styles import Font, PatternFill, Border, Side, Alignment
    from openpyxl.utils import get_column_letter
    
    # Configurações de borda
    border_style = Side(style=border_config['data_border'], color=border_config['border_color'])
    header_border_style = Side(style=border_config['header_border'], color=border_config['border_color'])
    
    # Estilo do cabeçalho
    header_font = Font(bold=True, color=theme['header_font'])
    header_fill = PatternFill(start_color=theme['header_bg'], end_color=theme['header_bg'], fill_type='solid')
    header_alignment = Alignment(horizontal='center', vertical='center')
    
    # Estilo das células de dados
    data_font = Font(color='000000')
    data_alignment = Alignment(horizontal='left', vertical='center')
    
    # Aplica formatação ao cabeçalho
    for col in range(1, len(df.columns) + 1):
        cell = worksheet.cell(row=1, column=col)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = header_alignment
        cell.border = Border(
            left=header_border_style, right=header_border_style,
            top=header_border_style, bottom=header_border_style
        )
    
    # Aplica formatação aos dados
    for row in range(2, len(df) + 2):
        for col in range(1, len(df.columns) + 1):
            cell = worksheet.cell(row=row, column=col)
            cell.font = data_font
            cell.alignment = data_alignment
            cell.border = Border(
                left=border_style, right=border_style,
                top=border_style, bottom=border_style
            )
            
            # Formatação específica para colunas numéricas
            column_name = df.columns[col - 1]
            if any(keyword in column_name.lower() for keyword in ['valor', 'diferenca', 'percentual']):
                if cell.value is not None and isinstance(cell.value, (int, float)):
                    cell.number_format = CURRENCY_FORMATS['BRL']
                    cell.alignment = Alignment(horizontal='right', vertical='center')
            
            # Formatação para datas
            elif 'data' in column_name.lower():
                if cell.value is not None:
                    cell.number_format = DATE_FORMATS['pt_BR']
                    cell.alignment = Alignment(horizontal='center', vertical='center')
    
    # Otimiza largura das colunas
    optimize_column_widths(worksheet, df)


def main():
    """Função principal"""
    logger = setup_logging()
    
    try:
        logger.info("=== AUDITORIA UNIFICADA COMPLETA ===")
        
        # Configurações
        cartao_csv = "data/extratos/report_20250628_194465.csv"
        banco_csv = "data/extratos/NU_636868111_01JUN2025_27JUN2025.csv"
        recebimentos_excel = "data/recebimentos/Recebimentos_2025-06.xlsx"
        report_file = "data/relatorios/auditoria_unificada_completa.xlsx"
        
        # Verifica se os arquivos existem
        if not os.path.exists(cartao_csv):
            logger.error(f"Arquivo CSV do cartão não encontrado: {cartao_csv}")
            return
        
        if not os.path.exists(banco_csv):
            logger.error(f"Arquivo CSV do banco não encontrado: {banco_csv}")
            return
        
        if not os.path.exists(recebimentos_excel):
            logger.error(f"Arquivo Excel de recebimentos não encontrado: {recebimentos_excel}")
            return
        
        logger.info("Carregando dados...")
        
        # Carrega dados de cartão
        cartao_df = parse_cartao_csv(cartao_csv)
        
        # Carrega dados gerados
        auditor = DataAuditor(tolerance_percentage=0.01)
        generated_df = auditor.load_generated_data(recebimentos_excel)
        generated_df = auditor.normalize_column_names(generated_df)
        
        # Converte DATA PGTO para date se necessário
        if 'DATA PGTO' in generated_df.columns:
            generated_df['DATA PGTO'] = pd.to_datetime(generated_df['DATA PGTO']).dt.date
        
        # Carrega dados PIX
        banco_transactions = load_banco_pix_csv(banco_csv)
        recebimentos_transactions = load_recebimentos_excel(recebimentos_excel)
        
        logger.info("Executando auditorias...")
        
        # Executa auditoria de cartão
        cartao_results = audit_cartao_transactions(cartao_df, generated_df)
        
        # Calcula estatísticas do cartão
        cartao_stats = {
            'total_transacoes': len(cartao_df),
            'cartao_encontradas': len([r for r in cartao_results if r['tipo_pagamento'] == 'CARTÃO' and r['status'] == 'COINCIDENTE']),
            'pix_encontradas': len([r for r in cartao_results if r['tipo_pagamento'] == 'PIX' and r['status'] == 'COINCIDENTE']),
            'nao_encontradas': len([r for r in cartao_results if r['status'] in ['NÃO ENCONTRADA', 'VALOR NÃO ENCONTRADO']]),
            'valores_coincidentes': len([r for r in cartao_results if r['status'] == 'COINCIDENTE']),
            'valores_divergentes': len([r for r in cartao_results if r['status'] == 'DIVERGENTE'])
        }
        
        # Executa auditoria PIX
        pix_results = audit_pix_transactions(banco_transactions, recebimentos_transactions)
        
        logger.info("Gerando relatório unificado...")
        
        # Gera relatório unificado
        generate_unified_report(cartao_results, pix_results, cartao_stats, recebimentos_transactions, report_file)
        
        logger.info(f"✅ Auditoria unificada concluída!")
        logger.info(f"📊 Relatório salvo em: {report_file}")
        
        # Exibe resumo no console
        logger.info("\n=== RESUMO EXECUTIVO ===")
        logger.info(f"Cartão - Total: {cartao_stats['total_transacoes']}, Coincidentes: {cartao_stats['valores_coincidentes']}")
        logger.info(f"PIX - Banco: {len(banco_transactions)}, Recebimentos: {len(recebimentos_transactions)}")
        logger.info(f"PIX - Correspondências: {len([r for r in pix_results if r['status'] == 'CORRESPONDÊNCIA ENCONTRADA'])}")
        
    except Exception as e:
        logger.error(f"❌ Erro na auditoria: {e}")
        raise


if __name__ == '__main__':
    main() 