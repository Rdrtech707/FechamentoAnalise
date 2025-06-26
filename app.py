# Arquivo: app.py

from config import MDB_FILE, MDB_PASSWORD
from modules.access_db import get_connection
from modules.extractors import get_ordens, get_contas, get_fcaixa
from modules.processors import process_recebimentos
from modules.exporters import export_to_excel


def main():
    # Pergunta mês e ano ao usuário
    year = input("Informe o ano (YYYY): ").strip()
    month = input("Informe o mês (MM): ").strip().zfill(2)
    periodo = f"{year}-{month}"

    # Conecta e extrai dados
    conn = get_connection(MDB_FILE, MDB_PASSWORD)
    ordens_df = get_ordens(conn)
    contas_df = get_contas(conn)
    fcaixa_df = get_fcaixa(conn)

    # Processa recebimentos
    recibos = process_recebimentos(ordens_df, contas_df, fcaixa_df)

    # Reordena colunas
    recibos = recibos[[
        'N° OS','DATA ENCERRAMENTO','VALOR TOTAL','VALOR MÃO DE OBRA',
        'VALOR PEÇAS','DESCONTO','VALOR PAGO','CARTÃO','DINHEIRO',
        'PIX','TROCO','VEÍCULO (PLACA)','CÓDIGO CLIENTE'
    ]]

    # Filtra pelo período desejado baseado em DATA_PGTO
    valid = recibos.dropna(subset=['DATA PGTO']).copy()
    valid['MES'] = valid['DATA PGTO'].dt.strftime('%Y-%m')

    if periodo in valid['MES'].unique():
        df_periodo = valid[valid['MES'] == periodo].drop(columns='MES')
        export_to_excel({periodo: df_periodo}, output_dir='data/recebimentos')
        print(f"Arquivo gerado: data/recebimentos/Recebimentos_{periodo}.xlsx")
    else:
        print(f"Nenhum registro encontrado para o período {periodo}.")

if __name__ == '__main__':
    main()