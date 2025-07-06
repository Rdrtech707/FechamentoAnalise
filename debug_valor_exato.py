import pandas as pd
import logging

def debug_valor_exato():
    """Debug para verificar comparação exata de valores"""
    
    # Configura logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)
    
    try:
        # Carrega recebimentos
        logger.info("Carregando recebimentos...")
        recebimentos_df = pd.read_excel("data/recebimentos/Recebimentos_2025-06.xlsx")
        
        # Calcula valor líquido
        recebimentos_df['VALOR_LIQUIDO'] = recebimentos_df['VALOR MÃO DE OBRA'] - recebimentos_df['DESCONTO']
        
        # Converte DATA PGTO para string
        recebimentos_df['DATA_PGTO_STR'] = pd.to_datetime(recebimentos_df['DATA PGTO']).dt.strftime('%d/%m/%Y')
        
        # Valor específico para testar
        valor_teste = 1264.54
        
        logger.info(f"Testando valor: {valor_teste}")
        logger.info(f"Tipo do valor: {type(valor_teste)}")
        
        # Procura recebimentos com esse valor exato
        matching_recebimentos = recebimentos_df[
            recebimentos_df['VALOR_LIQUIDO'].round(2) == round(valor_teste, 2)
        ]
        
        logger.info(f"Recebimentos encontrados com valor exato: {len(matching_recebimentos)}")
        
        if len(matching_recebimentos) > 0:
            for idx, row in matching_recebimentos.iterrows():
                os_numero = row['N° OS']
                mao_obra = row['VALOR MÃO DE OBRA']
                desconto = row['DESCONTO']
                valor_liquido = row['VALOR_LIQUIDO']
                
                logger.info(f"OS {os_numero}: M.O.={mao_obra}, Desconto={desconto}, Líquido={valor_liquido}")
                logger.info(f"  Tipo do valor líquido: {type(valor_liquido)}")
                logger.info(f"  Valor líquido == {valor_teste}: {valor_liquido == valor_teste}")
        else:
            logger.info("Nenhum recebimento encontrado com valor exato")
            
            # Mostra valores próximos
            logger.info("Valores próximos encontrados:")
            for idx, row in recebimentos_df.iterrows():
                valor_liquido = row['VALOR_LIQUIDO']
                diferenca = abs(valor_liquido - valor_teste)
                if diferenca <= 1:  # Diferença menor que 1 real
                    os_numero = row['N° OS']
                    mao_obra = row['VALOR MÃO DE OBRA']
                    desconto = row['DESCONTO']
                    
                    logger.info(f"OS {os_numero}: M.O.={mao_obra}, Desconto={desconto}, Líquido={valor_liquido}, Diferença={diferenca}")
                    logger.info(f"  Tipo do valor líquido: {type(valor_liquido)}")
                    logger.info(f"  Valor líquido == {valor_teste}: {valor_liquido == valor_teste}")
        
        # Testa com diferentes tipos de dados
        logger.info(f"\n=== TESTE DE TIPOS DE DADOS ===")
        logger.info(f"Valor teste (float): {valor_teste}")
        logger.info(f"Valor teste (str): {str(valor_teste)}")
        
        # Verifica se há problemas de precisão
        logger.info(f"\n=== VERIFICAÇÃO DE PRECISÃO ===")
        for idx, row in recebimentos_df.iterrows():
            valor_liquido = row['VALOR_LIQUIDO']
            if abs(valor_liquido - valor_teste) < 0.01:  # Diferença muito pequena
                os_numero = row['N° OS']
                mao_obra = row['VALOR MÃO DE OBRA']
                desconto = row['DESCONTO']
                
                logger.info(f"OS {os_numero}: M.O.={mao_obra}, Desconto={desconto}")
                logger.info(f"  Cálculo: {mao_obra} - {desconto} = {valor_liquido}")
                logger.info(f"  Valor líquido: {valor_liquido}")
                logger.info(f"  Valor teste: {valor_teste}")
                logger.info(f"  Diferença: {valor_liquido - valor_teste}")
                logger.info(f"  Comparação exata: {valor_liquido == valor_teste}")
                logger.info(f"  Comparação com round(2): {round(valor_liquido, 2) == round(valor_teste, 2)}")
                logger.info(f"  Comparação com round(4): {round(valor_liquido, 4) == round(valor_teste, 4)}")
                logger.info("")
        
        # Mostra todos os valores líquidos para debug
        logger.info(f"\n=== TODOS OS VALORES LÍQUIDOS ===")
        for idx, row in recebimentos_df.iterrows():
            os_numero = row['N° OS']
            mao_obra = row['VALOR MÃO DE OBRA']
            desconto = row['DESCONTO']
            valor_liquido = row['VALOR_LIQUIDO']
            
            if abs(valor_liquido - valor_teste) < 10:  # Valores próximos
                logger.info(f"OS {os_numero}: {mao_obra} - {desconto} = {valor_liquido}")
        
        # Verifica se existe algum recebimento com valor 1315 de mão de obra
        logger.info(f"\n=== VERIFICANDO OS 3939 ===")
        os_3939 = recebimentos_df[recebimentos_df['N° OS'] == 3939]
        if len(os_3939) > 0:
            row = os_3939.iloc[0]
            mao_obra = row['VALOR MÃO DE OBRA']
            desconto = row['DESCONTO']
            valor_liquido = row['VALOR_LIQUIDO']
            
            logger.info(f"OS 3939 encontrada:")
            logger.info(f"  M.O.: {mao_obra}")
            logger.info(f"  Desconto: {desconto}")
            logger.info(f"  Valor líquido: {valor_liquido}")
            logger.info(f"  Cálculo: {mao_obra} - {desconto} = {mao_obra - desconto}")
            logger.info(f"  Comparação com 1264.54: {valor_liquido == 1264.54}")
            logger.info(f"  Comparação com round: {round(valor_liquido, 2) == round(1264.54, 2)}")
        else:
            logger.info("OS 3939 não encontrada")
        
    except Exception as e:
        logger.error(f"Erro: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_valor_exato() 