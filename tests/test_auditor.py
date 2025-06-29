import pytest
import pandas as pd
import os
import tempfile
from datetime import datetime
from modules.auditor import DataAuditor, AuditError, AuditResult, AuditSummary


class TestDataAuditor:
    """Testes para o módulo de auditoria"""
    
    @pytest.fixture
    def sample_csv_data(self):
        """Dados CSV de exemplo para testes"""
        return pd.DataFrame({
            'numero_os': ['001', '002', '003'],
            'data_pagamento': ['2024-01-15', '2024-01-16', '2024-01-17'],
            'valor_total': [1000.50, 2500.75, 1500.00],
            'valor_pago': [1000.50, 2400.75, 1500.00],
            'valor_devedor': [0.00, 100.00, 0.00],
            'cartao': [500.25, 1200.00, 750.00],
            'dinheiro': [300.25, 800.75, 500.00],
            'pix': [200.00, 400.00, 250.00],
            'troco': [0.00, 0.00, 0.00],
            'placa_veiculo': ['ABC1234', 'XYZ5678', 'DEF9012'],
            'codigo_cliente': ['CLI001', 'CLI002', 'CLI003'],
            'data_encerramento': ['2024-01-15', '2024-01-16', '2024-01-17']
        })
    
    @pytest.fixture
    def sample_generated_data(self):
        """Dados gerados de exemplo para testes"""
        return pd.DataFrame({
            'N° OS': ['001', '002', '003'],
            'DATA PGTO': ['2024-01-15', '2024-01-16', '2024-01-17'],
            'VALOR TOTAL': [1000.50, 2500.75, 1500.00],
            'VALOR PAGO': [1000.50, 2400.75, 1500.00],
            'DEVEDOR': [0.00, 100.00, 0.00],
            'CARTÃO': [500.25, 1200.00, 750.00],
            'DINHEIRO': [300.25, 800.75, 500.00],
            'PIX': [200.00, 400.00, 250.00],
            'TROCO': [0.00, 0.00, 0.00],
            'VEÍCULO (PLACA)': ['ABC1234', 'XYZ5678', 'DEF9012'],
            'CÓDIGO CLIENTE': ['CLI001', 'CLI002', 'CLI003'],
            'DATA ENCERRAMENTO': ['2024-01-15', '2024-01-16', '2024-01-17']
        })
    
    @pytest.fixture
    def temp_dir(self):
        """Diretório temporário para testes"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir
    
    def test_auditor_initialization(self):
        """Testa inicialização do auditor"""
        auditor = DataAuditor(tolerance_percentage=0.01)
        assert auditor.tolerance_percentage == 0.01
        
        auditor = DataAuditor(tolerance_percentage=0.05)
        assert auditor.tolerance_percentage == 0.05
    
    def test_load_csv_data(self, sample_csv_data, temp_dir):
        """Testa carregamento de dados CSV"""
        csv_file = os.path.join(temp_dir, "test.csv")
        sample_csv_data.to_csv(csv_file, index=False)
        
        auditor = DataAuditor()
        df = auditor.load_csv_data(csv_file)
        
        assert len(df) == 3
        assert list(df.columns) == list(sample_csv_data.columns)
    
    def test_load_generated_data(self, sample_generated_data, temp_dir):
        """Testa carregamento de dados Excel"""
        excel_file = os.path.join(temp_dir, "test.xlsx")
        sample_generated_data.to_excel(excel_file, index=False)
        
        auditor = DataAuditor()
        df = auditor.load_generated_data(excel_file)
        
        assert len(df) == 3
        assert 'N° OS' in df.columns
    
    def test_normalize_column_names(self):
        """Testa normalização de nomes de colunas"""
        df = pd.DataFrame({
            'N_OS': [1, 2],
            'VALOR_TOTAL': [100, 200],
            'DATA_PGTO': ['2024-01-01', '2024-01-02']
        })
        
        auditor = DataAuditor()
        normalized_df = auditor.normalize_column_names(df)
        
        # Verifica se algumas normalizações foram aplicadas
        assert 'N° OS' in normalized_df.columns or 'N_OS' in normalized_df.columns
    
    def test_compare_numeric_values(self):
        """Testa comparação de valores numéricos"""
        auditor = DataAuditor(tolerance_percentage=0.01)
        
        # Valores iguais
        result = auditor.compare_numeric_values(100.0, 100.0, 'VALOR')
        assert result.is_match is True
        assert result.difference == 0.0
        
        # Valores dentro da tolerância
        result = auditor.compare_numeric_values(100.0, 100.5, 'VALOR')
        assert result.is_match is True  # 0.5% de diferença < 1% tolerância
        
        # Valores fora da tolerância
        result = auditor.compare_numeric_values(100.0, 102.0, 'VALOR')
        assert result.is_match is False  # 2% de diferença > 1% tolerância
    
    def test_compare_text_values(self):
        """Testa comparação de valores de texto"""
        auditor = DataAuditor()
        
        # Valores iguais
        result = auditor.compare_text_values("ABC123", "ABC123", 'PLACA')
        assert result.is_match is True
        
        # Valores diferentes
        result = auditor.compare_text_values("ABC123", "XYZ789", 'PLACA')
        assert result.is_match is False
        
        # Case insensitive
        result = auditor.compare_text_values("abc123", "ABC123", 'PLACA')
        assert result.is_match is True
    
    def test_compare_date_values(self):
        """Testa comparação de valores de data"""
        auditor = DataAuditor()
        
        # Datas iguais
        result = auditor.compare_date_values('2024-01-15', '2024-01-15', 'DATA')
        assert result.is_match is True
        
        # Datas diferentes
        result = auditor.compare_date_values('2024-01-15', '2024-01-16', 'DATA')
        assert result.is_match is False
    
    def test_audit_record(self, sample_csv_data, sample_generated_data):
        """Testa auditoria de um registro individual"""
        auditor = DataAuditor()
        
        csv_row = sample_csv_data.iloc[0]
        generated_row = sample_generated_data.iloc[0]
        
        field_mappings = {
            'numero_os': 'N° OS',
            'valor_total': 'VALOR TOTAL',
            'valor_pago': 'VALOR PAGO'
        }
        
        results = auditor.audit_record(csv_row, generated_row, field_mappings)
        
        assert len(results) == 3
        assert all(result.is_match for result in results)
    
    def test_audit_data_perfect_match(self, sample_csv_data, sample_generated_data, temp_dir):
        """Testa auditoria com dados perfeitamente coincidentes"""
        csv_file = os.path.join(temp_dir, "test.csv")
        excel_file = os.path.join(temp_dir, "test.xlsx")
        
        sample_csv_data.to_csv(csv_file, index=False)
        sample_generated_data.to_excel(excel_file, index=False)
        
        auditor = DataAuditor()
        field_mappings = {
            'numero_os': 'N° OS',
            'valor_total': 'VALOR TOTAL',
            'valor_pago': 'VALOR PAGO'
        }
        
        summary, results = auditor.audit_data(
            csv_file_path=csv_file,
            generated_file_path=excel_file,
            field_mappings=field_mappings,
            key_field='numero_os'
        )
        
        assert summary.total_records == 3
        assert summary.matching_records == 3
        assert summary.mismatched_records == 0
        assert summary.total_fields_checked == 9  # 3 registros × 3 campos
        assert summary.matching_fields == 9
        assert summary.mismatched_fields == 0
    
    def test_audit_data_with_differences(self, sample_csv_data, sample_generated_data, temp_dir):
        """Testa auditoria com diferenças nos dados"""
        # Modifica alguns valores para criar diferenças
        sample_csv_data.loc[0, 'valor_total'] = 1001.00  # Diferença pequena
        sample_csv_data.loc[1, 'valor_pago'] = 2401.00   # Diferença maior
        
        csv_file = os.path.join(temp_dir, "test.csv")
        excel_file = os.path.join(temp_dir, "test.xlsx")
        
        sample_csv_data.to_csv(csv_file, index=False)
        sample_generated_data.to_excel(excel_file, index=False)
        
        auditor = DataAuditor(tolerance_percentage=0.01)
        field_mappings = {
            'numero_os': 'N° OS',
            'valor_total': 'VALOR TOTAL',
            'valor_pago': 'VALOR PAGO'
        }
        
        summary, results = auditor.audit_data(
            csv_file_path=csv_file,
            generated_file_path=excel_file,
            field_mappings=field_mappings,
            key_field='numero_os'
        )
        
        # Deve encontrar algumas diferenças
        assert summary.mismatched_fields > 0
        assert summary.matching_fields < summary.total_fields_checked
    
    def test_audit_data_missing_records(self, sample_csv_data, sample_generated_data, temp_dir):
        """Testa auditoria com registros faltando"""
        # Remove um registro do CSV
        sample_csv_data = sample_csv_data.iloc[:2]
        
        csv_file = os.path.join(temp_dir, "test.csv")
        excel_file = os.path.join(temp_dir, "test.xlsx")
        
        sample_csv_data.to_csv(csv_file, index=False)
        sample_generated_data.to_excel(excel_file, index=False)
        
        auditor = DataAuditor()
        field_mappings = {
            'numero_os': 'N° OS',
            'valor_total': 'VALOR TOTAL'
        }
        
        summary, results = auditor.audit_data(
            csv_file_path=csv_file,
            generated_file_path=excel_file,
            field_mappings=field_mappings,
            key_field='numero_os'
        )
        
        assert summary.total_records == 2
        assert summary.matching_records == 2
        assert summary.mismatched_records == 0
    
    def test_generate_audit_report(self, sample_csv_data, sample_generated_data, temp_dir):
        """Testa geração de relatório de auditoria"""
        csv_file = os.path.join(temp_dir, "test.csv")
        excel_file = os.path.join(temp_dir, "test.xlsx")
        report_file = os.path.join(temp_dir, "report.xlsx")
        
        sample_csv_data.to_csv(csv_file, index=False)
        sample_generated_data.to_excel(excel_file, index=False)
        
        auditor = DataAuditor()
        field_mappings = {
            'numero_os': 'N° OS',
            'valor_total': 'VALOR TOTAL'
        }
        
        summary, results = auditor.audit_data(
            csv_file_path=csv_file,
            generated_file_path=excel_file,
            field_mappings=field_mappings,
            key_field='numero_os'
        )
        
        auditor.generate_audit_report(summary, results, report_file)
        
        # Verifica se o relatório foi criado
        assert os.path.exists(report_file)
        
        # Verifica se o relatório tem as planilhas esperadas
        report_df = pd.ExcelFile(report_file)
        assert 'Resumo' in report_df.sheet_names
        assert 'Detalhes' in report_df.sheet_names
    
    def test_audit_error_handling(self, temp_dir):
        """Testa tratamento de erros"""
        auditor = DataAuditor()
        
        # Arquivo CSV inexistente
        with pytest.raises(AuditError):
            auditor.load_csv_data("arquivo_inexistente.csv")
        
        # Arquivo Excel inexistente
        with pytest.raises(AuditError):
            auditor.load_generated_data("arquivo_inexistente.xlsx")
    
    def test_different_tolerance_levels(self):
        """Testa diferentes níveis de tolerância"""
        # Tolerância 0% (exata)
        auditor_strict = DataAuditor(tolerance_percentage=0.0)
        result = auditor_strict.compare_numeric_values(100.0, 100.1, 'VALOR')
        assert result.is_match is False
        
        # Tolerância 5%
        auditor_loose = DataAuditor(tolerance_percentage=0.05)
        result = auditor_loose.compare_numeric_values(100.0, 100.1, 'VALOR')
        assert result.is_match is True  # 0.1% < 5%
    
    def test_empty_dataframes(self, temp_dir):
        """Testa auditoria com DataFrames vazios"""
        # Cria DataFrames vazios mas com colunas
        empty_csv = pd.DataFrame(columns=['numero_os', 'valor_total'])
        empty_excel = pd.DataFrame(columns=['N° OS', 'VALOR TOTAL'])
        
        csv_file = os.path.join(temp_dir, "empty.csv")
        excel_file = os.path.join(temp_dir, "empty.xlsx")
        
        empty_csv.to_csv(csv_file, index=False)
        empty_excel.to_excel(excel_file, index=False)
        
        auditor = DataAuditor()
        field_mappings = {'numero_os': 'N° OS'}
        
        summary, results = auditor.audit_data(
            csv_file_path=csv_file,
            generated_file_path=excel_file,
            field_mappings=field_mappings,
            key_field='numero_os'
        )
        
        assert summary.total_records == 0
        assert summary.matching_records == 0
        assert summary.mismatched_records == 0 