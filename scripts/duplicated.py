import pandas as pd
from openpyxl import Workbook
import autotust as tust

# INPUTS
DB_PATH = r'D:\dev\auto_tust\cases\BasePSR'

# INICIANDO VARIÁVEIS
years = range(2023, 2032)
summary_data = []
yearly_data = []

# ITERAÇÃO SOBRE OS ANOS
for year in years:
    _, duplicated_generators = tust.load_ger(DB_PATH, year)
    total_must = 0
    rows = []
    for generator_list in duplicated_generators.values():
        for generator in generator_list:
            must = generator.must.get(year, 0)
            row = [generator.type, generator.name, must, generator.ceg, generator.cegnucleo]
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
    header = ['type', 'name', 'must', 'ceg', 'cegnucleo']
    ws_year.append(header)
    for row in data['rows']:
        ws_year.append(row)

wb.save(filename='outputs/duplicated.xlsx')
print(f"Excel file created")
