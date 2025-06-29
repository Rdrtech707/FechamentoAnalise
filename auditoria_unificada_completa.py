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
import tkinter as tk
from tkinter import filedialog, messagebox
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
    remetente: Optional[str] = None  # Nome ou CPF do remetente
    chave_pix: Optional[str] = None  # Chave PIX do remetente


@dataclass
class GroupedPixTransaction:
    """Representa transações PIX agrupadas por remetente e data"""
    data: str
    valor_total: float
    remetente: str
    origem: str
    transacoes_originais: List[PixTransaction]
    quantidade_transacoes: int
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


def select_files_gui():
    """Interface gráfica para seleção de arquivos"""
    # Cria janela principal (oculta)
    root = tk.Tk()
    root.withdraw()  # Esconde a janela principal
    
    files = {}
    
    try:
        # Seleciona arquivo CSV do cartão
        messagebox.showinfo("Seleção de Arquivos", 
                          "Selecione o arquivo CSV de transações do cartão")
        cartao_csv = filedialog.askopenfilename(
            title="Selecione o arquivo CSV do cartão",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        
        if not cartao_csv:
            messagebox.showerror("Erro", "Nenhum arquivo CSV do cartão selecionado!")
            return None
        
        files['cartao_csv'] = cartao_csv
        
        # Seleciona arquivo CSV do banco
        messagebox.showinfo("Seleção de Arquivos", 
                          "Selecione o arquivo CSV de transações PIX do banco")
        banco_csv = filedialog.askopenfilename(
            title="Selecione o arquivo CSV do banco",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        
        if not banco_csv:
            messagebox.showerror("Erro", "Nenhum arquivo CSV do banco selecionado!")
            return None
        
        files['banco_csv'] = banco_csv
        
        # Seleciona arquivo Excel de recebimentos
        messagebox.showinfo("Seleção de Arquivos", 
                          "Selecione o arquivo Excel de recebimentos")
        recebimentos_excel = filedialog.askopenfilename(
            title="Selecione o arquivo Excel de recebimentos",
            filetypes=[("Excel files", "*.xlsx"), ("Excel files", "*.xls"), ("All files", "*.*")]
        )
        
        if not recebimentos_excel:
            messagebox.showerror("Erro", "Nenhum arquivo Excel de recebimentos selecionado!")
            return None
        
        files['recebimentos_excel'] = recebimentos_excel
        
        # Confirma seleção
        confirm_msg = f"""
Arquivos selecionados:

📄 Cartão: {os.path.basename(cartao_csv)}
🏦 Banco: {os.path.basename(banco_csv)}
📊 Recebimentos: {os.path.basename(recebimentos_excel)}

Deseja continuar com a auditoria?
        """
        
        if messagebox.askyesno("Confirmar Arquivos", confirm_msg):
            return files
        else:
            messagebox.showinfo("Cancelado", "Auditoria cancelada pelo usuário")
            return None
            
    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao selecionar arquivos: {e}")
        return None
    finally:
        root.destroy()


def select_files_powershell():
    """Seleção de arquivos via PowerShell (fallback)"""
    logger = logging.getLogger(__name__)
    
    print("\n=== SELEÇÃO DE ARQUIVOS ===")
    print("Digite os caminhos dos arquivos ou pressione Enter para usar os padrões:")
    
    # Arquivo CSV do cartão
    cartao_csv = input(f"CSV do cartão (padrão: data/extratos/report_20250628_194465.csv): ").strip()
    if not cartao_csv:
        cartao_csv = "data/extratos/report_20250628_194465.csv"
    
    # Arquivo CSV do banco
    banco_csv = input(f"CSV do banco (padrão: data/extratos/NU_636868111_01JUN2025_27JUN2025.csv): ").strip()
    if not banco_csv:
        banco_csv = "data/extratos/NU_636868111_01JUN2025_27JUN2025.csv"
    
    # Arquivo Excel de recebimentos
    recebimentos_excel = input(f"Excel de recebimentos (padrão: data/recebimentos/Recebimentos_2025-06.xlsx): ").strip()
    if not recebimentos_excel:
        recebimentos_excel = "data/recebimentos/Recebimentos_2025-06.xlsx"
    
    return {
        'cartao_csv': cartao_csv,
        'banco_csv': banco_csv,
        'recebimentos_excel': recebimentos_excel
    }


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
    """Carrega transações PIX do CSV do banco, ignorando 707 MOTORSPORT LTDA"""
    logger = logging.getLogger(__name__)
    logger.info(f"Carregando CSV do banco: {csv_path}")
    
    try:
        df = pd.read_csv(csv_path, encoding='utf-8')
        transactions = []
        
        for _, row in df.iterrows():
            descricao = str(row['Descrição']).strip()
            
            # Filtra transferências recebidas pelo PIX ou Transferência Recebida
            if (('Transferência recebida' in descricao and 'Pix' in descricao) or 
                'Transferência Recebida' in descricao):
                try:
                    valor = float(str(row['Valor']).replace(',', '.'))
                    data = str(row['Data']).strip()
                    
                    # Extrai informações do remetente da descrição
                    remetente = extract_remetente_from_description(descricao)
                    if remetente and remetente.strip().upper() == '707 MOTORSPORT LTDA':
                        continue  # Ignora esse remetente
                    chave_pix = extract_chave_pix_from_description(descricao)
                    
                    transaction = PixTransaction(
                        data=data,
                        valor=valor,
                        descricao=descricao,
                        origem='banco',
                        identificador=None,  # Não usa o identificador do banco
                        remetente=remetente,
                        chave_pix=chave_pix
                    )
                    transactions.append(transaction)
                    
                except (ValueError, KeyError) as e:
                    logger.warning(f"Erro ao processar linha do banco: {e}")
                    continue
        logger.info(f"Carregadas {len(transactions)} transações PIX do banco (ignorando 707 MOTORSPORT LTDA)")
        return transactions
        
    except Exception as e:
        logger.error(f"Erro ao carregar CSV do banco: {e}")
        return []


def extract_remetente_from_description(descricao: str) -> Optional[str]:
    """Extrai o nome do remetente da descrição da transação PIX"""
    try:
        # Padrões específicos baseados no formato real do CSV
        patterns = [
            # Padrão: "Transferência recebida pelo Pix - NOME - CPF/CNPJ - BANCO"
            r'Transferência recebida pelo Pix\s*-\s*([^-]+?)\s*-\s*[•\d\./-]+\s*-',
            # Padrão: "Transferência Recebida - NOME - CPF/CNPJ - BANCO"
            r'Transferência Recebida\s*-\s*([^-]+?)\s*-\s*[•\d\./-]+\s*-',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, descricao, re.IGNORECASE)
            if match:
                remetente = match.group(1).strip()
                # Remove caracteres especiais e normaliza
                remetente = re.sub(r'[^\w\s]', '', remetente).strip()
                # Remove espaços extras
                remetente = re.sub(r'\s+', ' ', remetente)
                if len(remetente) > 2:  # Nome deve ter pelo menos 3 caracteres
                    return remetente
        
        # Se não encontrou com os padrões específicos, tenta extrair o nome antes do primeiro CPF/CNPJ
        if '•••' in descricao or re.search(r'\d{3}\.\d{3}\.\d{3}', descricao):
            # Procura por texto antes do CPF/CNPJ
            parts = descricao.split(' - ')
            if len(parts) >= 2:
                # Pega a segunda parte (após "Transferência recebida pelo Pix")
                nome_part = parts[1]
                # Remove o CPF/CNPJ se presente
                nome_clean = re.sub(r'[•\d\./-]+', '', nome_part).strip()
                if len(nome_clean) > 2:
                    return nome_clean
        
        return None
    except:
        return None


def extract_chave_pix_from_description(descricao: str) -> Optional[str]:
    """Extrai a chave PIX da descrição da transação"""
    try:
        # Padrões para CPF, CNPJ, email, telefone
        patterns = [
            r'(\d{3}\.\d{3}\.\d{3}-\d{2})',  # CPF
            r'(\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2})',  # CNPJ
            r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',  # Email
            r'(\+55\s?\d{2}\s?\d{4,5}\s?\d{4})',  # Telefone
        ]
        
        for pattern in patterns:
            match = re.search(pattern, descricao)
            if match:
                return match.group(1)
        
        return None
    except:
        return None


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
                'os_correspondente': None,
                'observacao': f'Data {data_cartao} não encontrada nos dados gerados'
            })
            continue
        
        # Procura por valor na coluna correspondente
        campo_procurado = 'CARTÃO' if tipo_pagamento == 'CARTÃO' else 'PIX'
        valor_encontrado = None
        os_correspondente = None
        
        for _, gen_row in matching_generated.iterrows():
            if campo_procurado in gen_row.index:
                valor_gen = gen_row[campo_procurado]
                if pd.notna(valor_gen) and abs(valor_gen - valor_cartao) <= (valor_cartao * 0.01):  # 1% tolerância
                    valor_encontrado = valor_gen
                    os_correspondente = gen_row.get('N° OS', 'N/A')
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
                'os_correspondente': os_correspondente,
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
                'os_correspondente': None,
                'observacao': f'Valor {valor_cartao} não encontrado na coluna {campo_procurado} para a data {data_cartao}'
            })
    
    return results


