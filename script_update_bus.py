import pandas as pd
import os

DB_PATH = r"D:\dev\auto_tust\cases\BasePSR_RedeEPE_2022"
excel_path = r"D:\dev\auto_tust\inputs\usinas_atualizar.xlsx"
excel = pd.ExcelFile(excel_path)
years = range(2031, 2032)

df = excel.parse('Sheet1')
geradores_barras = dict(zip(df['name'], df['barra']))

for year in years:
    ger_file = os.path.join(DB_PATH, f"{year}-{year+1}.GER")
    new_ger_file = os.path.join(DB_PATH, f"{year}-{year+1}_updated.GER")
    only_updated_ger_file = os.path.join(DB_PATH, f"{year}-{year+1}_only_updated.GER")

    if os.path.exists(ger_file):
        with open(ger_file, "r") as file, open(new_ger_file, "w") as new_file, open(only_updated_ger_file, "w") as only_updated_file:
            for line in file:
                name = line[0:32].strip()
                if name in geradores_barras:
                    new_bar = str(geradores_barras[name]).zfill(5)
                    updated_line = line[:70] + new_bar + line[75:]
                    new_file.write(updated_line)
                    only_updated_file.write(updated_line)
                else:
                    new_file.write(line)

    print(f"Ano {year}: Arquivo .GER atualizado.")

