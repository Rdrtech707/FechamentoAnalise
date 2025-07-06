#!/usr/bin/env python3
"""
Extrator de Notas Fiscais de Serviço (NFSe)
Extrai nomes e valores totais de arquivos PDF de notas fiscais de serviço
"""

import os
import re
import logging
import pandas as pd
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import pdfplumber
from pathlib import Path


class NFSeExtractor:
    """Classe para extrair dados de Notas Fiscais de Serviço (NFSe)"""
    
    def __init__(self, log_level: str = "INFO"):
        """Inicializa o extrator"""
        self.setup_logging(log_level)
        self.logger = logging.getLogger(__name__)
        
        # Padrões para extração de dados
        self.patterns = {
            'numero_nfse': [
                r'N[ºo]:?\s*(\d+/\d+)',
                r'NFSe[\s\-:]*[Nn][ºo]?:?\s*(\d+/\d+)',
                r'Nota Fiscal de Serviços Eletrônica[\s\-:]*N[ºo]?:?\s*(\d+/\d+)',
                r'N[ºo]?:?\s*(\d+/\d+)',
            ],
            'valor_total': [
                r'Valor dos serviços:?\s*R?\$?\s*([\d\.]+,[\d]{2})',
                r'Valor Líquido:?\s*R?\$?\s*([\d\.]+,[\d]{2})',
                r'Valor Total dos Serviços[\s\-:]*R?\$?\s*([\d\.]+,[\d]{2})',
                r'Valor Total[\s\-:]*R?\$?\s*([\d\.]+,[\d]{2})',
                r'Total[\s\-:]*R?\$?\s*([\d\.]+,[\d]{2})',
                r'R?\$?\s*([\d\.]+,[\d]{2})',
            ],
            'nome_tomador': [
                r'Tomador do\(s\) Serviço\(s\)[^\n]*\nCPF/CNPJ:[^\n]*\n([^\n]+)',
                r'Tomador[\s\-:]*([^\n\r]+)',
                r'Cliente[\s\-:]*([^\n\r]+)',
                r'Nome[\s\-:]*([^\n\r]+)',
                r'Razão Social[\s\-:]*([^\n\r]+)',
            ],
            'cnpj_cpf': [
                r'CPF/CNPJ:\s*([\d.-]+)',
                r'CNPJ[:\s]*(\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2})',
                r'CPF[:\s]*(\d{3}\.?\d{3}\.?\d{3}-?\d{2})',
                r'(\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2})',  # CNPJ
                r'(\d{3}\.?\d{3}\.?\d{3}-?\d{2})',  # CPF
            ],
            'data_emissao': [
                r'Data de Emissão[:\s]*(\d{2}/\d{2}/\d{4})',
                r'Emissão[:\s]*(\d{2}/\d{2}/\d{4})',
                r'(\d{2}/\d{2}/\d{4})',  # Data no formato DD/MM/AAAA
            ],
            'descricao_servico': [
                r'Descrição do Serviço[:\s]*([^\n\r]+)',
                r'Serviço[:\s]*([^\n\r]+)',
                r'Descrição[:\s]*([^\n\r]+)',
            ]
        }
    
    def setup_logging(self, level: str):
        """Configura o sistema de logging"""
        logging.basicConfig(
            level=getattr(logging, level.upper()),
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('nfse_extractor.log', encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """
        Extrai texto de um arquivo PDF
        
        Args:
            pdf_path: Caminho para o arquivo PDF
            
        Returns:
            str: Texto extraído do PDF
        """
        try:
            self.logger.info(f"Extraindo texto do PDF: {pdf_path}")
            
            text = ""
            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages, 1):
                    self.logger.debug(f"Processando página {page_num}")
                    page_text = page.extract_text()
                    if page_text:
                        text += f"\n--- PÁGINA {page_num} ---\n"
                        text += page_text
                        text += "\n"
            
            self.logger.info(f"Texto extraído com sucesso: {len(text)} caracteres")
            return text
            
        except Exception as e:
            error_msg = f"Erro ao extrair texto do PDF {pdf_path}: {e}"
            self.logger.error(error_msg)
            raise Exception(error_msg)
    
    def extract_value_with_patterns(self, text: str, pattern_key: str) -> Optional[str]:
        """
        Extrai valor usando múltiplos padrões
        
        Args:
            text: Texto para extrair
            pattern_key: Chave do padrão a usar
            
        Returns:
            str: Valor extraído ou None
        """
        patterns = self.patterns.get(pattern_key, [])
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                value = match.group(1).strip()
                if value:
                    self.logger.debug(f"Encontrado {pattern_key}: {value}")
                    return value
        
        return None
    
    def clean_value(self, value: str, value_type: str) -> str:
        """
        Limpa e formata valores extraídos
        
        Args:
            value: Valor a ser limpo
            value_type: Tipo do valor (valor_total, cnpj_cpf, etc.)
            
        Returns:
            str: Valor limpo
        """
        if not value:
            return ""
        
        value = value.strip()
        
        if value_type == 'valor_total':
            # Remove caracteres não numéricos exceto vírgula e ponto
            value = re.sub(r'[^\d,\.]', '', value)
            # Troca ponto por nada e vírgula por ponto para float
            value = value.replace('.', '').replace(',', '.')
        
        elif value_type == 'cnpj_cpf':
            # Remove caracteres não numéricos
            value = re.sub(r'[^\d]', '', value)
        
        elif value_type == 'nome_tomador':
            # Remove caracteres especiais e normaliza espaços
            value = re.sub(r'[^\w\sÁÉÍÓÚÂÊÎÔÛÃÕÇáéíóúâêîôûãõç]', '', value)
            value = re.sub(r'\s+', ' ', value)
        
        return value.strip()
    
    def extract_nfse_data(self, pdf_path: str) -> dict:
        """
        Extrai dados de uma NFSe do PDF
        
        Args:
            pdf_path: Caminho para o arquivo PDF
            
        Returns:
            dict: Dicionário com os dados extraídos
        """
        try:
            self.logger.info(f"Processando NFSe: {pdf_path}")
            
            # Extrai texto do PDF
            texto = self.extract_text_from_pdf(pdf_path)
            
            # Extrai dados usando regex
            numero_nfse = self.extract_value_with_patterns(texto, 'numero_nfse')
            nome_tomador = self.extract_value_with_patterns(texto, 'nome_tomador')
            valor_total_text = self.extract_value_with_patterns(texto, 'valor_total')
            data_emissao = self.extract_value_with_patterns(texto, 'data_emissao')
            
            # Converte valor_total para float
            valor_total = None
            if valor_total_text:
                try:
                    # Remove caracteres não numéricos exceto vírgula e ponto
                    valor_limpo = re.sub(r'[^\d,\.]', '', valor_total_text)
                    # Troca ponto por nada e vírgula por ponto para float
                    valor_limpo = valor_limpo.replace('.', '').replace(',', '.')
                    valor_total = float(valor_limpo)
                except (ValueError, AttributeError):
                    self.logger.warning(f"Erro ao converter valor_total '{valor_total_text}' para float")
                    valor_total = None
            
            # Cria dicionário com dados essenciais
            dados = {
                'numero_nfse': numero_nfse,
                'nome_tomador': nome_tomador,
                'valor_total': valor_total,
                'data_emissao': data_emissao
            }
            
            self.logger.info(f"Dados extraídos: {dados}")
            return dados
            
        except Exception as e:
            error_msg = f"Erro ao extrair dados de {pdf_path}: {e}"
            self.logger.error(error_msg)
            raise Exception(error_msg)
    
    def process_directory(self, directory_path: str) -> pd.DataFrame:
        """
        Processa todos os PDFs em um diretório
        
        Args:
            directory_path: Caminho para o diretório
            
        Returns:
            pd.DataFrame: DataFrame com dados extraídos
        """
        try:
            self.logger.info(f"Processando diretório: {directory_path}")
            
            # Encontra todos os arquivos PDF (evita duplicatas)
            pdf_files = set()
            for ext in ['*.pdf', '*.PDF']:
                pdf_files.update(Path(directory_path).glob(ext))
            
            # Converte para lista e ordena
            pdf_files = sorted(list(pdf_files))
            
            if not pdf_files:
                self.logger.warning(f"Nenhum arquivo PDF encontrado em: {directory_path}")
                return pd.DataFrame()
            
            self.logger.info(f"Encontrados {len(pdf_files)} arquivos PDF únicos")
            
            # Processa cada arquivo
            results = []
            processed_files = set()  # Para evitar duplicatas
            
            for pdf_file in pdf_files:
                if str(pdf_file) in processed_files:
                    self.logger.warning(f"Arquivo já processado, pulando: {pdf_file}")
                    continue
                    
                try:
                    data = self.extract_nfse_data(str(pdf_file))
                    results.append(data)
                    processed_files.add(str(pdf_file))
                except Exception as e:
                    self.logger.error(f"Erro ao processar {pdf_file}: {e}")
                    results.append({
                        'numero_nfse': None,
                        'nome_tomador': None,
                        'valor_total': None,
                        'data_emissao': None
                    })
                    processed_files.add(str(pdf_file))
            
            # Cria DataFrame
            df = pd.DataFrame(results)
            
            # Converte valor_total para float se ainda não estiver
            if 'valor_total' in df.columns:
                df['valor_total'] = pd.to_numeric(df['valor_total'], errors='coerce')
            
            # Reordena colunas
            column_order = ['numero_nfse', 'nome_tomador', 'valor_total', 'data_emissao']
            df = df[[col for col in column_order if col in df.columns]]
            
            self.logger.info(f"Processamento concluído: {len(df)} registros únicos")
            return df
            
        except Exception as e:
            error_msg = f"Erro ao processar diretório {directory_path}: {e}"
            self.logger.error(error_msg)
            raise Exception(error_msg)
    
    def save_results(self, df: pd.DataFrame, output_path: str):
        """
        Salva resultados em arquivo Excel
        
        Args:
            df: DataFrame com resultados
            output_path: Caminho para salvar
        """
        try:
            self.logger.info(f"Salvando resultados em: {output_path}")
            
            # Garante que o diretório existe
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Salva em Excel
            with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='NFSe_Extraidas', index=False)
                
                # Cria planilha de resumo
                summary_data = {
                    'Métrica': [
                        'Total de arquivos processados',
                        'Arquivos com sucesso',
                        'Arquivos com erro',
                        'Total de valores extraídos',
                        'Valor total das NFSe',
                        'Data do processamento'
                    ],
                    'Valor': [
                        len(df),
                        len(df[df['numero_nfse'].notna()]),
                        len(df[df['numero_nfse'].isna()]),
                        len(df[df['valor_total'].notna()]),
                        df[df['valor_total'].notna()]['valor_total'].sum() if len(df[df['valor_total'].notna()]) > 0 else 0,
                        datetime.now().strftime('%d/%m/%Y %H:%M:%S')
                    ]
                }
                
                summary_df = pd.DataFrame(summary_data)
                summary_df.to_excel(writer, sheet_name='Resumo', index=False)
            
            self.logger.info(f"Resultados salvos com sucesso: {output_path}")
            
        except Exception as e:
            error_msg = f"Erro ao salvar resultados: {e}"
            self.logger.error(error_msg)
            raise Exception(error_msg)


