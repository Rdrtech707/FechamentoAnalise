"""
Módulo de Auditoria - Compara dados CSV com dados gerados pela aplicação
"""

import pandas as pd
import logging
from typing import Dict, List, Tuple, Any, Optional
from datetime import datetime
import os
from dataclasses import dataclass


@dataclass
class AuditResult:
    """Resultado de uma auditoria individual"""
    field_name: str
    csv_value: Any
    generated_value: Any
    is_match: bool
    difference: Optional[float] = None
    percentage_diff: Optional[float] = None
    notes: str = ""


@dataclass
class AuditSummary:
    """Resumo geral da auditoria"""
    total_records: int
    matching_records: int
    mismatched_records: int
    total_fields_checked: int
    matching_fields: int
    mismatched_fields: int
    audit_date: datetime
    csv_file: str
    generated_file: str
    tolerance_percentage: float = 0.01  # 1% de tolerância por padrão


class AuditError(Exception):
    """Exceção personalizada para erros de auditoria"""
    pass


class DataAuditor:
    """
    Classe principal para auditoria de dados CSV contra dados gerados
    """
    
    def __init__(self, tolerance_percentage: float = 0.01):
        """
        Inicializa o auditor
        
        Args:
            tolerance_percentage: Percentual de tolerância para comparações numéricas (padrão: 1%)
        """
        self.tolerance_percentage = tolerance_percentage
        self.logger = logging.getLogger(__name__)
    
    def load_csv_data(self, csv_file_path: str) -> pd.DataFrame:
        """
        Carrega dados do arquivo CSV
        
        Args:
            csv_file_path: Caminho para o arquivo CSV
            
        Returns:
            pd.DataFrame: Dados carregados do CSV
            
        Raises:
            AuditError: Se houver erro ao carregar o arquivo
        """
        try:
            self.logger.info(f"Carregando dados CSV: {csv_file_path}")
            
            # Tenta diferentes encodings
            encodings = ['utf-8', 'latin1', 'cp1252']
            df = None
            
            for encoding in encodings:
                try:
                    df = pd.read_csv(csv_file_path, encoding=encoding)
                    self.logger.info(f"CSV carregado com encoding: {encoding}")
                    break
                except UnicodeDecodeError:
                    continue
                except pd.errors.EmptyDataError:
                    # DataFrame vazio - cria um DataFrame vazio com colunas padrão
                    self.logger.warning(f"Arquivo CSV vazio: {csv_file_path}")
                    df = pd.DataFrame(columns=['N° OS'])  # Coluna mínima necessária
                    break
            
            if df is None:
                raise AuditError(f"Não foi possível carregar o arquivo CSV: {csv_file_path}")
            
            self.logger.info(f"CSV carregado com sucesso: {len(df)} registros, {len(df.columns)} colunas")
            return df
            
        except Exception as e:
            error_msg = f"Erro ao carregar arquivo CSV {csv_file_path}: {e}"
            self.logger.error(error_msg)
            raise AuditError(error_msg)
    
    def load_generated_data(self, excel_file_path: str, sheet_name: str = None) -> pd.DataFrame:
        """
        Carrega dados do arquivo Excel gerado pela aplicação
        
        Args:
            excel_file_path: Caminho para o arquivo Excel
            sheet_name: Nome da planilha (se None, usa a primeira)
            
        Returns:
            pd.DataFrame: Dados carregados do Excel
            
        Raises:
            AuditError: Se houver erro ao carregar o arquivo
        """
        try:
            self.logger.info(f"Carregando dados Excel: {excel_file_path}")
            
            if sheet_name:
                df = pd.read_excel(excel_file_path, sheet_name=sheet_name)
            else:
                # Lê a primeira planilha
                excel_file = pd.ExcelFile(excel_file_path)
                sheet_name = excel_file.sheet_names[0]
                df = pd.read_excel(excel_file_path, sheet_name=sheet_name)
            
            self.logger.info(f"Excel carregado com sucesso: {len(df)} registros, {len(df.columns)} colunas")
            self.logger.info(f"Planilha utilizada: {sheet_name}")
            
            return df
            
        except Exception as e:
            error_msg = f"Erro ao carregar arquivo Excel {excel_file_path}: {e}"
            self.logger.error(error_msg)
            raise AuditError(error_msg)
    
    def normalize_column_names(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Normaliza nomes das colunas para facilitar comparação
        
        Args:
            df: DataFrame a ser normalizado
            
        Returns:
            pd.DataFrame: DataFrame com colunas normalizadas
        """
        df_normalized = df.copy()
        
        # Mapeamento de normalização
        normalization_map = {
            'N° OS': ['N_OS', 'N° OS', 'NUMERO_OS', 'OS', 'numero_os'],
            'DATA PGTO': ['DATA_PGTO', 'DATA PGTO', 'DATA_PAGAMENTO', 'data_pagamento'],
            'VALOR TOTAL': ['VALOR_TOTAL', 'VALOR TOTAL', 'TOTAL', 'valor_total'],
            'VALOR PAGO': ['VALOR_PAGO', 'VALOR PAGO', 'PAGO', 'valor_pago'],
            'CÓDIGO CLIENTE': ['CODIGO_CLIENTE', 'CÓDIGO CLIENTE', 'CLIENTE', 'codigo_cliente'],
            'VEÍCULO (PLACA)': ['VEICULO_PLACA', 'VEÍCULO (PLACA)', 'PLACA', 'placa_veiculo']
        }
        
        # Aplica normalização
        for standard_name, variations in normalization_map.items():
            for col in df_normalized.columns:
                if col in variations:
                    df_normalized = df_normalized.rename(columns={col: standard_name})
                    break
        
        return df_normalized
    
    def compare_numeric_values(self, value1: Any, value2: Any, field_name: str) -> AuditResult:
        """
        Compara valores numéricos com tolerância
        
        Args:
            value1: Primeiro valor (CSV)
            value2: Segundo valor (gerado)
            field_name: Nome do campo sendo comparado
            
        Returns:
            AuditResult: Resultado da comparação
        """
        try:
            # Converte para float
            val1 = float(value1) if pd.notna(value1) else 0.0
            val2 = float(value2) if pd.notna(value2) else 0.0
            
            # Calcula diferença
            difference = abs(val1 - val2)
            percentage_diff = (difference / max(val1, val2)) * 100 if max(val1, val2) > 0 else 0
            
            # Verifica se está dentro da tolerância
            is_match = percentage_diff <= (self.tolerance_percentage * 100)
            
            notes = f"Diferença: {difference:.2f} ({percentage_diff:.2f}%)"
            if not is_match:
                notes += f" - Excede tolerância de {self.tolerance_percentage * 100:.2f}%"
            
            return AuditResult(
                field_name=field_name,
                csv_value=val1,
                generated_value=val2,
                is_match=is_match,
                difference=difference,
                percentage_diff=percentage_diff,
                notes=notes
            )
            
        except (ValueError, TypeError) as e:
            return AuditResult(
                field_name=field_name,
                csv_value=value1,
                generated_value=value2,
                is_match=False,
                notes=f"Erro na conversão numérica: {e}"
            )
    
    def compare_text_values(self, value1: Any, value2: Any, field_name: str) -> AuditResult:
        """
        Compara valores de texto
        
        Args:
            value1: Primeiro valor (CSV)
            value2: Segundo valor (gerado)
            field_name: Nome do campo sendo comparado
            
        Returns:
            AuditResult: Resultado da comparação
        """
        # Normaliza valores
        str1 = str(value1).strip().upper() if pd.notna(value1) else ""
        str2 = str(value2).strip().upper() if pd.notna(value2) else ""
        
        is_match = str1 == str2
        notes = "Valores idênticos" if is_match else f"CSV: '{str1}' vs Gerado: '{str2}'"
        
        return AuditResult(
            field_name=field_name,
            csv_value=str1,
            generated_value=str2,
            is_match=is_match,
            notes=notes
        )
    
    def compare_date_values(self, value1: Any, value2: Any, field_name: str) -> AuditResult:
        """
        Compara valores de data
        
        Args:
            value1: Primeiro valor (CSV)
            value2: Segundo valor (gerado)
            field_name: Nome do campo sendo comparado
            
        Returns:
            AuditResult: Resultado da comparação
        """
        try:
            # Converte para datetime
            date1 = pd.to_datetime(value1) if pd.notna(value1) else None
            date2 = pd.to_datetime(value2) if pd.notna(value2) else None
            
            is_match = date1 == date2
            notes = "Datas idênticas" if is_match else f"CSV: {date1} vs Gerado: {date2}"
            
            return AuditResult(
                field_name=field_name,
                csv_value=date1,
                generated_value=date2,
                is_match=is_match,
                notes=notes
            )
            
        except Exception as e:
            return AuditResult(
                field_name=field_name,
                csv_value=value1,
                generated_value=value2,
                is_match=False,
                notes=f"Erro na conversão de data: {e}"
            )
    
    def audit_record(self, csv_row: pd.Series, generated_row: pd.Series, 
                    field_mappings: Dict[str, str]) -> List[AuditResult]:
        """
        Audita um registro individual
        
        Args:
            csv_row: Linha do CSV
            generated_row: Linha dos dados gerados
            field_mappings: Mapeamento de campos CSV -> Gerado
            
        Returns:
            List[AuditResult]: Lista de resultados da auditoria
        """
        results = []
        
        for csv_field, generated_field in field_mappings.items():
            if csv_field not in csv_row.index:
                results.append(AuditResult(
                    field_name=csv_field,
                    csv_value=None,
                    generated_value=None,
                    is_match=False,
                    notes=f"Campo '{csv_field}' não encontrado no CSV"
                ))
                continue
            
            if generated_field not in generated_row.index:
                results.append(AuditResult(
                    field_name=generated_field,
                    csv_value=csv_row[csv_field],
                    generated_value=None,
                    is_match=False,
                    notes=f"Campo '{generated_field}' não encontrado nos dados gerados"
                ))
                continue
            
            csv_value = csv_row[csv_field]
            generated_value = generated_row[generated_field]
            
            # Determina tipo de comparação baseado no nome do campo
            if any(keyword in generated_field.upper() for keyword in ['VALOR', 'PAGO', 'DEVEDOR', 'CARTÃO', 'DINHEIRO', 'PIX', 'TROCO']):
                result = self.compare_numeric_values(csv_value, generated_value, generated_field)
            elif any(keyword in generated_field.upper() for keyword in ['DATA']):
                result = self.compare_date_values(csv_value, generated_value, generated_field)
            else:
                result = self.compare_text_values(csv_value, generated_value, generated_field)
            
            results.append(result)
        
        return results
    
    def audit_data(self, csv_file_path: str, generated_file_path: str, 
                   field_mappings: Dict[str, str], key_field: str = 'N° OS') -> AuditSummary:
        """
        Executa auditoria completa dos dados
        
        Args:
            csv_file_path: Caminho para o arquivo CSV
            generated_file_path: Caminho para o arquivo Excel gerado
            field_mappings: Mapeamento de campos CSV -> Gerado
            key_field: Campo chave para relacionar registros
            
        Returns:
            AuditSummary: Resumo da auditoria
            
        Raises:
            AuditError: Se houver erro na auditoria
        """
        try:
            self.logger.info("Iniciando auditoria de dados...")
            
            # Carrega dados
            csv_df = self.load_csv_data(csv_file_path)
            generated_df = self.load_generated_data(generated_file_path)
            
            # Normaliza nomes das colunas
            csv_df = self.normalize_column_names(csv_df)
            generated_df = self.normalize_column_names(generated_df)
            
            # Determina o campo chave normalizado
            normalized_key_field = None
            for standard_name, variations in [
                ('N° OS', ['N_OS', 'N° OS', 'NUMERO_OS', 'OS', 'numero_os']),
                ('DATA PGTO', ['DATA_PGTO', 'DATA PGTO', 'DATA_PAGAMENTO', 'data_pagamento']),
                ('VALOR TOTAL', ['VALOR_TOTAL', 'VALOR TOTAL', 'TOTAL', 'valor_total']),
                ('VALOR PAGO', ['VALOR_PAGO', 'VALOR PAGO', 'PAGO', 'valor_pago']),
                ('CÓDIGO CLIENTE', ['CODIGO_CLIENTE', 'CÓDIGO CLIENTE', 'CLIENTE', 'codigo_cliente']),
                ('VEÍCULO (PLACA)', ['VEICULO_PLACA', 'VEÍCULO (PLACA)', 'PLACA', 'placa_veiculo'])
            ]:
                if key_field in variations:
                    normalized_key_field = standard_name
                    break
            
            if normalized_key_field is None:
                normalized_key_field = key_field
            
            # Verifica se o campo chave existe
            if normalized_key_field not in csv_df.columns:
                raise AuditError(f"Campo chave '{key_field}' (normalizado: '{normalized_key_field}') não encontrado no CSV. Colunas disponíveis: {list(csv_df.columns)}")
            if normalized_key_field not in generated_df.columns:
                raise AuditError(f"Campo chave '{key_field}' (normalizado: '{normalized_key_field}') não encontrado nos dados gerados. Colunas disponíveis: {list(generated_df.columns)}")
            
            # Executa auditoria
            all_results = []
            matching_records = 0
            mismatched_records = 0
            
            for _, csv_row in csv_df.iterrows():
                key_value = csv_row[normalized_key_field]
                
                # Encontra registro correspondente nos dados gerados
                matching_generated = generated_df[generated_df[normalized_key_field] == key_value]
                
                if len(matching_generated) == 0:
                    # Registro não encontrado nos dados gerados
                    mismatched_records += 1
                    for csv_field, generated_field in field_mappings.items():
                        all_results.append(AuditResult(
                            field_name=generated_field,
                            csv_value=csv_row.get(csv_field),
                            generated_value=None,
                            is_match=False,
                            notes=f"Registro com {normalized_key_field}={key_value} não encontrado nos dados gerados"
                        ))
                else:
                    # Registro encontrado - compara campos
                    generated_row = matching_generated.iloc[0]
                    record_results = self.audit_record(csv_row, generated_row, field_mappings)
                    all_results.extend(record_results)
                    
                    # Verifica se todos os campos do registro coincidem
                    record_matches = all(result.is_match for result in record_results)
                    if record_matches:
                        matching_records += 1
                    else:
                        mismatched_records += 1
            
            # Calcula estatísticas
            total_records = len(csv_df)
            total_fields_checked = len(all_results)
            matching_fields = sum(1 for result in all_results if result.is_match)
            mismatched_fields = total_fields_checked - matching_fields
            
            # Cria resumo
            summary = AuditSummary(
                total_records=total_records,
                matching_records=matching_records,
                mismatched_records=mismatched_records,
                total_fields_checked=total_fields_checked,
                matching_fields=matching_fields,
                mismatched_fields=mismatched_fields,
                audit_date=datetime.now(),
                csv_file=csv_file_path,
                generated_file=generated_file_path,
                tolerance_percentage=self.tolerance_percentage
            )
            
            self.logger.info("Auditoria concluída com sucesso")
            self.logger.info(f"Resumo: {matching_records}/{total_records} registros coincidem")
            self.logger.info(f"Campos: {matching_fields}/{total_fields_checked} campos coincidem")
            
            return summary, all_results
            
        except Exception as e:
            error_msg = f"Erro durante auditoria: {e}"
            self.logger.error(error_msg)
            raise AuditError(error_msg)
    
    def generate_audit_report(self, summary: AuditSummary, results: List[AuditResult], 
                            output_file: str) -> None:
        """
        Gera relatório detalhado da auditoria
        
        Args:
            summary: Resumo da auditoria
            results: Resultados detalhados
            output_file: Arquivo de saída para o relatório
        """
        try:
            self.logger.info(f"Gerando relatório de auditoria: {output_file}")
            
            # Cria relatório em Excel
            with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
                # Resumo
                summary_data = {
                    'Métrica': [
                        'Total de Registros',
                        'Registros Coincidentes',
                        'Registros Divergentes',
                        'Total de Campos Verificados',
                        'Campos Coincidentes',
                        'Campos Divergentes',
                        'Taxa de Sucesso (Registros)',
                        'Taxa de Sucesso (Campos)',
                        'Data da Auditoria',
                        'Arquivo CSV',
                        'Arquivo Gerado',
                        'Tolerância (%)'
                    ],
                    'Valor': [
                        summary.total_records,
                        summary.matching_records,
                        summary.mismatched_records,
                        summary.total_fields_checked,
                        summary.matching_fields,
                        summary.mismatched_fields,
                        f"{(summary.matching_records/summary.total_records)*100:.2f}%" if summary.total_records > 0 else "0%",
                        f"{(summary.matching_fields/summary.total_fields_checked)*100:.2f}%" if summary.total_fields_checked > 0 else "0%",
                        summary.audit_date.strftime('%d/%m/%Y %H:%M:%S'),
                        summary.csv_file,
                        summary.generated_file,
                        f"{summary.tolerance_percentage*100:.2f}%"
                    ]
                }
                
                summary_df = pd.DataFrame(summary_data)
                summary_df.to_excel(writer, sheet_name='Resumo', index=False)
                
                # Detalhes
                details_data = []
                for result in results:
                    details_data.append({
                        'Campo': result.field_name,
                        'Valor CSV': result.csv_value,
                        'Valor Gerado': result.generated_value,
                        'Coincide': 'Sim' if result.is_match else 'Não',
                        'Diferença': result.difference,
                        'Diferença (%)': result.percentage_diff,
                        'Observações': result.notes
                    })
                
                details_df = pd.DataFrame(details_data)
                details_df.to_excel(writer, sheet_name='Detalhes', index=False)
                
                # Campos com divergências
                divergences = [r for r in results if not r.is_match]
                if divergences:
                    divergence_data = []
                    for result in divergences:
                        divergence_data.append({
                            'Campo': result.field_name,
                            'Valor CSV': result.csv_value,
                            'Valor Gerado': result.generated_value,
                            'Diferença': result.difference,
                            'Diferença (%)': result.percentage_diff,
                            'Observações': result.notes
                        })
                    
                    divergence_df = pd.DataFrame(divergence_data)
                    divergence_df.to_excel(writer, sheet_name='Divergências', index=False)
            
            self.logger.info(f"Relatório gerado com sucesso: {output_file}")
            
        except Exception as e:
            error_msg = f"Erro ao gerar relatório: {e}"
            self.logger.error(error_msg)
            raise AuditError(error_msg) 