def audit_pix_transactions(banco_transactions: List[PixTransaction], 
                          recebimentos_transactions: List[PixTransaction]) -> List[Dict]:
    """Executa auditoria de transações PIX com agrupamento por remetente"""
    logger = logging.getLogger(__name__)
    
    # Agrupa transações do banco por remetente e data
    logger.info("Agrupando transações PIX do banco por remetente...")
    banco_grouped = group_pix_transactions_by_remetente(banco_transactions)
    
    # Agrupa transações dos recebimentos por data (não há remetente)
    logger.info("Agrupando transações PIX dos recebimentos por data...")
    recebimentos_grouped = group_recebimentos_by_date(recebimentos_transactions)
    
    results = []
    
    for banco_group in banco_grouped:
        # Procura correspondência nos recebimentos agrupados
        encontrado = False
        
        for rec_group in recebimentos_grouped:
            # Compara por valor total (com tolerância de 1%)
            if abs(banco_group.valor_total - rec_group.valor_total) <= (banco_group.valor_total * 0.01):
                encontrado = True
                
                # Cria detalhes das transações individuais
                detalhes_banco = []
                for tx in banco_group.transacoes_originais:
                    detalhes_banco.append(f"R$ {tx.valor:,.2f} - {tx.remetente or 'N/A'}")
                
                detalhes_recebimentos = []
                for tx in rec_group.transacoes_originais:
                    detalhes_recebimentos.append(f"R$ {tx.valor:,.2f} - OS: {tx.referencia}")
                
                results.append({
                    'data_banco': banco_group.data,
                    'valor_banco': banco_group.valor_total,
                    'remetente_banco': banco_group.remetente,
                    'qtd_transacoes_banco': banco_group.quantidade_transacoes,
                    'detalhes_banco': ' | '.join(detalhes_banco),
                    'data_recebimentos': rec_group.data,
                    'valor_recebimentos': rec_group.valor_total,
                    'qtd_transacoes_recebimentos': rec_group.quantidade_transacoes,
                    'detalhes_recebimentos': ' | '.join(detalhes_recebimentos),
                    'status': 'CORRESPONDÊNCIA ENCONTRADA',
                    'tipo_agrupamento': 'Múltiplas transações' if banco_group.quantidade_transacoes > 1 else 'Transação única',
                    'observacao': f'Valor total R$ {banco_group.valor_total:,.2f} corresponde ao total dos recebimentos'
                })
                break
        
        if not encontrado:
            # Cria detalhes das transações individuais
            detalhes_banco = []
            for tx in banco_group.transacoes_originais:
                detalhes_banco.append(f"R$ {tx.valor:,.2f} - {tx.remetente or 'N/A'}")
            
            results.append({
                'data_banco': banco_group.data,
                'valor_banco': banco_group.valor_total,
                'remetente_banco': banco_group.remetente,
                'qtd_transacoes_banco': banco_group.quantidade_transacoes,
                'detalhes_banco': ' | '.join(detalhes_banco),
                'data_recebimentos': None,
                'valor_recebimentos': None,
                'qtd_transacoes_recebimentos': None,
                'detalhes_recebimentos': None,
                'status': 'SEM CORRESPONDÊNCIA',
                'tipo_agrupamento': 'Múltiplas transações' if banco_group.quantidade_transacoes > 1 else 'Transação única',
                'observacao': f'Transações de {banco_group.remetente} sem correspondência nos recebimentos'
            })
    
    return results


