# Arquivo: app.py

from config import MDB_FILE, MDB_PASSWORD
from modules.access_db import get_connection
from modules.extractors import get_ordens, get_contas, get_fcaixa
from modules.processors import process_recebimentos


def main():
    # Conecta ao banco e extrai dados
    conn = get_connection(MDB_FILE, MDB_PASSWORD)
    ordens_df = get_ordens(conn)
    contas_df = get_contas(conn)
    fcaixa_df = get_fcaixa(conn)

    # Processa recebimentos
    receb_df = process_recebimentos(ordens_df, contas_df, fcaixa_df)
    print("Tabela de recebimentos por OS:")
    print(receb_df)


if __name__ == "__main__":
    main()