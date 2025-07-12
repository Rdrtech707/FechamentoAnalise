# DETALHES TÉCNICOS PARA ANÁLISE LLM

## 🔍 ESTRUTURAS DE DADOS PRINCIPAIS

### 1. **DataFrames Pandas**
```python
# Recebimentos DataFrame
recebimentos_df = pd.DataFrame({
    'N° OS': int,
    'VALOR MÃO DE OBRA': float,
    'DESCONTO': float,
    'DATA PGTO': datetime,
    'VALOR_LIQUIDO': float  # Calculado: MÃO DE OBRA - DESCONTO
})

# Transações de Cartão DataFrame
cartao_df = pd.DataFrame({
    'DATA': datetime,
    'VALOR': float,
    'DESCRIÇÃO': str,
    'TIPO': str  # 'CREDITO' ou 'DEBITO'
})

# Transações PIX DataFrame
pix_df = pd.DataFrame({
    'DATA': datetime,
    'VALOR': float,
    'DESCRIÇÃO': str,
    'TIPO': str  # 'PIX'
})
```

### 2. **Classes de Auditoria**
```python
@dataclass
class AuditResult:
    total_transactions: int
    matched_transactions: int
    unmatched_transactions: int
    total_value: float
    matched_value: float
    unmatched_value: float
    discrepancies: List[Dict]

@dataclass
class AuditSummary:
    cartao_result: AuditResult
    pix_result: AuditResult
    nfse_result: AuditResult
    overall_summary: Dict
```

## 🧮 ALGORITMOS PRINCIPAIS

### 1. **Algoritmo de Reconciliação**
```python
def reconcile_transactions(recebimentos_df, transactions_df):
    """
    Algoritmo de reconciliação baseado em:
    1. Comparação de valores (com tolerância de centavos)
    2. Comparação de datas (com tolerância de dias)
    3. Análise de descrições (fuzzy matching)
    """
    matched = []
    unmatched = []
    
    for _, transaction in transactions_df.iterrows():
        # Busca por valor exato
        exact_matches = recebimentos_df[
            abs(recebimentos_df['VALOR_LIQUIDO'] - transaction['VALOR']) < 0.01
        ]
        
        if len(exact_matches) > 0:
            # Filtra por data próxima
            date_matches = exact_matches[
                abs(exact_matches['DATA_PGTO'] - transaction['DATA']).dt.days <= 3
            ]
            
            if len(date_matches) > 0:
                matched.append({
                    'transaction': transaction,
                    'recebimento': date_matches.iloc[0]
                })
            else:
                unmatched.append(transaction)
        else:
            unmatched.append(transaction)
    
    return matched, unmatched
```

### 2. **Algoritmo de Extração de NFSe**
```python
def extract_nfse_data(pdf_path):
    """
    Algoritmo de extração usando:
    1. pdfplumber para extrair texto
    2. Regex patterns para identificar dados
    3. Validação de formatos brasileiros
    """
    patterns = {
        'numero_nfse': r'N[ºo]:?\s*(\d+/\d+)',
        'valor_total': r'Valor Total[\s\-:]*R?\$?\s*([\d\.]+,[\d]{2})',
        'nome_tomador': r'Tomador[\s\-:]*([^\n\r]+)',
        'data_emissao': r'Data de Emissão[:\s]*(\d{2}/\d{2}/\d{4})'
    }
    
    # Extração e validação
    extracted_data = {}
    for field, pattern in patterns.items():
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            extracted_data[field] = clean_value(match.group(1), field)
    
    return extracted_data
```

## 📊 PADRÕES DE PROCESSAMENTO

### 1. **Pipeline de Dados**
```python
class DataPipeline:
    def __init__(self):
        self.extractors = []
        self.processors = []
        self.exporters = []
    
    def add_extractor(self, extractor):
        self.extractors.append(extractor)
    
    def add_processor(self, processor):
        self.processors.append(processor)
    
    def add_exporter(self, exporter):
        self.exporters.append(exporter)
    
    def run(self, data):
        # Extração
        for extractor in self.extractors:
            data = extractor.extract(data)
        
        # Processamento
        for processor in self.processors:
            data = processor.process(data)
        
        # Exportação
        for exporter in self.exporters:
            exporter.export(data)
```