def group_pix_transactions_by_remetente(transactions: List[PixTransaction]) -> List[GroupedPixTransaction]:
    """Agrupa transações PIX da mesma pessoa no mesmo dia"""
    logger = logging.getLogger(__name__)
    
    # Agrupa por data (simplificado)
    grouped_dict = {}
    
    for tx in transactions:
        # Cria chave de agrupamento: apenas data
        group_key = tx.data
        
        if group_key not in grouped_dict:
            grouped_dict[group_key] = []
        grouped_dict[group_key].append(tx)
    
    # Cria transações agrupadas
    grouped_transactions = []
    
    for data, transacoes in grouped_dict.items():
        if len(transacoes) == 1:
            # Transação única - mantém como está
            tx = transacoes[0]
            grouped_tx = GroupedPixTransaction(
                data=data,
                valor_total=tx.valor,
                remetente=tx.remetente or "Desconhecido",
                origem=tx.origem,
                transacoes_originais=transacoes,
                quantidade_transacoes=1,
                referencia=tx.referencia
            )
        else:
            # Múltiplas transações no mesmo dia - agrupa
            valor_total = sum(tx.valor for tx in transacoes)
            # Tenta identificar um remetente comum ou usa "Múltiplos"
            remetentes = [tx.remetente for tx in transacoes if tx.remetente]
            if len(set(remetentes)) == 1 and remetentes[0]:
                remetente = remetentes[0]
            else:
                remetente = "Múltiplos remetentes"
            
            grouped_tx = GroupedPixTransaction(
                data=data,
                valor_total=valor_total,
                remetente=remetente,
                origem=transacoes[0].origem,
                transacoes_originais=transacoes,
                quantidade_transacoes=len(transacoes),
                referencia="Múltiplas transações"
            )
            logger.info(f"Agrupadas {len(transacoes)} transações em {data} - Total: R$ {valor_total:,.2f}")
        
        grouped_transactions.append(grouped_tx)
    
    logger.info(f"Transações agrupadas: {len(transactions)} -> {len(grouped_transactions)} grupos")
    return grouped_transactions


