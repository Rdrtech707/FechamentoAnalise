# 📋 Instruções para Configuração de Estilos - TABELA RECEBIMENTOS

Este arquivo contém instruções detalhadas para leigos modificarem o arquivo `style_config.py` e personalizarem a aparência dos relatórios Excel gerados pelo sistema.

## 📁 Arquivo: `style_config.py`

Este arquivo controla TODOS os aspectos visuais dos relatórios Excel:
- **Cores** (cabeçalhos, dados, fundos)
- **Formatos** (moeda, data, números)
- **Largura das colunas**
- **Bordas** (estilos e cores)
- **Temas** (conjuntos de configurações)

---

## 🎨 1. CONFIGURAÇÃO DE CORES

### 1.1 Tabela de Cores Disponíveis

| Cor | Código | Nome |
|-----|--------|------|
| 🔴 | `FF0000` | Vermelho |
| 🟢 | `00FF00` | Verde |
| 🔵 | `0000FF` | Azul |
| ⚫ | `000000` | Preto |
| ⚪ | `FFFFFF` | Branco |
| 🟡 | `FFFF00` | Amarelo |
| 🟠 | `FFA500` | Laranja |
| 🟣 | `800080` | Roxo |
| 🟤 | `8B4513` | Marrom |
| 🔘 | `808080` | Cinza |
| 🔵 | `1F4E78` | Azul Escuro |
| 🟢 | `90EE90` | Verde Claro |
| 🟡 | `F2F2F2` | Cinza Claro |

### 1.2 Como Alterar Cores

**Exemplo:** Para mudar a cor do cabeçalho para azul escuro:

```python
THEMES = {
    'default': {
        'header_bg': '1F4E78',  # Azul escuro
        'header_font': 'FFFFFF',  # Texto branco
        'contabil_bg': 'F2F2F2',  # Fundo cinza claro
        'contabil_font': '000000',  # Texto preto
    }
}
```

---

## 📏 2. CONFIGURAÇÃO DE LARGURA DAS COLUNAS

### 2.1 Como Ajustar a Largura

A seção `COLUMN_WIDTHS` controla a largura de cada coluna:

```python
COLUMN_WIDTHS = {
    'N° OS': 12,              # Largura 12 para coluna N° OS
    'DATA ENCERRAMENTO': 18,  # Largura 18 para datas
    'VALOR TOTAL': 15,        # Largura 15 para valores
    'VEÍCULO (PLACA)': 25,    # Largura 25 para placas
    'default': 15,            # Largura padrão para outras colunas
}
```

### 2.2 Valores Recomendados

- **Números pequenos**: 8-12
- **Datas**: 15-18
- **Valores monetários**: 12-15
- **Textos longos**: 20-30
- **Códigos**: 10-15

### 2.3 Como Adicionar Nova Coluna

Se aparecer uma nova coluna no relatório, adicione-a assim:

```python
COLUMN_WIDTHS = {
    # ... colunas existentes ...
    'NOVA COLUNA': 15,  # Ajuste o número conforme necessário
    'default': 15,
}
```

---

## �� 3. CONFIGURAÇÃO DE BORDAS

### 3.1 Estilos de Borda Disponíveis

| Estilo | Descrição | Aparência |
|--------|-----------|-----------|
| `none` | Sem borda | ─ |
| `thin` | Borda fina | ─ |
| `medium` | Borda média | ─ |
| `thick` | Borda grossa | ─ |
| `dashed` | Borda tracejada | ┈ |
| `dotted` | Borda pontilhada | ┈ |

### 3.2 Configurações de Bordas por Tema

```python
BORDER_CONFIGS = {
    'default': {
        'header_border': 'thin',      # Borda do cabeçalho
        'data_border': 'thin',        # Borda dos dados
        'border_color': '000000',     # Cor da borda (preto)
    },
    'corporate': {
        'header_border': 'thick',     # Cabeçalho com borda grossa
        'data_border': 'thin',        # Dados com borda fina
        'border_color': '1F4E78',     # Cor azul escuro
    }
}
```

### 3.3 Como Criar Novo Tema de Bordas

```python
BORDER_CONFIGS = {
    # ... temas existentes ...
    'meu_tema': {
        'header_border': 'medium',
        'data_border': 'dashed',
        'border_color': 'FF0000',  # Bordas vermelhas
    }
}
```

---

## 💰 4. CONFIGURAÇÃO DE FORMATOS DE MOEDA

### 4.1 Formatos Disponíveis

```python
CURRENCY_FORMATS = {
    'BRL': 'R$ #,##0.00',    # Real brasileiro
    'USD': 'US$ #,##0.00',   # Dólar americano
    'EUR': '€ #,##0.00',     # Euro
}
```

