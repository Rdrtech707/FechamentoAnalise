import pandas as pd
import logging
from typing import Optional, Tuple


def _prepara_ordens(ordens_df: pd.DataFrame) -> pd.DataFrame:
    """
    Prepara e processa dados da tabela ORDEMS.
    
    Args:
        ordens_df: DataFrame da tabela ORDEMS
        
    Returns:
        pd.DataFrame: DataFrame processado com colunas renomeadas
    """
    logging.info("[PROCESSO] Processando tabela ORDEMS...")
    ordens = ordens_df.copy()
    
    # Calcula VALOR TOTAL conforme especificação
    ordens['VALOR TOTAL'] = ordens[['V_MAO', 'V_PECAS', 'V_DESLOCA', 'V_TERCEIRO', 'V_OUTROS']].sum(axis=1)
    
    # Cria VEÍCULO (PLACA) conforme especificação
    ordens['VEÍCULO (PLACA)'] = ordens['APARELHO'].astype(str) + ' (' + ordens['MODELO'].astype(str) + ')'
    
    # Renomeia colunas conforme especificação
    ordens_proc = ordens.rename(columns={
        'CODIGO': 'N° OS',
        'SAIDA': 'DATA ENCERRAMENTO',
        'V_MAO': 'VALOR MÃO DE OBRA',
        'V_PECAS': 'VALOR PEÇAS',
        'V_OUTROS': 'DESCONTO'
    })[[
        'N° OS', 'DATA ENCERRAMENTO', 'VALOR TOTAL',
        'VALOR MÃO DE OBRA', 'VALOR PEÇAS', 'DESCONTO', 'VEÍCULO (PLACA)'
    ]]
    
    logging.info(f"[OK] ORDEMS processada: {len(ordens_proc)} registros")
    return ordens_proc


def _extrai_receitas(fcaixa_df: pd.DataFrame) -> Tuple[pd.Series, pd.Series]:
    """
    Extrai receitas por forma de pagamento da tabela FCAIXA.
    
    Args:
        fcaixa_df: DataFrame da tabela FCAIXA
        
    Returns:
        Tuple[pd.Series, pd.Series]: (pix_receita, dinheiro_receita)
    """
    logging.info("[DINHEIRO] Processando tabela FCAIXA...")
    fcaixa = fcaixa_df.copy()
    
    # Extrai código numérico da coluna COD_CONTA
    fcaixa['COD_CONTA_NUM'] = (
        fcaixa['COD_CONTA']
        .astype(str)
        .str.extract(r'(\d+)', expand=False)
        .fillna('0')
        .astype(int)
    )
    
    # Calcula receitas por forma de pagamento
    pix_receita = fcaixa[fcaixa['FORMA'] == 0].groupby('COD_CONTA_NUM')['RECEITA'].sum()
    dinheiro_receita = fcaixa[fcaixa['FORMA'] == 5].groupby('COD_CONTA_NUM')['RECEITA'].sum()
    
    logging.info(f"[OK] FCAIXA processada: {len(fcaixa)} registros")
    logging.info(f"   Receitas PIX (FORMA=0): {len(pix_receita)} registros")
    logging.info(f"   Receitas Dinheiro (FORMA=5): {len(dinheiro_receita)} registros")
    
    return pix_receita, dinheiro_receita


def _valida_referencia_os(referencia: str) -> bool:
    """
    Valida se a referência está no formato correto para OS.
    
    Args:
        referencia: String da referência
        
    Returns:
        bool: True se estiver no formato O\d+
    """
    import re
    return bool(re.match(r'^O\d+$', str(referencia)))


