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
    # --- Prepara ordens ---
    ordens = ordens_df.copy()
    ordens['VALOR TOTAL'] = ordens[['V_MAO','V_PECAS','V_DESLOCA','V_TERCEIRO','V_OUTROS']].sum(axis=1)
    ordens['VEÍCULO (PLACA)'] = ordens['APARELHO'] + ' (' + ordens['MODELO'] + ')'
    ordens_proc = ordens.rename(columns={
        'CODIGO':'N° OS', 'SAIDA':'DATA ENCERRAMENTO',
        'V_MAO':'VALOR MÃO DE OBRA','V_PECAS':'VALOR PEÇAS','V_OUTROS':'DESCONTO'
    })[['N° OS','DATA ENCERRAMENTO','VALOR TOTAL','VALOR MÃO DE OBRA','VALOR PEÇAS','DESCONTO','VEÍCULO (PLACA)']]

    # --- Prepara FCAIXA ---
    fcaixa = fcaixa_df.copy()
    fcaixa['COD_CONTA'] = pd.to_numeric(fcaixa['COD_CONTA'], errors='coerce').fillna(0).astype(int)
    fcaixa_sum = fcaixa.groupby(['COD_CONTA','FORMA'])['RECEITA'].sum().unstack(fill_value=0)
    for forma in (0,5):
        if forma not in fcaixa_sum.columns:
            fcaixa_sum[forma] = 0

    # --- Prepara CONTAS e faz merge ---
    contas = contas_df.copy()
    contas['CODIGO'] = pd.to_numeric(contas['CODIGO'], errors='coerce').fillna(0).astype(int)
    contas['OS'] = contas['REFERENCIA'].astype(str).str.extract(r'^O(\d+)$', expand=False)
    contas = contas.dropna(subset=['OS']).copy()
    contas['OS'] = contas['OS'].astype(int)
    contas = contas.merge(fcaixa_sum, left_on='CODIGO', right_index=True, how='left').fillna(0)
    contas['DINHEIRO'] = contas['ECF_DINHEIRO'] - contas.get(5,0)
    contas['PIX'] = contas['ECF_DINHEIRO'] - contas.get(0,0)

# --- Agrega por OS com DATA_PGTO ---
    agg = contas.groupby('OS').agg({
        'COD_CLIENTE':'first',
        'VALOR':'sum',
        'ECF_CARTAO':'sum',
        'DINHEIRO':'sum',
        'PIX':'sum',
        'ECF_TROCO':'sum',
        'DATA_PGTO':'max'
    }).rename(columns={
        'COD_CLIENTE':'CÓDIGO CLIENTE',
        'VALOR':'VALOR PAGO',
        'ECF_CARTAO':'CARTÃO',
        'ECF_TROCO':'TROCO',
        'DATA_PGTO':'DATA PGTO'
    })

    final = ordens_proc.merge(agg, left_on='N° OS', right_index=True, how='left')
    return final