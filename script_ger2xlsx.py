import pandas as pd
from openpyxl import Workbook
import autotust_v61 as tust

# INPUTS
DB_PATH = r'D:\dev\auto_tust\cases\BasePSR'

# INICIANDO VARIÁVEIS
years = range(2023, 2032)
summary_data = []
yearly_data = []

# ITERAÇÃO SOBRE OS ANOS
for year in years:
    generators, _ = tust.load_ger(DB_PATH, year)
    total_must = 0
    rows = []
    for generator in generators.values():
        must = generator.must.get(year, 0)
        s = generator.s.get(year, 0)
        d = generator.d.get(year, 0)
        row = [generator.type, generator.name, must, s, d, generator.ceg, generator.cegnucleo]
        total_must += must
        rows.append(row)

    summary_data.append({"year": year, "total_must": total_must})
    yearly_data.append({"year": year, "rows": rows})


# OUTPUTS EM EXCEL
wb = Workbook()
ws_summary = wb.active
ws_summary.title = "Resumo"
ws_summary.append(['Year', 'Total MUST'])

for data in summary_data:
    ws_summary.append([data['year'], data['total_must']])

for data in yearly_data:
    ws_year = wb.create_sheet(title=str(data['year']))
    header = ['type', 'name', 'must', 's', 'd', 'ceg', 'cegnucleo']
    ws_year.append(header)
    for row in data['rows']:
        ws_year.append(row)

wb.save(filename='outputs/ger2xlsx.xlsx')
print(f"Excel file created")
