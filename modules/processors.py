# Arquivo: modules/processors.py
import pandas as pd


def process_recebimentos(
    ordens_df: pd.DataFrame,
    contas_df: pd.DataFrame,
    fcaixa_df: pd.DataFrame
) -> pd.DataFrame:
    """
    Monta a tabela consolidada de recebimentos:
    Colunas: N° OS, DATA ENCERRAMENTO, VALOR TOTAL, VALOR MÃO DE OBRA,
             VALOR PEÇAS, DESCONTO, VEÍCULO (PLACA), CÓDIGO CLIENTE,
             VALOR PAGO, CARTÃO, DINHEIRO, PIX, TROCO
    """
    # Prepara ordens
    ordens = ordens_df.copy()
    ordens['VALOR TOTAL'] = ordens[['V_MAO','V_PECAS','V_DESLOCA','V_TERCEIRO','V_OUTROS']].sum(axis=1)
    ordens['VEÍCULO (PLACA)'] = ordens['APARELHO'] + ' (' + ordens['MODELO'] + ')'
    ordens_proc = ordens[[
        'CODIGO','SAIDA','VALOR TOTAL','V_MAO','V_PECAS','V_OUTROS','VEÍCULO (PLACA)'
    ]].rename(columns={
        'CODIGO':'N° OS',
        'SAIDA':'DATA ENCERRAMENTO',
        'V_MAO':'VALOR MÃO DE OBRA',
        'V_PECAS':'VALOR PEÇAS',
        'V_OUTROS':'DESCONTO'
    })

    # Prepara fcaixa (soma por conta e forma)
    fcaixa = fcaixa_df.copy()
    fcaixa['COD_CONTA'] = pd.to_numeric(
        fcaixa['COD_CONTA'], errors='coerce'
    ).fillna(0).astype(int)
    fcaixa_sum = (
        fcaixa.groupby(['COD_CONTA','FORMA'])['RECEITA']
              .sum()
              .unstack(fill_value=0)
    )
    for forma in (0, 5):
        if forma not in fcaixa_sum.columns:
            fcaixa_sum[forma] = 0

    # Prepara contas e extrai OS
    contas = contas_df.copy()
    contas['CODIGO'] = pd.to_numeric(
        contas['CODIGO'], errors='coerce'
    ).fillna(0).astype(int)
    contas['OS'] = (
        contas['REFERENCIA']
        .astype(str)
        .str.extract(r'^O(\d+)$', expand=False)
    )
    contas = contas.dropna(subset=['OS']).copy()
    contas['OS'] = contas['OS'].astype(int)

    # remove as linhas sem OS válido
    contas = contas.dropna(subset=['OS']).copy()
    # converte para inteiro
    contas['OS'] = contas['OS'].astype(int)
    # Merge com fcaixa
    contas = contas.merge(
        fcaixa_sum,
        left_on='CODIGO',
        right_index=True,
        how='left'
    ).fillna(0)

    # Calcula DINHEIRO e PIX conforme instruções
    contas['DINHEIRO'] = contas['ECF_DINHEIRO'] - contas[5]
    contas['PIX'] = contas['ECF_DINHEIRO'] - contas[0]

    # Agrega por OS
    agg = contas.groupby('OS').agg({
        'COD_CLIENTE':'first',
        'VALOR':'sum',
        'ECF_CARTAO':'sum',
        'DINHEIRO':'sum',
        'PIX':'sum',
        'ECF_TROCO':'sum'
    }).rename(columns={
        'COD_CLIENTE':'CÓDIGO CLIENTE',
        'VALOR':'VALOR PAGO',
        'ECF_CARTAO':'CARTÃO',
        'ECF_TROCO':'TROCO'
    })

    # Junta ordens com pagamentos
    final = ordens_proc.merge(
        agg,
        left_on='N° OS',
        right_index=True,
        how='left'
    )
    return final