### 4.2 Como Criar Novo Formato

```python
CURRENCY_FORMATS = {
    # ... formatos existentes ...
    'MXN': 'MX$ #,##0.00',   # Peso mexicano
}
```

---

## 📅 5. CONFIGURAÇÃO DE FORMATOS DE DATA

### 5.1 Formatos Disponíveis

```python
DATE_FORMATS = {
    'pt_BR': 'dd/mm/yyyy',   # Brasileiro
    'en_US': 'mm/dd/yyyy',   # Americano
    'iso': 'yyyy-mm-dd',     # Internacional
}
```

### 5.2 Como Criar Novo Formato

```python
DATE_FORMATS = {
    # ... formatos existentes ...
    'custom': 'dd-mm-yyyy',  # Formato personalizado
}
```

---

## 🎨 6. TEMAS PRÉ-DEFINIDOS

### 6.1 Tema Padrão (default)
- **Cabeçalho**: Azul claro com texto preto
- **Dados contábeis**: Cinza claro com texto azul escuro
- **Bordas**: Finas e pretas

### 6.2 Tema Escuro (dark)
- **Cabeçalho**: Cinza escuro com texto branco
- **Dados contábeis**: Cinza médio com texto verde
- **Bordas**: Médias e brancas

### 6.3 Tema Corporativo (corporate)
- **Cabeçalho**: Azul escuro com texto branco
- **Dados contábeis**: Branco com texto azul escuro
- **Bordas**: Grossas no cabeçalho, finas nos dados

### 6.4 Tema Minimal (minimal)
- **Cabeçalho**: Cinza claro com texto preto
- **Dados contábeis**: Branco com texto preto
- **Bordas**: Apenas no cabeçalho

---

## 🔧 7. COMO APLICAR MUDANÇAS

### 7.1 Passo a Passo

1. **Abra o arquivo** `style_config.py`
2. **Localize a seção** que deseja modificar
3. **Altere os valores** conforme necessário
4. **Salve o arquivo**
5. **Execute o programa** novamente

### 7.2 Exemplo Prático

**Problema:** Quero um relatório com tema escuro e bordas grossas

**Solução:**
1. No `app.py`, mude a linha:
   ```python
   export_to_excel(
       {periodo: df_periodo}, 
       output_dir=OUTPUT_DIR,
       border_theme='dark'  # Mudou de 'default' para 'dark'
   )
   ```

---

## ⚠️ 8. DICAS IMPORTANTES

### 8.1 Cores
- **Sempre use códigos hexadecimais** (6 dígitos)
- **Teste a legibilidade** - texto escuro em fundo escuro não funciona
- **Mantenha consistência** - use cores similares no mesmo tema

### 8.2 Larguras
- **Valores muito pequenos** (< 8) podem cortar texto
- **Valores muito grandes** (> 30) deixam muito espaço vazio
- **Teste com dados reais** para encontrar o tamanho ideal

### 8.3 Bordas
- **Bordas grossas** no cabeçalho destacam a seção
- **Bordas finas** nos dados mantêm a legibilidade
- **Cores contrastantes** melhoram a aparência

---

## 🚨 9. SOLUÇÃO DE PROBLEMAS

### 9.1 Erro de Código de Cor
**Problema:** `ValueError: Invalid color code`
**Solução:** Verifique se o código tem exatamente 6 caracteres hexadecimais

### 9.2 Coluna Muito Larga/Estreita
**Problema:** Texto cortado ou muito espaço vazio
**Solução:** Ajuste o valor em `COLUMN_WIDTHS`

### 9.3 Bordas Não Aparecem
**Problema:** Bordas não são aplicadas
**Solução:** Verifique se o `border_theme` está correto no `app.py`

### 9.4 Formato de Moeda Errado
**Problema:** Valores não aparecem como moeda
**Solução:** Verifique se a coluna está em `CONTABEIS_COLS`

---

## 📞 10. SUPORTE

Se encontrar problemas:
1. **Verifique os logs** no arquivo `app.log`
2. **Teste com valores padrão** primeiro
3. **Faça mudanças pequenas** e teste cada uma
4. **Mantenha backup** do arquivo original

---

## 🎯 RESUMO RÁPIDO

Para mudanças comuns:

**Mudar cor do cabeçalho:**
```python
THEMES['default']['header_bg'] = 'NOVA_COR'
```

**Ajustar largura de coluna:**
```python
COLUMN_WIDTHS['NOME_COLUNA'] = NOVA_LARGURA
```

**Mudar tema de bordas:**
```python
# No app.py, mude border_theme='novo_tema'
```

**Adicionar nova coluna contábil:**
```python
CONTABEIS_COLS.append('NOVA_COLUNA')
``` 