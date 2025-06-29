"""
Auditoria Unificada PIX - Compara dados do banco, cartão e tabela de recebimentos
Analisa transferências PIX recebidas para identificar correspondências e divergências
"""

import pandas as pd
import logging
from datetime import datetime
import os
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import re


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
    match_type: str = "exato"  # 'exato', 'aproximado', 'parcial'
    confidence: float = 1.0
    notes: str = ""


@dataclass
class AuditSummary:
    """Resumo da auditoria"""
    total_banco_pix: int
    total_cartao_pix: int
    total_recebimentos_pix: int
    matches_encontrados: int
    divergencias_banco: int
    divergencias_cartao: int
    divergencias_recebimentos: int
    valor_total_banco: float
    valor_total_cartao: float
    valor_total_recebimentos: float
    audit_date: datetime


class PixAuditor:
    """
    Auditor especializado em análise de transações PIX
    """
    
    def __init__(self, tolerance_days: int = 3, tolerance_value: float = 0.01):
        """
        Inicializa o auditor
        
        Args:
            tolerance_days: Tolerância em dias para correspondência de datas
            tolerance_value: Tolerância percentual para valores (1% = 0.01)
        """
        self.tolerance_days = tolerance_days
        self.tolerance_value = tolerance_value
        self.logger = logging.getLogger(__name__)
        
        # Configurar logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('audit_pix_unificado.log', encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
    
    def load_banco_csv(self, csv_path: str) -> List[PixTransaction]:
        """
        Carrega transações PIX do CSV do banco
        """
        self.logger.info(f"Carregando CSV do banco: {csv_path}")
        
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
                        self.logger.warning(f"Erro ao processar linha do banco: {e}")
                        continue
            
            self.logger.info(f"Carregadas {len(transactions)} transações PIX do banco")
            return transactions
            
        except Exception as e:
            self.logger.error(f"Erro ao carregar CSV do banco: {e}")
            return []
    
    def load_cartao_csv(self, csv_path: str) -> List[PixTransaction]:
        """
        Carrega transações PIX do CSV do cartão
        """
        self.logger.info(f"Carregando CSV do cartão: {csv_path}")
        
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
                            origem='cartao',
                            identificador=str(row['Identificador']).strip()
                        )
                        transactions.append(transaction)
                        
                    except (ValueError, KeyError) as e:
                        self.logger.warning(f"Erro ao processar linha do cartão: {e}")
                        continue
            
            self.logger.info(f"Carregadas {len(transactions)} transações PIX do cartão")
            return transactions
            
        except Exception as e:
            self.logger.error(f"Erro ao carregar CSV do cartão: {e}")
            return []
    
    def load_recebimentos_excel(self, excel_path: str) -> List[PixTransaction]:
        """
        Carrega transações PIX da tabela de recebimentos
        """
        self.logger.info(f"Carregando Excel de recebimentos: {excel_path}")
        
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
                    self.logger.warning(f"Erro ao processar linha de recebimentos: {e}")
                    continue
            
            self.logger.info(f"Carregadas {len(transactions)} transações PIX dos recebimentos")
            return transactions
            
        except Exception as e:
            self.logger.error(f"Erro ao carregar Excel de recebimentos: {e}")
            return []
    
    def parse_date(self, date_str: str) -> Optional[datetime]:
        """
        Converte string de data para datetime
        """
        try:
            # Tenta diferentes formatos
            formats = ['%d/%m/%Y', '%Y-%m-%d', '%d-%m-%Y']
            for fmt in formats:
                try:
                    return datetime.strptime(date_str, fmt)
                except ValueError:
                    continue
            return None
        except:
            return None
    
    def dates_are_close(self, date1: str, date2: str) -> bool:
        """
        Verifica se duas datas estão próximas (dentro da tolerância)
        """
        dt1 = self.parse_date(date1)
        dt2 = self.parse_date(date2)
        
        if dt1 is None or dt2 is None:
            return False
        
        diff_days = abs((dt1 - dt2).days)
        return diff_days <= self.tolerance_days
    
    def values_are_close(self, val1: float, val2: float) -> bool:
        """
        Verifica se dois valores estão próximos (dentro da tolerância)
        """
        if val1 == 0 and val2 == 0:
            return True
        
        if val1 == 0 or val2 == 0:
            return False
        
        diff_percent = abs(val1 - val2) / max(val1, val2)
        return diff_percent <= self.tolerance_value
    
    def extract_payer_name(self, descricao: str) -> str:
        """
        Extrai o nome do pagador da descrição
        """
        # Padrões comuns para extrair nome do pagador
        patterns = [
            r'- ([^-]+) - \d{3}\.\d{3}\.\d{3}-\d{2}',  # Nome - CPF
            r'- ([^-]+) - \d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}',  # Nome - CNPJ
            r'Transferência recebida pelo Pix - ([^-]+) -',  # Nome após "Transferência recebida"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, descricao)
            if match:
                return match.group(1).strip()
        
        return descricao[:50]  # Retorna primeiros 50 caracteres se não encontrar padrão
    
    def find_matches(self, banco_transactions: List[PixTransaction], 
                    recebimentos_transactions: List[PixTransaction],
                    cartao_transactions: List[PixTransaction]) -> List[AuditMatch]:
        """
        Encontra correspondências entre as transações
        """
        matches = []
        
        for banco_tx in banco_transactions:
            match = AuditMatch(banco_transaction=banco_tx)
            
            # Procura correspondência nos recebimentos
            for rec_tx in recebimentos_transactions:
                if (self.dates_are_close(banco_tx.data, rec_tx.data) and 
                    self.values_are_close(banco_tx.valor, rec_tx.valor)):
                    match.recebimentos_transaction = rec_tx
                    match.confidence = 0.9
                    break
            
            # Procura correspondência no cartão
            for cartao_tx in cartao_transactions:
                if (self.dates_are_close(banco_tx.data, cartao_tx.data) and 
                    self.values_are_close(banco_tx.valor, cartao_tx.valor)):
                    match.cartao_transaction = cartao_tx
                    match.confidence = 0.9
                    break
            
            # Determina tipo de match
            if match.recebimentos_transaction and match.cartao_transaction:
                match.match_type = "completo"
                match.confidence = 1.0
            elif match.recebimentos_transaction or match.cartao_transaction:
                match.match_type = "parcial"
            else:
                match.match_type = "sem_correspondencia"
                match.notes = "Transação do banco sem correspondência nos outros sistemas"
            
            matches.append(match)
        
        return matches
    
    def generate_report(self, matches: List[AuditMatch], output_file: str):
        """
        Gera relatório detalhado da auditoria
        """
        self.logger.info(f"Gerando relatório: {output_file}")
        
        # Filtra apenas as transações do banco sem correspondência
        unmatched = [m for m in matches if m.match_type == "sem_correspondencia"]
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("RELATÓRIO DE AUDITORIA PIX UNIFICADA\n")
            f.write("=" * 80 + "\n")
            f.write(f"Data da auditoria: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n\n")
            f.write("Transações PIX do banco sem correspondência nos recebimentos:\n")
            f.write("-" * 80 + "\n")
            if not unmatched:
                f.write("Todas as transações PIX do banco possuem correspondência nos recebimentos.\n")
            else:
                for match in unmatched:
                    f.write(f"Data: {match.banco_transaction.data} | Valor: R$ {match.banco_transaction.valor:,.2f}\n")
                    f.write(f"Descrição: {match.banco_transaction.descricao}\n")
                    f.write("-" * 80 + "\n")
        
        self.logger.info(f"Relatório gerado com sucesso: {output_file}")
    
    def run_audit(self, banco_csv: str, cartao_csv: str, recebimentos_excel: str, 
                  output_file: str = "auditoria_pix_unificada.txt"):
        """
        Executa a auditoria completa
        """
        self.logger.info("Iniciando auditoria PIX unificada")
        
        # Carrega dados
        banco_transactions = self.load_banco_csv(banco_csv)
        cartao_transactions = self.load_cartao_csv(cartao_csv)
        recebimentos_transactions = self.load_recebimentos_excel(recebimentos_excel)
        
        if not banco_transactions:
            self.logger.error("Nenhuma transação PIX encontrada no banco")
            return
        
        # Encontra correspondências
        matches = self.find_matches(banco_transactions, recebimentos_transactions, cartao_transactions)
        
        # Gera relatório
        self.generate_report(matches, output_file)
        
        self.logger.info("Auditoria PIX unificada concluída")


def main():
    """
    Função principal para executar a auditoria
    """
    # Configurar logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Caminhos dos arquivos
    banco_csv = "data/extratos/NU_636868111_01JUN2025_27JUN2025.csv"
    recebimentos_excel = "data/recebimentos/Recebimentos_2025-06.xlsx"
    
    # Verifica se os arquivos existem
    if not os.path.exists(banco_csv):
        print(f"Arquivo do banco não encontrado: {banco_csv}")
        return
    
    if not os.path.exists(recebimentos_excel):
        print(f"Arquivo de recebimentos não encontrado: {recebimentos_excel}")
        return
    
    # Executa auditoria (sem cartão por enquanto)
    auditor = PixAuditor(tolerance_days=3, tolerance_value=0.01)
    
    # Carrega dados
    banco_transactions = auditor.load_banco_csv(banco_csv)
    recebimentos_transactions = auditor.load_recebimentos_excel(recebimentos_excel)
    
    if not banco_transactions:
        print("Nenhuma transação PIX encontrada no banco")
        return
    
    # Encontra correspondências (sem cartão)
    matches = auditor.find_matches(banco_transactions, recebimentos_transactions, [])
    
    # Gera relatório
    auditor.generate_report(matches, "auditoria_pix_unificada.txt")
    
    print("Auditoria PIX unificada concluída!")
    print(f"Relatório gerado: auditoria_pix_unificada.txt")


if __name__ == "__main__":
    main() 