def main():
    """Função principal"""
    try:
        # Configura logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        
        # Cria extrator
        extrator = NFSeExtractor()
        
        # Processa diretório
        directory_path = "data/06-JUN"
        df = extrator.process_directory(directory_path)
        
        if df.empty:
            print("Nenhum arquivo PDF encontrado para processar.")
            return
        
        # Calcula totais
        total_arquivos = len(df)
        arquivos_sucesso = len(df[df['numero_nfse'].notna()])
        arquivos_erro = total_arquivos - arquivos_sucesso
        
        # Calcula valor total (já está como float)
        valores_validos = df[df['valor_total'].notna()]['valor_total']
        valor_total = valores_validos.sum()
        
        # Salva resultados
        output_file = "data/relatorios/nfse_extraidas.xlsx"
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        df.to_excel(output_file, index=False)
        extrator.logger.info(f"Resultados salvos com sucesso: {output_file}")
        
        # Exibe resumo
        print("\n=== RESUMO DA EXTRAÇÃO ===")
        print(f"Total de arquivos processados: {total_arquivos}")
        print(f"Arquivos com sucesso: {arquivos_sucesso}")
        print(f"Arquivos com erro: {arquivos_erro}")
        print(f"Valor total das NFSe: R$ {valor_total:,.2f}")
        print(f"\nArquivo de saída: {output_file}")
        
        # Mostra primeiras linhas
        print(f"\n=== PRIMEIRAS 5 LINHAS ===")
        print(df.head().to_string(index=False))
        
    except Exception as e:
        print(f"Erro: {e}")
        logging.error(f"Erro na execução: {e}")


if __name__ == "__main__":
    main() 