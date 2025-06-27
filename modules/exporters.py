import os
import pandas as pd
from openpyxl.utils import get_column_letter
from openpyxl.styles import Alignment


def export_to_excel(dataframes_by_month: dict, output_dir: str):
    """
    Salva cada DataFrame em planilhas Excel separadas por mês,
    ajustando automaticamente a largura das colunas e formatando
    colunas numéricas em estilo contábil com duas casas decimais.

    - dataframes_by_month: {"YYYY-MM": pd.DataFrame}
    - output_dir: pasta onde salvar os arquivos
    """
    os.makedirs(output_dir, exist_ok=True)

    contabeis = [
        "VALOR TOTAL", "VALOR MÃO DE OBRA", "VALOR PEÇAS",
        "DESCONTO", "VALOR PAGO", "CARTÃO", "DINHEIRO",
        "PIX", "TROCO"
    ]

    for month, df in dataframes_by_month.items():
        filepath = os.path.join(output_dir, f"Recebimentos_{month}.xlsx")
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            sheet_name = month
            df.to_excel(writer, sheet_name=sheet_name, index=False)
            ws = writer.sheets[sheet_name]

            for idx, col in enumerate(df.columns, start=1):
                # Ajusta largura de cada coluna com base no conteúdo
                max_length = max(
                    df[col].astype(str).map(len).max(),
                    len(col)
                ) + 2
                ws.column_dimensions[get_column_letter(idx)].width = max_length

                # Aplica formatação contábil para colunas numéricas
                if col in contabeis:
                    for cell in ws[get_column_letter(idx)][1:]:
                        cell.number_format = 'R$ #,##0.00'
                        cell.alignment = Alignment(horizontal='left')