def _processa_contas_pagas(
    contas_df: pd.DataFrame, 
    periodo: Optional[str],
    pix_receita: pd.Series,
    dinheiro_receita: pd.Series
) -> pd.DataFrame:
    """
    Processa contas pagas (PAGO = 'S') e calcula formas de pagamento.
    
    Args:
        contas_df: DataFrame da tabela CONTAS
        periodo: Período para filtrar (YYYY-MM)
        pix_receita: Series com receitas PIX
        dinheiro_receita: Series com receitas Dinheiro
        
    Returns:
        pd.DataFrame: DataFrame agregado por OS
    """
    logging.info("[CARTAO] Processando tabela CONTAS (pagas)...")
    contas_pagas = contas_df.copy()
    
    # Converte CODIGO para numérico
    contas_pagas['CODIGO'] = pd.to_numeric(contas_pagas['CODIGO'], errors='coerce').fillna(0).astype(int)
    
    # Valida e extrai número da OS da referência
    contas_pagas['REFERENCIA_VALIDA'] = contas_pagas['REFERENCIA'].apply(_valida_referencia_os)
    contas_pagas['OS'] = contas_pagas['REFERENCIA'].astype(str).str.extract(r'^O(\d+)$', expand=False)
    
    # Log de referências inválidas
    refs_invalidas = contas_pagas[~contas_pagas['REFERENCIA_VALIDA']]['REFERENCIA'].unique()
    if len(refs_invalidas) > 0:
        logging.warning(f"   Referências inválidas encontradas: {refs_invalidas[:10]}...")
    
    contas_pagas = contas_pagas.dropna(subset=['OS']).copy()
    contas_pagas['OS'] = contas_pagas['OS'].astype(int)
    
    # Filtra apenas contas pagas (PAGO = 'S')
    contas_pagas = contas_pagas[contas_pagas['PAGO'] == 'S'].copy()
    
    # Filtra por DATA_PGTO do período especificado
    if periodo:
        contas_pagas['DATA_PGTO'] = pd.to_datetime(contas_pagas['DATA_PGTO'], errors='coerce')
        contas_pagas['MES_PGTO'] = contas_pagas['DATA_PGTO'].dt.strftime('%Y-%m')
        contas_pagas = contas_pagas[contas_pagas['MES_PGTO'] == periodo].copy()
        contas_pagas = contas_pagas.drop(columns=['MES_PGTO'])
        logging.info(f"   Filtrado para período: {periodo}")
    
    # Merge com receitas do FCAIXA para cálculos de DINHEIRO e PIX
    contas_pagas = contas_pagas.merge(
        pix_receita.rename('RECEITA_PIX'),
        left_on='CODIGO', right_index=True, how='left'
    )
    contas_pagas = contas_pagas.merge(
        dinheiro_receita.rename('RECEITA_DINHEIRO'),
        left_on='CODIGO', right_index=True, how='left'
    )
    contas_pagas = contas_pagas.fillna(0)
    
    # Calcula DINHEIRO e PIX conforme especificação CORRETA
    # DINHEIRO = ECF_DINHEIRO - RECEITA (FORMA = 5)
    # PIX = ECF_DINHEIRO - RECEITA (FORMA = 0)
    contas_pagas['DINHEIRO'] = contas_pagas['ECF_DINHEIRO'] - contas_pagas['RECEITA_DINHEIRO']
    contas_pagas['PIX'] = contas_pagas['ECF_DINHEIRO'] - contas_pagas['RECEITA_PIX']
    
    # Garante que DATA_PGTO seja datetime e agrega por OS
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
    
    logging.info(f"[OK] CONTAS (pagas) processada: {len(agg_pagas)} registros")
    return agg_pagas


def _processa_contas_devidas(contas_df: pd.DataFrame) -> pd.Series:
    """
    Processa contas devidas (PAGO = 'N') para cálculo do DEVEDOR.
    
    Args:
        contas_df: DataFrame da tabela CONTAS
        
    Returns:
        pd.Series: Series com valores devidos por OS
    """
    logging.info("[DEVIDO] Processando tabela CONTAS (devidas)...")
    contas_devidas = contas_df.copy()
    
    # Converte CODIGO para numérico
    contas_devidas['CODIGO'] = pd.to_numeric(contas_devidas['CODIGO'], errors='coerce').fillna(0).astype(int)
    
    # Valida e extrai número da OS da referência
    contas_devidas['REFERENCIA_VALIDA'] = contas_devidas['REFERENCIA'].apply(_valida_referencia_os)
    contas_devidas['OS'] = contas_devidas['REFERENCIA'].astype(str).str.extract(r'^O(\d+)$', expand=False)
    contas_devidas = contas_devidas.dropna(subset=['OS']).copy()
    contas_devidas['OS'] = contas_devidas['OS'].astype(int)
    
    # Filtra apenas contas devidas (PAGO = 'N')
    contas_devidas = contas_devidas[contas_devidas['PAGO'] == 'N'].copy()
    
    # Agrega DEVEDOR por OS
    agg_devidas = contas_devidas.groupby('OS')['VALOR'].sum().rename('DEVEDOR')
    
    logging.info(f"[OK] CONTAS (devidas) processada: {len(agg_devidas)} registros")
    return agg_devidas


