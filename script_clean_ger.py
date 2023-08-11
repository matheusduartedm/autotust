import pandas as pd
import os

excel_path = r"D:\dev\auto_tust\inputs\usinas_retirar.xlsx"
excel = pd.ExcelFile(excel_path)
DB_PATH = r"D:\dev\auto_tust\cases\BasePSR_v2"
years = range(2024, 2032)

geradores_retirados_total = {}

for year in years:
    ger_file = DB_PATH + f"\\{year}-{year+1}.GER"
    new_ger_file = DB_PATH + f"\\{year}-{year+1}_filtered.GER"

    sheet = str(year) if year < 2028 else str(2027)
    df = excel.parse(sheet)
    geradores_retirar = set(df[df['Status'] == 'Retirar']['name'])
    
    geradores_retirados = []
    if os.path.exists(ger_file):
        with open(ger_file, "r") as file, open(new_ger_file, "w") as new_file:
            for line in file:
                name = line[0:32].strip()
                if name in geradores_retirar:
                    geradores_retirados.append(name)
                    new_file.write('(' + line)
                else:
                    new_file.write(line)
    geradores_retirados_total[year] = geradores_retirados
    print(f"Ano {year}: {len(geradores_retirados)} geradores retirados.")

df_geradores_retirados = pd.DataFrame(dict([(k, pd.Series(v)) for k, v in geradores_retirados_total.items() ]))
df_geradores_retirados.to_csv(r"D:\dev\auto_tust\outputs\geradores_retirados.csv", index=False)

