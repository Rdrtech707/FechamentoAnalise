# Instruções para Auditoria de Transações de Cartão

## 📋 Visão Geral

Este sistema de auditoria especializada compara transações de cartão extraídas de um CSV com os dados gerados pela aplicação principal. Ele identifica automaticamente se uma transação é de cartão (Crédito/Débito) ou PIX e procura os valores correspondentes nas colunas corretas da tabela gerada.

## 🎯 Funcionalidades

### Identificação Automática de Tipo de Pagamento
- **Cartão**: Transações com "Meio - Meio" = "Crédito" ou "Débito"
- **PIX**: Transações com "Meio - Meio" diferente de Crédito/Débito

### Mapeamento de Colunas
- Transações de **Cartão** → Procura na coluna **CARTÃO** da tabela gerada
- Transações de **PIX** → Procura na coluna **PIX** da tabela gerada

### Critérios de Comparação
1. **Data**: "Data e hora" do CSV deve coincidir com "DATA_PGTO" da tabela gerada
2. **Valor**: "Valor (R$)" do CSV deve coincidir com o valor na coluna correspondente
3. **Tolerância**: 1% de diferença é aceitável para pequenas variações

## 📁 Arquivos do Sistema

### Script Principal
- `audit_cartao.py` - Script especializado para auditoria de cartão

### Arquivos de Dados
- `data/extratos/report_20250628_194465.csv` - CSV com transações de cartão
- `data/recebimentos/Recebimentos_2025-06.xlsx` - Tabela gerada pela aplicação

### Relatórios
- `auditoria_cartao_relatorio.xlsx` - Relatório detalhado da auditoria

## 🚀 Como Usar

### 1. Preparação
Certifique-se de que:
- O CSV de transações está em `data/extratos/report_20250628_194465.csv`
- A tabela gerada está em `data/recebimentos/Recebimentos_2025-06.xlsx`
- Todas as dependências estão instaladas

### 2. Execução
```bash
python audit_cartao.py
```

### 3. Interpretação dos Resultados

#### Status Possíveis:
- **COINCIDENTE**: Valor encontrado e coincide (dentro da tolerância)
- **DIVERGENTE**: Valor encontrado mas não coincide
- **NÃO ENCONTRADA**: Data não encontrada na tabela gerada
- **VALOR NÃO ENCONTRADO**: Data encontrada mas valor não encontrado na coluna correta

#### Relatório Excel:
- **Aba "Resumo"**: Estatísticas gerais da auditoria
- **Aba "Detalhes"**: Todas as transações auditadas
- **Aba "Divergências"**: Apenas transações com problemas

## 📊 Exemplo de Saída

```
=== AUDITORIA DE TRANSAÇÕES DE CARTÃO ===
Carregando CSV de transações: data/extratos/report_20250628_194465.csv
CSV processado: 28 transações
Transações por tipo: {'CARTÃO': 26, 'PIX': 2}
Dados gerados carregados: 15 registros

=== RESUMO DA AUDITORIA ===
Total de transações: 28
Cartão encontradas: 20
PIX encontradas: 1
Não encontradas: 7
Valores coincidentes: 18
Valores divergentes: 3
Taxa de sucesso: 64.29%

=== PRIMEIRAS 5 DIVERGÊNCIAS ===
1. ID: 039898
   Data: 2025-06-27
   Tipo: CARTÃO
   Valor CSV: R$ 2487.17
   Valor Gerado: R$ 2487.00
   Status: DIVERGENTE
   Observação: Encontrado na coluna CARTÃO
```

## 🔧 Configurações

### Tolerância de Valores
A tolerância padrão é de 1%. Para alterar, modifique esta linha no código:
```python
auditor = DataAuditor(tolerance_percentage=0.01)  # 1% de tolerância
```

### Caminhos dos Arquivos
Para alterar os caminhos, modifique estas variáveis na função `main()`:
```python
csv_file = "data/extratos/report_20250628_194465.csv"
generated_file = os.path.join(OUTPUT_DIR, "Recebimentos_2025-06.xlsx")
report_file = "auditoria_cartao_relatorio.xlsx"
```

## 📋 Estrutura do CSV Esperada

O CSV deve ter as seguintes colunas:
- `Data e hora`: Data e hora da transação (formato: "27 Jun, 2025 · 18:38")
- `Meio - Meio`: Tipo de pagamento ("Crédito", "Débito", ou outro para PIX)
- `Identificador`: ID único da transação
- `Valor (R$)`: Valor da transação (formato: "2.487,17")
- `Líquido (R$)`: Valor líquido da transação

## 📋 Estrutura da Tabela Gerada Esperada

A tabela Excel gerada deve ter as seguintes colunas:
- `DATA PGTO`: Data do pagamento
- `CARTÃO`: Valores de transações de cartão
- `PIX`: Valores de transações PIX

## ⚠️ Problemas Comuns

### 1. "Arquivo CSV não encontrado"
- Verifique se o arquivo está no caminho correto
- Confirme se o nome do arquivo está correto

### 2. "Arquivo gerado não encontrado"
- Execute primeiro a aplicação principal para gerar a tabela
- Verifique se o arquivo foi salvo no diretório correto

### 3. "Data não encontrada"
- Verifique se as datas estão no mesmo formato
- Confirme se o período do CSV corresponde ao da tabela gerada

### 4. "Valor não encontrado"
- Verifique se os valores estão sendo processados corretamente
- Confirme se a tolerância está adequada

## 🔍 Dicas para Análise

### 1. Verificar Divergências
- Foque primeiro nas transações "NÃO ENCONTRADA"
- Analise as "DIVERGENTE" para entender as diferenças

### 2. Ajustar Tolerância
- Se houver muitas divergências pequenas, aumente a tolerância
- Se houver coincidências incorretas, diminua a tolerância

### 3. Verificar Datas
- Confirme se as datas estão sendo interpretadas corretamente
- Verifique se há diferenças de fuso horário

## 📞 Suporte

Para problemas ou dúvidas:
1. Verifique os logs de erro no terminal
2. Confirme se todos os arquivos estão no lugar correto
3. Teste com um conjunto menor de dados primeiro 