def process_recebimentos(
    ordens_df: pd.DataFrame,
    contas_df: pd.DataFrame,
    fcaixa_df: pd.DataFrame,
    periodo: Optional[str] = None
) -> pd.DataFrame:
    """
    Monta a tabela consolidada de recebimentos conforme especificações:
    
    Mapeamento:
    - N° OS = CODIGO da tabela ORDEMS
    - DATA ENCERRAMENTO = SAIDA da tabela ORDEMS
    - VALOR TOTAL = soma de (V_MAO, V_PECAS, V_DESLOCA, V_TERCEIRO, V_OUTROS) da tabela ORDEMS
    - VALOR MÃO DE OBRA = V_MAO da tabela ORDEMS
    - VALOR PEÇAS = V_PECAS da tabela ORDEMS
    - DESCONTO = V_OUTROS da tabela ORDEMS
    - VEÍCULO (PLACA) = "APARELHO + (MODELO)" da tabela ORDEMS
    - CÓDIGO CLIENTE = COD_CLIENTE da tabela CONTAS
    - VALOR PAGO = soma de todos os valores em VALOR respectivos a ordem de serviço
    - CARTÃO = ECF_CARTAO
    - DINHEIRO = ECF_DINHEIRO - RECEITA (se a RECEITA respectiva tiver FORMA = 5)
    - PIX = ECF_DINHEIRO - RECEITA (se a RECEITA respectiva tiver FORMA = 0)
    - TROCO = ECF_TROCO da tabela CONTAS
    
    Args:
        ordens_df: DataFrame da tabela ORDEMS
        contas_df: DataFrame da tabela CONTAS
        fcaixa_df: DataFrame da tabela FCAIXA
        periodo: Formato 'YYYY-MM' para filtrar DATA_PGTO (ex: '2024-01')
        
    Returns:
        pd.DataFrame: Tabela consolidada de recebimentos
    """
    try:
        logging.info("[PROCESSO] Iniciando processamento de recebimentos...")
        
        # Prepara ordens
        ordens_proc = _prepara_ordens(ordens_df)
        
        # Extrai receitas
        pix_receita, dinheiro_receita = _extrai_receitas(fcaixa_df)
        
        # Processa contas pagas
        agg_pagas = _processa_contas_pagas(contas_df, periodo, pix_receita, dinheiro_receita)
        
        # Processa contas devidas
        agg_devidas = _processa_contas_devidas(contas_df)
        
        # Merge final com as ordens
        logging.info("[MERGE] Fazendo merge final...")
        final = ordens_proc.merge(agg_pagas, left_on='N° OS', right_index=True, how='left')
        final = final.merge(agg_devidas, left_on='N° OS', right_index=True, how='left')
        
        # Preenche valores nulos com 0
        final['DEVEDOR'] = final['DEVEDOR'].fillna(0)
        final['VALOR PAGO'] = final['VALOR PAGO'].fillna(0)
        final['CARTÃO'] = final['CARTÃO'].fillna(0)
        final['DINHEIRO'] = final['DINHEIRO'].fillna(0)
        final['PIX'] = final['PIX'].fillna(0)
        final['TROCO'] = final['TROCO'].fillna(0)
        
        # Reordena colunas conforme especificação
        colunas_finais = [
            'N° OS', 'DATA ENCERRAMENTO', 'VALOR TOTAL', 'VALOR MÃO DE OBRA',
            'VALOR PEÇAS', 'DESCONTO', 'VEÍCULO (PLACA)', 'CÓDIGO CLIENTE',
            'VALOR PAGO', 'DEVEDOR', 'CARTÃO', 'DINHEIRO', 'PIX', 'TROCO', 'DATA PGTO'
        ]
        
        final = final[colunas_finais]
        
        logging.info(f"[OK] Processamento concluído: {len(final)} registros finais")
        logging.info(f"   Colunas finais: {list(final.columns)}")
        
        return final
        
    except Exception as e:
        error_msg = f"Erro no processamento de recebimentos: {e}"
        logging.error(error_msg)
        raise Exception(error_msg)