def group_recebimentos_by_date(transactions: List[PixTransaction]) -> List[GroupedPixTransaction]:
    """Agrupa transações de recebimentos por data"""
    logger = logging.getLogger(__name__)
    
    # Agrupa por data
    grouped_dict = {}
    
    for tx in transactions:
        if tx.data not in grouped_dict:
            grouped_dict[tx.data] = []
        grouped_dict[tx.data].append(tx)
    
    # Cria transações agrupadas
    grouped_transactions = []
    
    for data, transacoes in grouped_dict.items():
        if len(transacoes) == 1:
            # Transação única
            tx = transacoes[0]
            grouped_tx = GroupedPixTransaction(
                data=data,
                valor_total=tx.valor,
                remetente="Recebimento",
                origem=tx.origem,
                transacoes_originais=transacoes,
                quantidade_transacoes=1,
                referencia=tx.referencia
            )
        else:
            # Múltiplas transações na mesma data
            valor_total = sum(tx.valor for tx in transacoes)
            grouped_tx = GroupedPixTransaction(
                data=data,
                valor_total=valor_total,
                remetente="Recebimentos múltiplos",
                origem=transacoes[0].origem,
                transacoes_originais=transacoes,
                quantidade_transacoes=len(transacoes),
                referencia="Múltiplas OS"
            )
            logger.info(f"Agrupados {len(transacoes)} recebimentos em {data} - Total: R$ {valor_total:,.2f}")
        
        grouped_transactions.append(grouped_tx)
    
    return grouped_transactions


