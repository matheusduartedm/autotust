import pandas as pd
from openpyxl import Workbook
import autotust as tust

# INPUTS
DB_PATH = r'D:\dev\auto_tust\cases\BasePSR_RedeEPE_2022'

# INICIANDO VARIÁVEIS
years = range(2023, 2032)
summary_data = []
yearly_data = []

# ITERAÇÃO SOBRE OS ANOS
for year in years:
    buses = tust.load_dc(DB_PATH, year)
    rows = []
    for bus in buses.values():
        circuits = bus.circuits.get(year, [])
        circuit_names = ", ".join([buses[num].name for num in circuits if num in buses])
        row = [bus.num, bus.name, bus.area, circuit_names]
        rows.append(row)

    yearly_data.append({"year": year, "rows": rows})

# OUTPUTS EM EXCEL
wb = Workbook()
ws_summary = wb.active
ws_summary.title = "Resumo"

for data in yearly_data:
    ws_year = wb.create_sheet(title=str(data['year']))
    header = ['num', 'name', 'area', 'circuits']
    ws_year.append(header)
    for row in data['rows']:
        ws_year.append(row)

wb.save(filename='outputs/dc2xlsx.xlsx')
print(f"Excel file created")