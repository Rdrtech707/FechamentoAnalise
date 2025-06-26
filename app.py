# Arquivo: app.py

from config import MDB_FILE, MDB_PASSWORD
from modules.access_db import get_connection
from modules.extractors import get_ordens, get_contas, get_fcaixa
from modules.processors import process_recebimentos
from modules.exporters import export_to_excel


def main():
    conn = get_connection(MDB_FILE, MDB_PASSWORD)
    ordens_df = get_ordens(conn)
    contas_df = get_contas(conn)
    fcaixa_df = get_fcaixa(conn)

    recibos = process_recebimentos(ordens_df, contas_df, fcaixa_df)

        # Reordena colunas conforme nova ordem
    recibos = recibos[[
        'N° OS',
        'DATA ENCERRAMENTO',
        'VALOR TOTAL',
        'VALOR MÃO DE OBRA',
        'VALOR PEÇAS',
        'DESCONTO',
        'VALOR PAGO',
        'CARTÃO',
        'DINHEIRO',
        'PIX',
        'TROCO',
        'VEÍCULO (PLACA)',
        'CÓDIGO CLIENTE'
    ]]

    # --- Nova Parte: agrupamento por mês e exportação ---
    # Filtra registros com data válida
    valid = recibos.dropna(subset=['DATA ENCERRAMENTO']).copy()
    # Extrai ano-mês
    valid['MES'] = valid['DATA ENCERRAMENTO'].dt.strftime('%Y-%m')
    # Cria dicionário de DataFrames por mês
    dfs_by_month = {mes: df.drop(columns='MES') for mes, df in valid.groupby('MES')}
    # Exporta para Excel
    export_to_excel(dfs_by_month, output_dir='data/recebimentos')
    print(f"Exportados meses: {list(dfs_by_month.keys())}")

if __name__ == '__main__':
    main()