def generate_unified_report(cartao_results: List[Dict], pix_results: List[Dict], 
                           cartao_stats: Dict, recebimentos_transactions: List[PixTransaction],
                           banco_transactions: List[PixTransaction], output_file: str):
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
            
            # Auditoria de Cartão - Detalhes
            if cartao_results:
                cartao_df = pd.DataFrame(cartao_results)
                # Calcula diferença percentual apenas para linhas com diferença
                cartao_df['dif_percentual'] = cartao_df.apply(
                    lambda row: (row['diferenca'] / row['valor_cartao'] * 100) if row['diferenca'] is not None and row['valor_cartao'] and row['valor_cartao'] > 0 else None, axis=1)
                
                # Define colunas para exibição
                colunas_cartao = [
                    'identificador', 'data_cartao', 'tipo_pagamento', 'valor_cartao', 'valor_gerado',
                    'diferenca', 'dif_percentual', 'status', 'os_correspondente', 'observacao'
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

            # Auditoria PIX - Detalhes (NÃO agrupado)
            # Carrega novamente as transações PIX do banco para garantir granularidade
            banco_pix_csv = "data/extratos/NU_636868111_01JUN2025_27JUN2025.csv"
            banco_pix_df = pd.read_csv(banco_pix_csv, encoding='utf-8')
            # Filtra apenas recebidas pelo Pix ou Transferência Recebida
            pix_banco_df = banco_pix_df[
                (banco_pix_df['Descrição'].str.contains('Transferência recebida', na=False) & 
                 banco_pix_df['Descrição'].str.contains('Pix', na=False)) |
                banco_pix_df['Descrição'].str.contains('Transferência Recebida', na=False)
            ]
            # Ajusta colunas para exibir principais informações
            pix_banco_df = pix_banco_df.rename(columns={
                'Data': 'data',
                'Valor': 'valor',
                'Descrição': 'descricao',
            })
            # Extrai remetente para exibição
            pix_banco_df['remetente'] = pix_banco_df['descricao'].apply(extract_remetente_from_description)
            # Remove 707 MOTORSPORT LTDA
            pix_banco_df = pix_banco_df[~(pix_banco_df['remetente'].str.strip().str.upper() == '707 MOTORSPORT LTDA')]
            
            # Adiciona coluna OS correspondente baseada nos resultados da auditoria
            pix_banco_df['os_correspondente'] = None
            pix_banco_df['status_correspondencia'] = 'SEM CORRESPONDÊNCIA'
            
            # Carrega os dados de recebimentos para comparação individual
            recebimentos_df = pd.read_excel("data/recebimentos/Recebimentos_2025-06.xlsx")
            
            # Normaliza as datas para comparação
            recebimentos_df['DATA_PGTO_NORM'] = pd.to_datetime(recebimentos_df['DATA PGTO']).dt.strftime('%d/%m/%Y')
            
            # Primeiro, tenta correspondência individual (transação por transação)
            for idx, row in pix_banco_df.iterrows():
                # Procura correspondência por data e valor com tolerância
                matching_recebimentos = recebimentos_df[
                    (recebimentos_df['DATA_PGTO_NORM'] == row['data']) & 
                    (recebimentos_df['PIX'] > 0) &  # Garante que tem valor PIX
                    (abs(recebimentos_df['PIX'] - row['valor']) <= (row['valor'] * 0.01))  # 1% tolerância
                ]
                
                if not matching_recebimentos.empty:
                    # Encontrou correspondência individual
                    os_numero = matching_recebimentos.iloc[0]['N° OS']
                    pix_banco_df.at[idx, 'os_correspondente'] = str(os_numero)
                    pix_banco_df.at[idx, 'status_correspondencia'] = 'CORRESPONDÊNCIA ENCONTRADA'
            
            # Segundo, procura por correspondências múltiplas (múltiplas transações para uma OS)
            # Agrupa transações do banco por data
            transacoes_por_data = {}
            for idx, row in pix_banco_df.iterrows():
                if row['status_correspondencia'] == 'SEM CORRESPONDÊNCIA':  # Só processa as não encontradas
                    data = row['data']
                    if data not in transacoes_por_data:
                        transacoes_por_data[data] = []
                    transacoes_por_data[data].append({
                        'idx': idx,
                        'valor': row['valor'],
                        'remetente': row['remetente']
                    })
            
            # Para cada data com múltiplas transações não encontradas, procura correspondência por valor total
            for data, transacoes in transacoes_por_data.items():
                if len(transacoes) > 1:  # Só processa se há múltiplas transações
                    valor_total = sum(tx['valor'] for tx in transacoes)
                    
                    # Procura recebimentos com valor total correspondente na mesma data
                    matching_recebimentos = recebimentos_df[
                        (recebimentos_df['DATA_PGTO_NORM'] == data) & 
                        (recebimentos_df['PIX'] > 0) &  # Garante que tem valor PIX
                        (abs(recebimentos_df['PIX'] - valor_total) <= (valor_total * 0.01))  # 1% tolerância
                    ]
                    
                    if not matching_recebimentos.empty:
                        # Encontrou correspondência múltipla
                        os_numero = matching_recebimentos.iloc[0]['N° OS']
                        
                        # Marca todas as transações com a mesma OS
                        for tx in transacoes:
                            pix_banco_df.at[tx['idx'], 'os_correspondente'] = str(os_numero)
                            pix_banco_df.at[tx['idx'], 'status_correspondencia'] = 'CORRESPONDÊNCIA MÚLTIPLA'
            
            # Terceiro, para transações individuais não encontradas, tenta correspondência por valor total
            # (caso de uma transação que corresponde ao valor total de uma OS)
            for idx, row in pix_banco_df.iterrows():
                if row['status_correspondencia'] == 'SEM CORRESPONDÊNCIA':
                    # Procura recebimentos com valor total correspondente na mesma data
                    matching_recebimentos = recebimentos_df[
                        (recebimentos_df['DATA_PGTO_NORM'] == row['data']) & 
                        (recebimentos_df['PIX'] > 0) &  # Garante que tem valor PIX
                        (abs(recebimentos_df['PIX'] - row['valor']) <= (row['valor'] * 0.01))  # 1% tolerância
                    ]
                    
                    if not matching_recebimentos.empty:
                        # Encontrou correspondência por valor total
                        os_numero = matching_recebimentos.iloc[0]['N° OS']
                        pix_banco_df.at[idx, 'os_correspondente'] = str(os_numero)
                        pix_banco_df.at[idx, 'status_correspondencia'] = 'CORRESPONDÊNCIA ENCONTRADA'
            
            # Reordena colunas
            cols = ['data', 'valor', 'remetente', 'os_correspondente', 'status_correspondencia', 'descricao']
            pix_banco_df = pix_banco_df[cols]
            safe_to_excel(pix_banco_df, writer, 'PIX - Detalhes', theme, border_config)

            # PIX - Divergências (baseado na correspondência individual)
            pix_sem_correspondencia = pix_banco_df[pix_banco_df['status_correspondencia'] == 'SEM CORRESPONDÊNCIA']
            if not pix_sem_correspondencia.empty:
                safe_to_excel(pix_sem_correspondencia, writer, 'PIX - Divergências', theme, border_config)
            else:
                empty_df = pd.DataFrame({'Mensagem': ['Nenhuma transação sem correspondência']})
                safe_to_excel(empty_df, writer, 'PIX - Divergências', theme, border_config)

            # Calcula estatísticas PIX baseadas na correspondência individual
            correspondencias_encontradas = len(pix_banco_df[pix_banco_df['status_correspondencia'].isin(['CORRESPONDÊNCIA ENCONTRADA', 'CORRESPONDÊNCIA MÚLTIPLA'])])
            sem_correspondencia = len(pix_banco_df[pix_banco_df['status_correspondencia'] == 'SEM CORRESPONDÊNCIA'])
            
            # Atualiza o resumo com as estatísticas corretas
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
                len(banco_transactions),  # Total de transações PIX do banco (não agrupadas)
                len(recebimentos_transactions),  # Total de transações PIX dos recebimentos
                correspondencias_encontradas,  # Correspondências baseadas na correspondência individual
                sem_correspondencia,  # Sem correspondência baseada na correspondência individual
                f"{(correspondencias_encontradas / len(pix_banco_df)) * 100:.2f}%" if len(pix_banco_df) > 0 else "0%",
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


def executar_auditoria(cartao_csv: str, banco_csv: str, recebimentos_excel: str, output_file: str = None):
    """
    Executa a auditoria unificada com os arquivos especificados
    
    Args:
        cartao_csv: Caminho para o arquivo CSV de transações de cartão
        banco_csv: Caminho para o arquivo CSV de transações PIX do banco
        recebimentos_excel: Caminho para o arquivo Excel de recebimentos
        output_file: Caminho para o arquivo de saída (opcional)
    """
    logger = setup_logging()
    
    try:
        logger.info("=== AUDITORIA UNIFICADA COMPLETA ===")
        
        # Define arquivo de saída padrão se não especificado
        if not output_file:
            output_file = "data/relatorios/auditoria_unificada_completa.xlsx"
        
        # Verifica se os arquivos existem
        if not os.path.exists(cartao_csv):
            raise FileNotFoundError(f"Arquivo CSV do cartão não encontrado: {cartao_csv}")
        
        if not os.path.exists(banco_csv):
            raise FileNotFoundError(f"Arquivo CSV do banco não encontrado: {banco_csv}")
        
        if not os.path.exists(recebimentos_excel):
            raise FileNotFoundError(f"Arquivo Excel de recebimentos não encontrado: {recebimentos_excel}")
        
        logger.info("Carregando dados...")
        logger.info(f"📄 Cartão: {os.path.basename(cartao_csv)}")
        logger.info(f"🏦 Banco: {os.path.basename(banco_csv)}")
        logger.info(f"📊 Recebimentos: {os.path.basename(recebimentos_excel)}")
        
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
        generate_unified_report(cartao_results, pix_results, cartao_stats, recebimentos_transactions, banco_transactions, output_file)
        
        logger.info(f"✅ Auditoria unificada concluída!")
        logger.info(f"📊 Relatório salvo em: {output_file}")
        
        # Exibe resumo no console
        logger.info("\n=== RESUMO EXECUTIVO ===")
        logger.info(f"Cartão - Total: {cartao_stats['total_transacoes']}, Coincidentes: {cartao_stats['valores_coincidentes']}")
        logger.info(f"PIX - Banco: {len(banco_transactions)}, Recebimentos: {len(recebimentos_transactions)}")
        logger.info(f"PIX - Correspondências: {len([r for r in pix_results if r['status'] == 'CORRESPONDÊNCIA ENCONTRADA'])}")
        
        return output_file
        
    except Exception as e:
        logger.error(f"❌ Erro na auditoria: {e}")
        raise


def main():
    """Função principal"""
    logger = setup_logging()
    
    try:
        logger.info("=== AUDITORIA UNIFICADA COMPLETA ===")
        
        # Pergunta sobre o método de seleção de arquivos
        print("\n=== MÉTODO DE SELEÇÃO DE ARQUIVOS ===")
        print("1. Interface gráfica (recomendado)")
        print("2. PowerShell (linha de comando)")
        
        choice = input("\nEscolha o método (1 ou 2): ").strip()
        
        if choice == "1":
            files = select_files_gui()
        else:
            files = select_files_powershell()
        
        if not files:
            logger.info("Seleção de arquivos cancelada")
            return
        
        # Extrai caminhos dos arquivos
        cartao_csv = files['cartao_csv']
        banco_csv = files['banco_csv']
        recebimentos_excel = files['recebimentos_excel']
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
        logger.info(f"📄 Cartão: {os.path.basename(cartao_csv)}")
        logger.info(f"🏦 Banco: {os.path.basename(banco_csv)}")
        logger.info(f"📊 Recebimentos: {os.path.basename(recebimentos_excel)}")
        
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
        generate_unified_report(cartao_results, pix_results, cartao_stats, recebimentos_transactions, banco_transactions, report_file)
        
        logger.info(f"✅ Auditoria unificada concluída!")
        logger.info(f"📊 Relatório salvo em: {report_file}")
        
        # Exibe resumo no console
        logger.info("\n=== RESUMO EXECUTIVO ===")
        logger.info(f"Cartão - Total: {cartao_stats['total_transacoes']}, Coincidentes: {cartao_stats['valores_coincidentes']}")
        logger.info(f"PIX - Banco: {len(banco_transactions)}, Recebimentos: {len(recebimentos_transactions)}")
        logger.info(f"PIX - Correspondências: {len([r for r in pix_results if r['status'] == 'CORRESPONDÊNCIA ENCONTRADA'])}")
        
        # Mostra mensagem de sucesso na interface gráfica se disponível
        try:
            root = tk.Tk()
            root.withdraw()
            messagebox.showinfo("Sucesso", f"Auditoria concluída com sucesso!\n\nRelatório salvo em:\n{report_file}")
            root.destroy()
        except:
            pass
        
    except Exception as e:
        logger.error(f"❌ Erro na auditoria: {e}")
        
        # Mostra erro na interface gráfica se disponível
        try:
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror("Erro", f"Erro na auditoria:\n{e}")
            root.destroy()
        except:
            pass
        
        raise


if __name__ == '__main__':
    main() 