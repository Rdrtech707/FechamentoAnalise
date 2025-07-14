import pyodbc
import json
import re
import sys
import os
from datetime import datetime

# Adiciona o diretório pai ao path para importar config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import MDB_FILE, MDB_PASSWORD

# Função para identificar se é CPF ou CNPJ
def identificar_cpf_cnpj(valor):
    valor = re.sub(r'\D', '', str(valor))
    if len(valor) == 11:
        return 'CPF', valor
    elif len(valor) == 14:
        return 'CNPJ', valor
    else:
        return 'DESCONHECIDO', valor

def solicitar_mes_ano():
    """Solicita ao usuário o mês e ano desejados"""
    while True:
        try:
            print("\n=== EXTRATOR DE INFORMAÇÕES DE OS ===")
            print("Digite o mês e ano desejados:")
            mes = int(input("Mês (1-12): "))
            ano = int(input("Ano (ex: 2024): "))
            
            if 1 <= mes <= 12 and 2000 <= ano <= 2100:
                return mes, ano
            else:
                print("❌ Mês deve ser entre 1-12 e ano entre 2000-2100")
        except ValueError:
            print("❌ Digite apenas números válidos")

# Função principal para extrair e montar o JSON
def extrair_os_info(caminho_banco, mes, ano):
    conn_str = (
        r'DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};'
        f'DBQ={caminho_banco};'
        f'PWD={MDB_PASSWORD};'
    )
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()

    # Query principal com JOIN entre as tabelas (sem filtro de data)
    query = """
    SELECT 
        o.CODIGO as NUMERO_OS,
        cl.CPF_CNPJ,
        cl.IE_RG as INSCRICAO_ESTADUAL,
        cl.NOME as NOME_RAZAO_SOCIAL,
        cl.CEP,
        cl.ENDERECO as LOGRADOURO,
        cl.NUMERO,
        cl.COMPLEM as COMPLEMENTO,
        cl.BAIRRO,
        cl.CIDADE as MUNICIPIO,
        cl.TELEFONE,
        cl.EMAIL,
        (o.V_MAO - o.V_OUTROS) as VALOR_TOTAL_SERVICOS
    FROM ORDEMS o
    LEFT JOIN CLIENTES cl ON o.COD_CLIENTE = cl.CODIGO
    ORDER BY o.CODIGO
    """
    
    cursor.execute(query)
    resultados = cursor.fetchall()
    
    # Buscar dados de pagamento separadamente
    dados_pagamento = buscar_dados_pagamento(cursor, mes, ano)
    
    # Filtrar resultados por mês/ano
    resultados_filtrados = []
    for row in resultados:
        numero_os = row.NUMERO_OS
        if numero_os in dados_pagamento:
            data_pagamento = dados_pagamento[numero_os]
            resultados_filtrados.append((row, data_pagamento))
    
    resultados = resultados_filtrados

    lista_os = []
    for row, data_pagamento in resultados:
        # Identificar CPF ou CNPJ
        documento = row.CPF_CNPJ if row.CPF_CNPJ else ''
        tipo_doc, doc_formatado = identificar_cpf_cnpj(documento)
        
        # Buscar serviços da OS
        servicos = buscar_servicos_os(cursor, row.NUMERO_OS)
        
        # Formatar data de pagamento
        data_pagamento_str = data_pagamento.strftime('%d/%m/%Y') if data_pagamento else ''
        
        os_info = {
            'NUMERO_OS': row.NUMERO_OS,
            'DATA_PAGAMENTO': data_pagamento_str,
            'CPF_OU_CNPJ': doc_formatado,
            'INSCRICAO_ESTADUAL': row.INSCRICAO_ESTADUAL if tipo_doc == 'CNPJ' else '',
            'NOME_OU_RAZAO_SOCIAL': row.NOME_RAZAO_SOCIAL or '',
            'CEP': row.CEP or '',
            'LOGRADOURO': row.LOGRADOURO or '',
            'NUMERO': row.NUMERO or '',
            'COMPLEMENTO': row.COMPLEMENTO or '',
            'BAIRRO': row.BAIRRO or '',
            'MUNICIPIO': row.MUNICIPIO or '',
            'TELEFONE': row.TELEFONE or '',
            'EMAIL': row.EMAIL or '',
            'SERVICOS': servicos,
            'VALOR_TOTAL_SERVICOS': float(row.VALOR_TOTAL_SERVICOS) if row.VALOR_TOTAL_SERVICOS else 0.0
        }
        lista_os.append(os_info)

    conn.close()
    return lista_os

def buscar_dados_pagamento(cursor, mes, ano):
    """Busca as datas de pagamento para um mês/ano específico"""
    query_pagamento = """
    SELECT REFERENCIA, DATA_PGTO
    FROM CONTAS 
    WHERE MONTH(DATA_PGTO) = ? AND YEAR(DATA_PGTO) = ?
    """
    cursor.execute(query_pagamento, (mes, ano))
    pagamentos = cursor.fetchall()
    
    dados_pagamento = {}
    for pagamento in pagamentos:
        referencia = pagamento.REFERENCIA
        if referencia.startswith('O'):
            numero_os = int(referencia[1:])  # Remove o 'O' e converte para int
            dados_pagamento[numero_os] = pagamento.DATA_PGTO
    
    return dados_pagamento

def buscar_servicos_os(cursor, numero_os):
    """Busca os serviços de uma OS específica"""
    query_servicos = """
    SELECT DESCRICAO, TOTAL
    FROM OS_SERVICOS 
    WHERE OS_NUM = ?
    ORDER BY DESCRICAO
    """
    cursor.execute(query_servicos, (numero_os,))
    servicos = cursor.fetchall()
    
    lista_servicos = []
    for servico in servicos:
        lista_servicos.append({
            'descricao': servico.DESCRICAO or '',
            'valor': float(servico.TOTAL) if servico.TOTAL else 0.0
        })
    
    return lista_servicos

if __name__ == "__main__":
    # Solicitar mês e ano ao usuário
    mes, ano = solicitar_mes_ano()
    
    print(f"\n🔄 Extraindo dados de {mes:02d}/{ano}...")
    
    # Extrair dados
    dados_os = extrair_os_info(MDB_FILE, mes, ano)
    
    # Gerar nome do arquivo com mês/ano
    nome_arquivo = f"os_servicos_{ano}_{mes:02d}.json"
    caminho_arquivo = f"../data/json/os_servicos/{nome_arquivo}"
    
    # Salvar JSON
    with open(caminho_arquivo, "w", encoding="utf-8") as f:
        json.dump(dados_os, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Arquivo {nome_arquivo} gerado com sucesso!")
    print(f"📊 Total de OS encontradas: {len(dados_os)}")
    print(f"📁 Local: data/json/os_servicos/{nome_arquivo}") 