### 2. **Padrão Observer para Logs**
```python
class LogObserver:
    def __init__(self):
        self.observers = []
    
    def add_observer(self, observer):
        self.observers.append(observer)
    
    def notify(self, message, level="INFO"):
        for observer in self.observers:
            observer.update(message, level)

class GUILogger:
    def update(self, message, level):
        # Atualiza interface gráfica
        self.log_text.insert(tk.END, f"[{level}] {message}\n")
```

## 🔧 CONFIGURAÇÕES E PARÂMETROS

### 1. **Configurações de Estilo**
```python
# style_config.py
COLUMN_WIDTHS = {
    'N° OS': 15,
    'VALOR MÃO DE OBRA': 20,
    'DESCONTO': 15,
    'VALOR_LIQUIDO': 20,
    'DATA PGTO': 15
}

BORDER_CONFIGS = {
    'header': Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )
}

THEMES = {
    'default': {
        'header_fill': PatternFill(start_color='2E86AB', end_color='2E86AB', fill_type='solid'),
        'header_font': Font(color='FFFFFF', bold=True),
        'data_font': Font(size=10)
    }
}
```

### 2. **Parâmetros de Validação**
```python
VALIDATION_PARAMS = {
    'value_tolerance': 0.01,  # Tolerância para valores em reais
    'date_tolerance': 3,      # Tolerância para datas em dias
    'min_transaction_value': 1.0,  # Valor mínimo para transação
    'max_transaction_value': 100000.0  # Valor máximo para transação
}
```

## 🗄️ ESTRUTURA DO BANCO DE DADOS

### 1. **Tabelas Principais**
```sql
-- Tabela de Ordens de Serviço
CREATE TABLE OrdensServico (
    NumeroOS INT PRIMARY KEY,
    ValorMaoObra DECIMAL(10,2),
    Desconto DECIMAL(10,2),
    DataPagamento DATE,
    Status VARCHAR(50)
);

-- Tabela de Contas
CREATE TABLE Contas (
    ID INT PRIMARY KEY,
    NumeroOS INT,
    Valor DECIMAL(10,2),
    DataVencimento DATE,
    Status VARCHAR(50)
);

-- Tabela de Fluxo de Caixa
CREATE TABLE FluxoCaixa (
    ID INT PRIMARY KEY,
    Data DATE,
    Tipo VARCHAR(50),
    Valor DECIMAL(10,2),
    Descricao VARCHAR(255)
);
```

### 2. **Queries Principais**
```python
# Query para recebimentos
RECEITOS_QUERY = """
SELECT 
    os.NumeroOS,
    os.ValorMaoObra,
    os.Desconto,
    os.DataPagamento,
    (os.ValorMaoObra - os.Desconto) as ValorLiquido
FROM OrdensServico os
WHERE os.Status = 'PAGO'
ORDER BY os.DataPagamento
"""

# Query para fluxo de caixa
FLUXO_CAIXA_QUERY = """
SELECT 
    fc.Data,
    fc.Tipo,
    fc.Valor,
    fc.Descricao
FROM FluxoCaixa fc
WHERE fc.Data BETWEEN ? AND ?
ORDER BY fc.Data
"""
```

## 🔄 FLUXOS DE EXCEÇÃO

### 1. **Tratamento de Erros**
```python
class AuditError(Exception):
    """Exceção base para erros de auditoria"""
    pass

class DatabaseConnectionError(AuditError):
    """Erro de conexão com banco de dados"""
    pass

class FileNotFoundError(AuditError):
    """Arquivo não encontrado"""
    pass

class DataValidationError(AuditError):
    """Erro de validação de dados"""
    pass
```

### 2. **Estratégias de Recuperação**
```python
def safe_database_operation(func):
    """Decorator para operações seguras de banco"""
    def wrapper(*args, **kwargs):
        max_retries = 3
        for attempt in range(max_retries):
            try:
                return func(*args, **kwargs)
            except pyodbc.Error as e:
                if attempt == max_retries - 1:
                    raise DatabaseConnectionError(f"Falha após {max_retries} tentativas: {e}")
                time.sleep(1)  # Espera antes de tentar novamente
    return wrapper
```

