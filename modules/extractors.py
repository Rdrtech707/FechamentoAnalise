# Arquivo: modules/extractors.py

import pandas as pd


def get_ordens(conn) -> pd.DataFrame:
    """
    Extrai dados da tabela ORDEMS, excluindo serviços com SITUACAO = 11.
    """
    query = """
    SELECT
        CODIGO,
        SAIDA,
        V_MAO,
        V_PECAS,
        V_DESLOCA,
        V_TERCEIRO,
        V_OUTROS,
        APARELHO,
        MODELO,
        SITUACAO
    FROM ORDEMS
    """
    df = pd.read_sql_query(query, conn, parse_dates=["SAIDA"])
    # Exclui ordens com SITUACAO == 11
    df = df[df['SITUACAO'] != 11].copy()
    # Remove coluna SITUACAO
    return df.drop(columns=['SITUACAO'])


def get_contas(conn) -> pd.DataFrame:
    """
    Extrai dados da tabela CONTAS:
    - CODIGO, TIPO, COD_CLIENTE, PAGO, OBSERVACAO,
      VALOR, REFERENCIA, ECF_DINHEIRO, ECF_CARTAO,
      ECF_TROCO, DATA_PGTO
    """
    query = """
    SELECT
        CODIGO,
        TIPO,
        COD_CLIENTE,
        PAGO,
        OBSERVACAO,
        VALOR,
        REFERENCIA,
        ECF_DINHEIRO,
        ECF_CARTAO,
        ECF_TROCO,
        DATA_PGTO
    FROM CONTAS
    """
    df = pd.read_sql_query(query, conn, parse_dates=["DATA_PGTO"])
    return df


def get_fcaixa(conn) -> pd.DataFrame:
    """
    Extrai dados da tabela FCAIXA:
    - RECEITA, COD_CONTA, FORMA
    """
    query = """
    SELECT
        RECEITA,
        COD_CONTA,
        FORMA
    FROM FCAIXA
    """
    df = pd.read_sql_query(query, conn)
    return df