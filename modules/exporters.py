import os
import pandas as pd
from openpyxl.utils import get_column_letter
from openpyxl.styles import Alignment, PatternFill


def export_to_excel(dataframes_by_month: dict, output_dir: str):
    """
    Salva cada DataFrame em planilhas Excel separadas por mês,
    ajustando largura de colunas, aplicando formatação contábil e cores.

    - dataframes_by_month: {"YYYY-MM": pd.DataFrame}
    - output_dir: pasta onde salvar os arquivos
    """
    os.makedirs(output_dir, exist_ok=True)

    contabeis = [
        "VALOR TOTAL", "VALOR MÃO DE OBRA", "VALOR PEÇAS",
        "DESCONTO", "VALOR PAGO", "DEVEDOR", "CARTÃO", "DINHEIRO",
        "PIX", "TROCO"
    ]
    # Definições de cores com maior contraste
    header_fill = PatternFill(fill_type="solid", start_color="FFBFBFBF", end_color="FFBFBFBF")  # cinza médio
    row_fill_light = PatternFill(fill_type="solid", start_color="FFFFFFFF", end_color="FFFFFFFF")  # branco
    row_fill_dark  = PatternFill(fill_type="solid", start_color="FFE6E6E6", end_color="FFE6E6E6")  # cinza mais escuro

    for month, df in dataframes_by_month.items():
        filepath = os.path.join(output_dir, f"Recebimentos_{month}.xlsx")
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            sheet_name = month
            df.to_excel(writer, sheet_name=sheet_name, index=False)
            ws = writer.sheets[sheet_name]

            # Ajusta largura e formata números
            for idx, col in enumerate(df.columns, start=1):
                max_length = max(df[col].astype(str).map(len).max(), len(col)) + 7
                ws.column_dimensions[get_column_letter(idx)].width = max_length
                if col in contabeis:
                    for cell in ws[get_column_letter(idx)][1:]:
                        cell.number_format = 'R$ #,##0.00'
                        cell.alignment = Alignment(horizontal='left')

            # Pinta cabeçalho
            for cell in ws[1]:
                cell.fill = header_fill

            # Aplica cores alternadas nas linhas de dados
            for row_idx in range(2, ws.max_row + 1):
                fill = row_fill_light if row_idx % 2 == 0 else row_fill_dark
                for col_idx in range(1, ws.max_column + 1):
                    ws.cell(row=row_idx, column=col_idx).fill = fill
