# Arquivo: modules/access_db.py

import pyodbc


def get_connection(mdb_file: str, password: str):
    """
    Conecta ao .mdb/.accdb usando ODBC.
    """
    conn_str = (
        r"DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};"
        rf"DBQ={mdb_file};"
        rf"PWD={password};"
    )
    return pyodbc.connect(conn_str)