## 📈 MÉTRICAS DE PERFORMANCE

### 1. **Indicadores de Performance**
```python
class PerformanceMetrics:
    def __init__(self):
        self.start_time = None
        self.end_time = None
        self.memory_usage = []
        self.processing_steps = []
    
    def start_timer(self):
        self.start_time = time.time()
    
    def end_timer(self):
        self.end_time = time.time()
        return self.end_time - self.start_time
    
    def add_step(self, step_name, duration):
        self.processing_steps.append({
            'step': step_name,
            'duration': duration
        })
    
    def get_summary(self):
        return {
            'total_time': self.end_timer(),
            'steps': self.processing_steps,
            'memory_peak': max(self.memory_usage) if self.memory_usage else 0
        }
```

### 2. **Otimizações Implementadas**
- **Processamento em lotes**: Divide grandes datasets em chunks
- **Cache de configurações**: Evita recarregamento de configurações
- **Lazy loading**: Carrega dados apenas quando necessário
- **Indexação de DataFrames**: Usa índices para busca rápida

## 🔐 SEGURANÇA E VALIDAÇÃO

### 1. **Validação de Entrada**
```python
def validate_file_path(file_path):
    """Validação de caminhos de arquivo"""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Arquivo não encontrado: {file_path}")
    
    if not os.path.isfile(file_path):
        raise ValueError(f"Caminho não é um arquivo: {file_path}")
    
    # Verifica extensão
    allowed_extensions = ['.csv', '.xlsx', '.xls']
    if not any(file_path.lower().endswith(ext) for ext in allowed_extensions):
        raise ValueError(f"Extensão não permitida: {file_path}")

def validate_dataframe(df, required_columns):
    """Validação de DataFrame"""
    missing_columns = set(required_columns) - set(df.columns)
    if missing_columns:
        raise DataValidationError(f"Colunas faltando: {missing_columns}")
    
    # Verifica se DataFrame não está vazio
    if df.empty:
        raise DataValidationError("DataFrame está vazio")
```

### 2. **Sanitização de Dados**
```python
def sanitize_value(value, value_type):
    """Sanitização de valores"""
    if value_type == 'currency':
        # Remove caracteres não numéricos exceto vírgula e ponto
        value = re.sub(r'[^\d,\.]', '', str(value))
        # Converte para float
        value = value.replace('.', '').replace(',', '.')
        return float(value)
    
    elif value_type == 'date':
        # Converte para datetime
        return pd.to_datetime(value, errors='coerce')
    
    elif value_type == 'text':
        # Remove caracteres especiais
        return re.sub(r'[^\w\sÁÉÍÓÚÂÊÎÔÛÃÕÇáéíóúâêîôûãõç]', '', str(value))
    
    return value
```

## 🧪 ESTRATÉGIAS DE TESTE

### 1. **Testes Unitários**
```python
class TestAuditor(unittest.TestCase):
    def setUp(self):
        self.auditor = DataAuditor()
        self.sample_data = pd.DataFrame({
            'VALOR': [100.0, 200.0, 300.0],
            'DATA': ['2025-01-01', '2025-01-02', '2025-01-03']
        })
    
    def test_reconciliation_algorithm(self):
        """Testa algoritmo de reconciliação"""
        result = self.auditor.reconcile_transactions(
            self.sample_data, 
            self.sample_data
        )
        self.assertEqual(len(result.matched_transactions), 3)
        self.assertEqual(len(result.unmatched_transactions), 0)
    
    def test_value_validation(self):
        """Testa validação de valores"""
        with self.assertRaises(DataValidationError):
            self.auditor.validate_value(-100.0)
```

### 2. **Testes de Integração**
```python
class TestIntegration(unittest.TestCase):
    def test_full_audit_pipeline(self):
        """Testa pipeline completo de auditoria"""
        # Setup
        test_files = self.create_test_files()
        
        # Execute
        result = execute_audit_pipeline(test_files)
        
        # Assert
        self.assertIsNotNone(result)
        self.assertTrue(result.success)
        self.assertGreater(len(result.report), 0)
```

---

**Este documento fornece detalhes técnicos específicos para análise profunda por LLM, incluindo algoritmos, estruturas de dados, padrões de código e estratégias de implementação.** 