# Arquivo: modules/exporters.py

import os

#from pathlib import Path


def export_to_excel(dataframes_by_month: dict, output_dir: str):
    os.makedirs(output_dir, exist_ok=True)
    for month, df in dataframes_by_month.items():
        filepath = os.path.join(output_dir, f"Recebimentos_{month}.xlsx")
        df.to_excel(filepath, index=False)