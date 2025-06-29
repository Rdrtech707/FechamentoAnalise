# Arquivo: style_config.py

# Colunas contábeis (valores financeiros)
CONTABEIS_COLS = [
    "VALOR TOTAL", "VALOR MÃO DE OBRA", "VALOR PEÇAS",
    "DESCONTO", "VALOR PAGO", "DEVEDOR", "CARTÃO", "DINHEIRO",
    "PIX", "TROCO"
]

# Formatos de moeda e data
CURRENCY_FORMATS = {
    'BRL': 'R$ #,##0.00',
    'USD': 'US$ #,##0.00',
    'EUR': '€ #,##0.00',
}

DATE_FORMATS = {
    'pt_BR': 'dd/mm/yyyy',
    'en_US': 'mm/dd/yyyy',
    'iso': 'yyyy-mm-dd',
}

# Configurações de largura das colunas - Expandido para auditoria unificada
COLUMN_WIDTHS = {
    # Colunas originais
    'N° OS': 12,
    'DATA ENCERRAMENTO': 18,
    'VALOR TOTAL': 15,
    'VALOR MÃO DE OBRA': 18,
    'VALOR PEÇAS': 15,
    'DESCONTO': 12,
    'VEÍCULO (PLACA)': 25,
    'CÓDIGO CLIENTE': 15,
    'VALOR PAGO': 15,
    'DEVEDOR': 12,
    'CARTÃO': 12,
    'DINHEIRO': 12,
    'PIX': 12,
    'TROCO': 12,
    'DATA PGTO': 15,
    
    # Colunas da auditoria de cartão
    'identificador': 25,
    'data_cartao': 15,
    'tipo_pagamento': 15,
    'valor_cartao': 15,
    'valor_gerado': 15,
    'diferenca': 15,
    'dif_percentual': 15,
    'status': 20,
    'os_correspondente': 15,
    'observacao': 50,
    
    # Colunas da auditoria PIX
    'data_banco': 15,
    'valor_banco': 15,
    'descricao_banco': 60,
    'data_recebimentos': 15,
    'valor_recebimentos': 15,
    'os_recebimentos': 15,
    
    # Novas colunas da auditoria PIX com agrupamento
    'remetente_banco': 30,
    'qtd_transacoes_banco': 20,
    'detalhes_banco': 80,
    'qtd_transacoes_recebimentos': 25,
    'detalhes_recebimentos': 80,
    'tipo_agrupamento': 20,
    'status_correspondencia': 25,
    
    # Colunas do resumo
    'Métrica': 35,
    'Valor': 20,
    'Mensagem': 50,
    
    # Larguras específicas para melhor legibilidade
    'descricao': 60,
    'origem': 15,
    'referencia': 20,
    'match_type': 15,
    'confidence': 15,
    'notes': 50,
    
    'default': 20,  # Largura padrão aumentada para colunas não especificadas
}

# Configurações de bordas
BORDER_STYLES = {
    'none': None,
    'thin': 'thin',
    'medium': 'medium',
    'thick': 'thick',
    'dashed': 'dashed',
    'dotted': 'dotted',
}

# Configurações de bordas por tema
BORDER_CONFIGS = {
    'default': {
        'header_border': 'thin',
        'data_border': 'thin',
        'border_color': '000000',  # Preto
    },
    'dark': {
        'header_border': 'medium',
        'data_border': 'thin',
        'border_color': 'FFFFFF',  # Branco
    },
    'corporate': {
        'header_border': 'thick',
        'data_border': 'thin',
        'border_color': '1F4E78',  # Azul escuro
    },
    'minimal': {
        'header_border': 'thin',
        'data_border': 'none',
        'border_color': 'CCCCCC',  # Cinza claro
    },
}

# Temas de cores (exemplo)
THEMES = {
    'default': {
        'header_bg': 'D9E1F2',
        'header_font': '000000',
        'contabil_bg': 'F2F2F2',
        'contabil_font': '1F4E78',
    },
    'dark': {
        'header_bg': '222222',
        'header_font': 'FFFFFF',
        'contabil_bg': '333333',
        'contabil_font': '00FF00',
    }
}

# Separadores decimais por idioma
DECIMAL_SEPARATORS = {
    'pt_BR': ',',
    'en_US': '.',
    'es_ES': ',',
} 