import pandas as pd


def process_recebimentos(
    ordens_df: pd.DataFrame,
    contas_df: pd.DataFrame,
    fcaixa_df: pd.DataFrame,
    periodo: str = None
) -> pd.DataFrame:
    """
    Monta a tabela consolidada de recebimentos:
    Colunas: N° OS, DATA ENCERRAMENTO, VALOR TOTAL, VALOR MÃO DE OBRA,
             VALOR PEÇAS, DESCONTO, VEÍCULO (PLACA), CÓDIGO CLIENTE,
             VALOR PAGO, DEVEDOR, CARTÃO, DINHEIRO, PIX, TROCO
    
    Args:
        periodo: Formato 'YYYY-MM' para filtrar DATA_PGTO (ex: '2024-01')
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

    # --- Prepara CONTAS para VALOR PAGO (PAGO = 'S') ---
    contas_pagas = contas_df.copy()
    contas_pagas['CODIGO'] = pd.to_numeric(contas_pagas['CODIGO'], errors='coerce').fillna(0).astype(int)
    contas_pagas['OS'] = contas_pagas['REFERENCIA'].astype(str).str.extract(r'^O(\d+)$', expand=False)
    contas_pagas = contas_pagas.dropna(subset=['OS']).copy()
    contas_pagas['OS'] = contas_pagas['OS'].astype(int)
    
    # --- Filtra apenas contas pagas (PAGO = 'S') ---
    contas_pagas = contas_pagas[contas_pagas['PAGO'] == 'S'].copy()
    
    # --- Filtra por DATA_PGTO do período especificado ---
    if periodo:
        contas_pagas['DATA_PGTO'] = pd.to_datetime(contas_pagas['DATA_PGTO'], errors='coerce')
        contas_pagas['MES_PGTO'] = contas_pagas['DATA_PGTO'].dt.strftime('%Y-%m')
        contas_pagas = contas_pagas[contas_pagas['MES_PGTO'] == periodo].copy()
        contas_pagas = contas_pagas.drop(columns=['MES_PGTO'])
    
    contas_pagas = contas_pagas.merge(pix_receita.rename('RECEITA_PIX'),
                          left_on='CODIGO', right_index=True, how='left')
    contas_pagas = contas_pagas.merge(dinheiro_receita.rename('RECEITA_DINHEIRO'),
                          left_on='CODIGO', right_index=True, how='left')
    contas_pagas = contas_pagas.fillna(0)

    # --- Cálculo de DINHEIRO e PIX conforme regra correta ---
    contas_pagas['DINHEIRO'] = contas_pagas['ECF_DINHEIRO'] - contas_pagas['RECEITA_PIX']
    contas_pagas['PIX'] = contas_pagas['ECF_DINHEIRO'] - contas_pagas['RECEITA_DINHEIRO']

    # --- Garante que DATA_PGTO seja datetime e agrega por OS ---
    contas_pagas['DATA_PGTO'] = pd.to_datetime(contas_pagas['DATA_PGTO'], errors='coerce')
    agg_pagas = contas_pagas.groupby('OS').agg({
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

    # --- Prepara CONTAS para DEVEDOR (PAGO = 'N') ---
    contas_devidas = contas_df.copy()
    contas_devidas['CODIGO'] = pd.to_numeric(contas_devidas['CODIGO'], errors='coerce').fillna(0).astype(int)
    contas_devidas['OS'] = contas_devidas['REFERENCIA'].astype(str).str.extract(r'^O(\d+)$', expand=False)
    contas_devidas = contas_devidas.dropna(subset=['OS']).copy()
    contas_devidas['OS'] = contas_devidas['OS'].astype(int)
    
    # --- Filtra apenas contas devidas (PAGO = 'N') ---
    contas_devidas = contas_devidas[contas_devidas['PAGO'] == 'N'].copy()
    
    # --- Agrega DEVEDOR por OS ---
    agg_devidas = contas_devidas.groupby('OS')['VALOR'].sum().rename('DEVEDOR')

    # --- Merge final com as ordens ---
    final = ordens_proc.merge(agg_pagas, left_on='N° OS', right_index=True, how='left')
    final = final.merge(agg_devidas, left_on='N° OS', right_index=True, how='left')
    
    # --- Preenche valores nulos com 0 ---
    final['DEVEDOR'] = final['DEVEDOR'].fillna(0)
    
    return final
