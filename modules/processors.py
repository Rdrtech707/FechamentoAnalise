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
        'CODIGO': 'N° OS',
        'SAIDA': 'DATA ENCERRAMENTO',
        'V_MAO': 'VALOR MÃO DE OBRA',
        'V_PECAS': 'VALOR PEÇAS',
        'V_OUTROS': 'DESCONTO'
    })[[
        'N° OS','DATA ENCERRAMENTO','VALOR TOTAL',
        'VALOR MÃO DE OBRA','VALOR PEÇAS','DESCONTO','VEÍCULO (PLACA)'
    ]]

    # --- Prepara FCAIXA: extrai código numérico e soma receitas por forma ---
    fcaixa = fcaixa_df.copy()
    fcaixa['COD_CONTA'] = (
        fcaixa['COD_CONTA']
        .astype(str)
        .str.extract(r'R(\d+)', expand=False)
        .fillna('0')
        .astype(int)
    )
    pix_receita = fcaixa[fcaixa['FORMA'] == 5].groupby('COD_CONTA')['RECEITA'].sum()
    dinheiro_receita = fcaixa[fcaixa['FORMA'] == 0].groupby('COD_CONTA')['RECEITA'].sum()

    # --- Prepara CONTAS e faz merge com receitas isoladas ---
    contas = contas_df.copy()
    contas['CODIGO'] = pd.to_numeric(contas['CODIGO'], errors='coerce').fillna(0).astype(int)
    contas['OS'] = contas['REFERENCIA'].astype(str).str.extract(r'^O(\d+)$', expand=False)
    contas = contas.dropna(subset=['OS']).copy()
    contas['OS'] = contas['OS'].astype(int)
    contas = contas.merge(pix_receita.rename('RECEITA_PIX'),
                          left_on='CODIGO', right_index=True, how='left')
    contas = contas.merge(dinheiro_receita.rename('RECEITA_DINHEIRO'),
                          left_on='CODIGO', right_index=True, how='left')
    contas = contas.fillna(0)

    # --- Cálculo de DINHEIRO e PIX conforme regra correta ---
    contas['DINHEIRO'] = contas['ECF_DINHEIRO'] - contas['RECEITA_PIX']
    contas['PIX'] = contas['ECF_DINHEIRO'] - contas['RECEITA_DINHEIRO']

    # --- Garante que DATA_PGTO seja datetime e agrega por OS ---
    contas['DATA_PGTO'] = pd.to_datetime(contas['DATA_PGTO'], errors='coerce')
    agg = contas.groupby('OS').agg({
        'COD_CLIENTE': 'first',
        'VALOR': 'sum',
        'ECF_CARTAO': 'sum',
        'DINHEIRO': 'sum',
        'PIX': 'sum',
        'ECF_TROCO': 'sum',
        'DATA_PGTO': 'max'
    }).rename(columns={
        'COD_CLIENTE': 'CÓDIGO CLIENTE',
        'VALOR': 'VALOR PAGO',
        'ECF_CARTAO': 'CARTÃO',
        'ECF_TROCO': 'TROCO',
        'DATA_PGTO': 'DATA PGTO'
    })

    # --- Merge final com as ordens ---
    final = ordens_proc.merge(agg, left_on='N° OS', right_index=True, how='left')
    return final
