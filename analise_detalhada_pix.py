"""
Análise Detalhada PIX - Mostra transações do banco e recebimentos lado a lado
para identificar possíveis correspondências e investigar divergências
"""

import pandas as pd
import logging
from datetime import datetime
import os
from typing import List, Dict, Optional
from dataclasses import dataclass


@dataclass
class PixTransaction:
    """Representa uma transação PIX"""
    data: str
    valor: float
    descricao: str
    origem: str
    identificador: Optional[str] = None
    referencia: Optional[str] = None


class PixAnalyzer:
    """
    Analisador detalhado de transações PIX
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Configurar logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    def load_banco_csv(self, csv_path: str) -> List[PixTransaction]:
        """Carrega transações PIX do CSV do banco"""
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
    
    def load_recebimentos_excel(self, excel_path: str) -> List[PixTransaction]:
        """Carrega transações PIX da tabela de recebimentos"""
        self.logger.info(f"Carregando Excel de recebimentos: {excel_path}")
        
        try:
            df = pd.read_excel(excel_path)
            transactions = []
            
            # Mostra as colunas disponíveis
            self.logger.info(f"Colunas disponíveis no Excel: {list(df.columns)}")
            
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
    
    def parse_date(self, date_str: str) -> datetime:
        """Converte string de data para datetime"""
        try:
            # Tenta diferentes formatos
            formats = ['%d/%m/%Y', '%Y-%m-%d', '%d-%m-%Y', '%d/%m/%y']
            for fmt in formats:
                try:
                    return datetime.strptime(date_str, fmt)
                except ValueError:
                    continue
            return None
        except:
            return None
    
    def generate_detailed_report(self, banco_transactions: List[PixTransaction], 
                               recebimentos_transactions: List[PixTransaction], 
                               output_file: str):
        """Gera relatório detalhado comparando as transações"""
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("=" * 100 + "\n")
            f.write("ANÁLISE DETALHADA PIX - BANCO vs RECEBIMENTOS\n")
            f.write("=" * 100 + "\n")
            f.write(f"Data da análise: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n\n")
            
            # Resumo estatístico
            f.write("RESUMO ESTATÍSTICO\n")
            f.write("-" * 50 + "\n")
            f.write(f"Total de transações PIX do banco: {len(banco_transactions)}\n")
            f.write(f"Total de transações PIX dos recebimentos: {len(recebimentos_transactions)}\n")
            f.write(f"Valor total PIX do banco: R$ {sum(t.valor for t in banco_transactions):,.2f}\n")
            f.write(f"Valor total PIX dos recebimentos: R$ {sum(t.valor for t in recebimentos_transactions):,.2f}\n\n")
            
            # Transações do banco
            f.write("TRANSAÇÕES PIX DO BANCO\n")
            f.write("-" * 50 + "\n")
            for i, tx in enumerate(banco_transactions, 1):
                f.write(f"{i:2d}. {tx.data} - R$ {tx.valor:10,.2f} - {tx.descricao[:80]}...\n")
            f.write("\n")
            
            # Transações dos recebimentos
            f.write("TRANSAÇÕES PIX DOS RECEBIMENTOS\n")
            f.write("-" * 50 + "\n")
            for i, tx in enumerate(recebimentos_transactions, 1):
                f.write(f"{i:2d}. {tx.data} - R$ {tx.valor:10,.2f} - {tx.descricao}\n")
            f.write("\n")
            
            # Análise de valores
            f.write("ANÁLISE DE VALORES\n")
            f.write("-" * 50 + "\n")
            
            valores_banco = [tx.valor for tx in banco_transactions]
            valores_recebimentos = [tx.valor for tx in recebimentos_transactions]
            
            f.write("Valores únicos do banco:\n")
            for valor in sorted(set(valores_banco)):
                f.write(f"  R$ {valor:10,.2f}\n")
            f.write("\n")
            
            f.write("Valores únicos dos recebimentos:\n")
            for valor in sorted(set(valores_recebimentos)):
                f.write(f"  R$ {valor:10,.2f}\n")
            f.write("\n")
            
            # Análise de datas
            f.write("ANÁLISE DE DATAS\n")
            f.write("-" * 50 + "\n")
            
            datas_banco = [tx.data for tx in banco_transactions]
            datas_recebimentos = [tx.data for tx in recebimentos_transactions]
            
            f.write("Datas únicas do banco:\n")
            for data in sorted(set(datas_banco)):
                f.write(f"  {data}\n")
            f.write("\n")
            
            f.write("Datas únicas dos recebimentos:\n")
            for data in sorted(set(datas_recebimentos)):
                f.write(f"  {data}\n")
            f.write("\n")
            
            # Tentativa de correspondência por valor
            f.write("TENTATIVA DE CORRESPONDÊNCIA POR VALOR\n")
            f.write("-" * 50 + "\n")
            
            for banco_tx in banco_transactions:
                f.write(f"\nValor do banco: R$ {banco_tx.valor:,.2f} ({banco_tx.data})\n")
                matches = [rec_tx for rec_tx in recebimentos_transactions if abs(rec_tx.valor - banco_tx.valor) < 0.01]
                
                if matches:
                    f.write("  ✓ Correspondências encontradas:\n")
                    for match in matches:
                        f.write(f"    - R$ {match.valor:,.2f} ({match.data}) - {match.descricao}\n")
                else:
                    f.write("  ✗ Nenhuma correspondência encontrada\n")
            
            # Análise de diferenças
            f.write("\nANÁLISE DE DIFERENÇAS\n")
            f.write("-" * 50 + "\n")
            
            valor_total_banco = sum(t.valor for t in banco_transactions)
            valor_total_recebimentos = sum(t.valor for t in recebimentos_transactions)
            diferenca = valor_total_banco - valor_total_recebimentos
            
            f.write(f"Valor total banco: R$ {valor_total_banco:,.2f}\n")
            f.write(f"Valor total recebimentos: R$ {valor_total_recebimentos:,.2f}\n")
            f.write(f"Diferença: R$ {diferenca:,.2f}\n")
            f.write(f"Percentual de diferença: {(diferenca/valor_total_banco*100):.2f}%\n")
        
        self.logger.info(f"Relatório detalhado gerado: {output_file}")


def main():
    """Função principal"""
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
    
    # Executa análise
    analyzer = PixAnalyzer()
    
    # Carrega dados
    banco_transactions = analyzer.load_banco_csv(banco_csv)
    recebimentos_transactions = analyzer.load_recebimentos_excel(recebimentos_excel)
    
    if not banco_transactions:
        print("Nenhuma transação PIX encontrada no banco")
        return
    
    # Gera relatório detalhado
    analyzer.generate_detailed_report(banco_transactions, recebimentos_transactions, 
                                    "analise_detalhada_pix.txt")
    
    print("Análise detalhada concluída!")
    print("Relatório gerado: analise_detalhada_pix.txt")


if __name__ == "__main__":
    main() 