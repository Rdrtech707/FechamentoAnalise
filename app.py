# Arquivo: app.py

from config import MDB_FILE, MDB_PASSWORD
from modules.access_db import get_connection
from modules.extractors import get_ordens, get_contas, get_fcaixa


def main():
    print("[LOG] Iniciando aplicação...")
    # Conecta ao banco
    print("[LOG] Conectando ao banco de dados...")
    conn = get_connection(MDB_FILE, MDB_PASSWORD)
    print("[LOG] Conexão estabelecida com sucesso!")

    # Extrai dados
    print("[LOG] Extraindo ordens...")
    ordens_df = get_ordens(conn)
    print(f"[LOG] Ordens extraídas: {len(ordens_df)} registros.")

    print("[LOG] Extraindo contas...")
    contas_df = get_contas(conn)
    print(f"[LOG] Contas extraídas: {len(contas_df)} registros.")

    print("[LOG] Extraindo fcaixa...")
    fcaixa_df = get_fcaixa(conn)
    print(f"[LOG] Fcaixa extraídas: {len(fcaixa_df)} registros.")

    # Para testar extração, mostramos as primeiras linhas
    print("Ordens extraídas:")
    print(ordens_df.head())
    print("Contas extraídas:")
    print(contas_df.head())
    print("Fcaixa extraídas:")
    print(fcaixa_df.head())
    print("[LOG] Execução finalizada com sucesso!")


if __name__ == "__main__":
    main()