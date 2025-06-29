#!/usr/bin/env python3
"""
Testes automatizados para auditoria de transações de cartão
"""

import pytest
import pandas as pd
import tempfile
import os
from datetime import datetime, date
from unittest.mock import patch, MagicMock

# Importa as funções do script de auditoria
import sys
sys.path.append('..')
from audit_cartao import parse_cartao_csv, create_audit_mappings, audit_cartao_transactions, generate_cartao_report


class TestAuditCartao:
    """Testes para auditoria de cartão"""
    
    def setup_method(self):
        """Configuração para cada teste"""
        self.sample_csv_data = '''Data e hora,Meio - Meio,Meio - Bandeira,Meio - Parcelas,Tipo - Origem,Tipo - Dados adicionais,Identificador,Status,Valor (R$),Líquido (R$),Taxa Aplicada - Valor(R$),Taxa Aplicada - Aplicada(%),Plano
"27 Jun, 2025 · 18:38",Credito,visa,6,Maquininha,NS: PB58221N79820,039898,Aprovada,"2.487,17","2.329,98","- 157,19",6.32,1 Dia Util
"27 Jun, 2025 · 17:28",Credito,visa,A Vista,Maquininha,NS: PB58221N79820,037844,Aprovada,"200,00","194,42","- 5,58",2.79,1 Dia Util
"26 Jun, 2025 · 09:34",Debito,visa,A Vista,Maquininha,NS: PB58221N79820,202988,Aprovada,"2.001,80","1.985,99","- 15,81",0.78,1 Dia Util
"25 Jun, 2025 · 11:35",PIX,visa,A Vista,Maquininha,NS: PB58221N79820,227355,Aprovada,"323,75","314,72","- 9,03",2.78,1 Dia Util'''
        
        self.sample_generated_data = pd.DataFrame({
            'DATA PGTO': [date(2025, 6, 27), date(2025, 6, 26), date(2025, 6, 25)],
            'CARTÃO': [2487.17, 2001.80, 0],
            'PIX': [0, 0, 323.75],
            'OUTROS': [0, 0, 0]
        })
    
    def test_parse_cartao_csv(self):
        """Testa o parsing do CSV de cartão"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
            f.write(self.sample_csv_data)
            csv_path = f.name
        
        try:
            df = parse_cartao_csv(csv_path)
            
            # Verifica se o DataFrame foi criado corretamente
            assert len(df) == 4
            assert 'DATA_PGTO' in df.columns
            assert 'TIPO_PAGAMENTO' in df.columns
            assert 'VALOR_AUDITORIA' in df.columns
            
            # Verifica tipos de pagamento
            tipos = df['TIPO_PAGAMENTO'].value_counts()
            assert tipos['CARTÃO'] == 3  # 2 Credito + 1 Debito
            assert tipos['PIX'] == 1
            
            # Verifica valores
            assert df.loc[0, 'VALOR_AUDITORIA'] == 2487.17
            assert df.loc[1, 'VALOR_AUDITORIA'] == 200.00
            
            # Verifica datas
            assert df.loc[0, 'DATA_PGTO'] == date(2025, 6, 27)
            assert df.loc[2, 'DATA_PGTO'] == date(2025, 6, 26)
            
        finally:
            os.unlink(csv_path)
    
    def test_create_audit_mappings(self):
        """Testa a criação de mapeamentos de auditoria"""
        # Cria DataFrame de teste
        df = pd.DataFrame({
            'Identificador': ['039898', '037844', '202988', '227355'],
            'TIPO_PAGAMENTO': ['CARTÃO', 'CARTÃO', 'CARTÃO', 'PIX'],
            'VALOR_AUDITORIA': [2487.17, 200.00, 2001.80, 323.75],
            'DATA_PGTO': [date(2025, 6, 27), date(2025, 6, 27), date(2025, 6, 26), date(2025, 6, 25)]
        })
        
        mappings = create_audit_mappings(df)
        
        # Verifica se os mapeamentos foram criados corretamente
        assert len(mappings) == 4
        
        # Verifica mapeamento de cartão
        assert mappings['039898']['generated_field'] == 'CARTÃO'
        assert mappings['039898']['tipo'] == 'CARTÃO'
        assert mappings['039898']['valor'] == 2487.17
        
        # Verifica mapeamento de PIX
        assert mappings['227355']['generated_field'] == 'PIX'
        assert mappings['227355']['tipo'] == 'PIX'
        assert mappings['227355']['valor'] == 323.75
    
    @patch('audit_cartao.DataAuditor')
    def test_audit_cartao_transactions_success(self, mock_auditor):
        """Testa auditoria bem-sucedida"""
        # Configura mock
        mock_auditor_instance = MagicMock()
        mock_auditor.return_value = mock_auditor_instance
        mock_auditor_instance.load_generated_data.return_value = self.sample_generated_data
        mock_auditor_instance.normalize_column_names.return_value = self.sample_generated_data
        
        # Cria arquivos temporários
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as csv_f:
            csv_f.write(self.sample_csv_data)
            csv_path = csv_f.name
        
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as excel_f:
            excel_path = excel_f.name
        
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as report_f:
            report_path = report_f.name
        
        try:
            # Executa auditoria
            audit_cartao_transactions(csv_path, excel_path, report_path)
            
            # Verifica se o relatório foi gerado
            assert os.path.exists(report_path)
            
        finally:
            # Limpa arquivos temporários
            for path in [csv_path, excel_path, report_path]:
                if os.path.exists(path):
                    os.unlink(path)
    
    def test_generate_cartao_report(self):
        """Testa geração de relatório Excel"""
        # Dados de teste
        results = [
            {
                'identificador': '039898',
                'data_cartao': date(2025, 6, 27),
                'valor_cartao': 2487.17,
                'tipo_pagamento': 'CARTÃO',
                'status': 'COINCIDENTE',
                'valor_gerado': 2487.17,
                'diferenca': 0.0,
                'observacao': 'Encontrado na coluna CARTÃO'
            },
            {
                'identificador': '037844',
                'data_cartao': date(2025, 6, 27),
                'valor_cartao': 200.00,
                'tipo_pagamento': 'CARTÃO',
                'status': 'NÃO ENCONTRADA',
                'valor_gerado': None,
                'diferenca': None,
                'observacao': 'Data 2025-06-27 não encontrada nos dados gerados'
            }
        ]
        
        summary_stats = {
            'total_transacoes': 2,
            'cartao_encontradas': 1,
            'pix_encontradas': 0,
            'nao_encontradas': 1,
            'valores_coincidentes': 1,
            'valores_divergentes': 0
        }
        
        # Gera relatório
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as f:
            report_path = f.name
        
        try:
            generate_cartao_report(results, summary_stats, report_path)
            
            # Verifica se o arquivo foi criado
            assert os.path.exists(report_path)
            assert os.path.getsize(report_path) > 0
            
            # Verifica se as abas foram criadas
            with pd.ExcelFile(report_path) as xl:
                assert 'Resumo' in xl.sheet_names
                assert 'Detalhes' in xl.sheet_names
                assert 'Divergências' in xl.sheet_names
                
                # Verifica dados do resumo
                resumo_df = pd.read_excel(report_path, sheet_name='Resumo')
                assert len(resumo_df) == 8  # 8 métricas
                assert resumo_df.iloc[0]['Valor'] == 2  # Total de transações
                
                # Verifica dados dos detalhes
                detalhes_df = pd.read_excel(report_path, sheet_name='Detalhes')
                assert len(detalhes_df) == 2  # 2 resultados
                
                # Verifica dados das divergências
                divergencias_df = pd.read_excel(report_path, sheet_name='Divergências')
                assert len(divergencias_df) == 1  # 1 divergência
                
        finally:
            if os.path.exists(report_path):
                os.unlink(report_path)
    
    def test_parse_cartao_csv_invalid_format(self):
        """Testa parsing de CSV com formato inválido"""
        invalid_csv_data = '''Data e hora,Meio - Meio,Identificador,Valor (R$)
"data invalida",Credito,039898,"valor invalido"'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
            f.write(invalid_csv_data)
            csv_path = f.name
        
        try:
            with pytest.raises(Exception):
                parse_cartao_csv(csv_path)
        finally:
            os.unlink(csv_path)
    
    @patch('audit_cartao.DataAuditor')
    def test_audit_cartao_transactions_missing_files(self, mock_auditor):
        """Testa auditoria com arquivos ausentes"""
        # Testa com CSV ausente
        audit_cartao_transactions('arquivo_inexistente.csv', 'arquivo_inexistente.xlsx')
        
        # Testa com Excel ausente
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
            f.write(self.sample_csv_data)
            csv_path = f.name
        
        try:
            audit_cartao_transactions(csv_path, 'arquivo_inexistente.xlsx')
        finally:
            os.unlink(csv_path)


if __name__ == '__main__':
    pytest.main([__file__]) 