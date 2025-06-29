# 📋 Instruções para Auditoria de Dados - TABELA RECEBIMENTOS

Este documento explica como usar o módulo de auditoria para comparar dados CSV com os dados gerados pela aplicação.

## 🎯 O que é a Auditoria?

O módulo de auditoria permite:
- **Comparar** dados de um arquivo CSV com os dados gerados pela aplicação
- **Identificar** discrepâncias entre os valores
- **Gerar relatórios** detalhados das diferenças encontradas
- **Validar** a precisão dos dados processados

## 📁 Arquivos do Módulo

- `modules/auditor.py` - Módulo principal de auditoria
- `audit_example.py` - Exemplo de uso
- `INSTRUCOES_AUDITORIA.md` - Esta documentação

## 🚀 Como Usar

### 1. Preparar o Arquivo CSV

Crie um arquivo CSV com os dados que você quer comparar. Exemplo:

```csv
numero_os,data_pagamento,valor_total,valor_pago,valor_devedor,cartao,dinheiro,pix,troco,placa_veiculo,codigo_cliente,data_encerramento
001,2024-01-15,1000.50,1000.50,0.00,500.25,300.25,200.00,0.00,ABC1234,CLI001,2024-01-15
002,2024-01-16,2500.75,2400.75,100.00,1200.00,800.75,400.00,0.00,XYZ5678,CLI002,2024-01-16
```

### 2. Configurar o Mapeamento de Campos

No arquivo `audit_example.py`, ajuste o mapeamento de campos:

```python
field_mappings = {
    'numero_os': 'N° OS',                    # Campo CSV -> Campo Gerado
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
```

### 3. Executar a Auditoria

```bash
python audit_example.py
```

## ⚙️ Configurações

### Tolerância para Valores Numéricos

```python
# 1% de tolerância (padrão)
auditor = DataAuditor(tolerance_percentage=0.01)

# 5% de tolerância
auditor = DataAuditor(tolerance_percentage=0.05)

# Sem tolerância (valores devem ser idênticos)
auditor = DataAuditor(tolerance_percentage=0.0)
```

### Campo Chave

Define qual campo usar para relacionar registros:

```python
# Usar N° OS como chave
key_field='N° OS'

# Usar código do cliente como chave
key_field='CÓDIGO CLIENTE'
```

## 📊 Tipos de Comparação

### 1. Valores Numéricos
- **Campos**: VALOR TOTAL, VALOR PAGO, DEVEDOR, CARTÃO, DINHEIRO, PIX, TROCO
- **Comparação**: Com tolerância percentual
- **Exemplo**: Se tolerância = 1%, valores 100.00 e 101.00 são considerados iguais

### 2. Datas
- **Campos**: DATA PGTO, DATA ENCERRAMENTO
- **Comparação**: Exata (mesmo dia)
- **Formatos aceitos**: Qualquer formato reconhecido pelo pandas

### 3. Texto
- **Campos**: N° OS, VEÍCULO (PLACA), CÓDIGO CLIENTE
- **Comparação**: Exata (ignora maiúsculas/minúsculas)
- **Exemplo**: "ABC1234" = "abc1234"

## 📈 Relatórios Gerados

### 1. Resumo
- Total de registros verificados
- Registros coincidentes/divergentes
- Taxa de sucesso
- Configurações usadas

### 2. Detalhes
- Todos os campos verificados
- Valores CSV vs Gerado
- Indicador de coincidência
- Diferenças encontradas

### 3. Divergências
- Apenas campos com diferenças
- Detalhes das discrepâncias
- Observações explicativas

## 🔧 Exemplo Completo

```python
from modules.auditor import DataAuditor

# Inicializa auditor
auditor = DataAuditor(tolerance_percentage=0.01)

# Define mapeamento
field_mappings = {
    'numero_os': 'N° OS',
    'valor_total': 'VALOR TOTAL',
    'valor_pago': 'VALOR PAGO'
}

# Executa auditoria
summary, results = auditor.audit_data(
    csv_file_path='meus_dados.csv',
    generated_file_path='Recebimentos_2024-01.xlsx',
    field_mappings=field_mappings,
    key_field='N° OS'
)

# Gera relatório
auditor.generate_audit_report(summary, results, 'relatorio.xlsx')
```

## ⚠️ Dicas Importantes

### 1. Preparação dos Dados
- **CSV**: Use encoding UTF-8 ou Latin1
- **Campos numéricos**: Use ponto como separador decimal
- **Datas**: Use formato consistente (YYYY-MM-DD recomendado)

### 2. Mapeamento de Campos
- **Nomes exatos**: Os nomes devem corresponder aos do arquivo gerado
- **Case sensitive**: "N° OS" ≠ "n° os"
- **Espaços**: "VALOR TOTAL" ≠ "VALOR_TOTAL"

### 3. Campo Chave
- **Único**: Cada valor deve aparecer apenas uma vez
- **Presente**: Deve existir em ambos os arquivos
- **Consistente**: Mesmo formato em CSV e Excel

## 🚨 Solução de Problemas

### Erro: "Campo não encontrado"
**Problema**: Campo do mapeamento não existe no arquivo
**Solução**: Verifique o nome exato do campo no arquivo

### Erro: "Registro não encontrado"
**Problema**: Valor do campo chave não existe no arquivo gerado
**Solução**: Verifique se o registro foi processado pela aplicação

### Erro: "Erro na conversão numérica"
**Problema**: Campo numérico contém texto
**Solução**: Limpe os dados CSV antes da auditoria

### Erro: "Erro na conversão de data"
**Problema**: Formato de data não reconhecido
**Solução**: Padronize o formato de datas no CSV

## 📋 Checklist de Auditoria

Antes de executar:

- [ ] Arquivo CSV existe e é legível
- [ ] Arquivo Excel gerado existe
- [ ] Mapeamento de campos está correto
- [ ] Campo chave é único e consistente
- [ ] Tolerância configurada adequadamente
- [ ] Encoding do CSV é compatível

## 🎯 Casos de Uso

### 1. Validação de Processamento
- Comparar dados originais com dados processados
- Verificar se cálculos estão corretos
- Identificar registros não processados

### 2. Auditoria Contábil
- Validar valores monetários
- Verificar formas de pagamento
- Confirmar datas de transação

### 3. Controle de Qualidade
- Detectar inconsistências
- Validar integridade dos dados
- Gerar relatórios de conformidade

## 📞 Suporte

Se encontrar problemas:
1. Verifique os logs no console
2. Confirme se os arquivos existem
3. Valide o mapeamento de campos
4. Teste com dados menores primeiro

---

**🎉 Agora você pode auditar seus dados com precisão e gerar relatórios detalhados!** 