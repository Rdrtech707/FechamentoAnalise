import pandas as pd
import os
import logging

def export_to_json(df: pd.DataFrame, output_dir: str, filename: str, orient: str = 'records', force_ascii: bool = False, date_format: str = 'iso', indent: int = 2, logger: logging.Logger = None) -> str:
    """
    Exporta um DataFrame para um arquivo JSON.
    
    Args:
        df: DataFrame a ser exportado
        output_dir: Diretório de saída
        filename: Nome do arquivo (sem extensão)
        orient: Orientação do JSON (default: 'records')
        force_ascii: Se deve forçar ASCII (default: False)
        date_format: Formato de datas (default: 'iso')
        indent: Indentação do JSON (default: 2)
        logger: Logger opcional para logs
    Returns:
        Caminho do arquivo JSON gerado
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        if logger:
            logger.info(f"Pasta criada: {output_dir}")
    
    json_path = os.path.join(output_dir, f"{filename}.json")
    try:
        df.to_json(json_path, orient=orient, force_ascii=force_ascii, date_format=date_format, indent=indent)
        if logger:
            logger.info(f"Arquivo JSON gerado com sucesso em {json_path}")
        return json_path
    except Exception as e:
        if logger:
            logger.error(f"Erro ao exportar para JSON: {e}")
        raise 