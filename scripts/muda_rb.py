from openpyxl import Workbook
import autotust_v61 as tust

# INPUTS
DB_PATH = r'D:\dev\auto_tust\cases\BasePSR'

# INICIANDO VARIÁVEIS
years = range(2023, 2032)
summary_data = {'Ano': [], 'MUST Total': []}
yearly_data = {}
generators, _ = tust.load_base(DB_PATH)

# ITERAÇÃO SOBRE OS ANOS
for year in years:
    rows = []
    total_must = 0
    for generator_name, generator in generators.items():
        d_current = generator.d.get(year, '')
        d_previous = generator.d.get(year - 1, d_current)
        s_current = generator.s.get(year, '')
        s_previous = generator.s.get(year - 1, s_current)

        if s_previous != s_current or d_previous != d_current:
            row = [generator.name, generator.must.get(year, 0), d_previous, d_current,s_previous, s_current]
            rows.append(row)
            total_must += generator.must.get(year, 0)

    summary_data['Ano'].append(year)
    summary_data['MUST Total'].append(total_must)
    yearly_data[year] = rows

# OUTPUTS EM EXCEL
wb = Workbook()
ws_summary = wb.active
ws_summary.title = "Resumo"
ws_summary.append(['Year', 'Total MUST'])

for row in zip(summary_data['Ano'], summary_data['MUST Total']):
    ws_summary.append(row)

for year, rows in yearly_data.items():
    ws_year = wb.create_sheet(title=str(year))
    header = ['name', 'must', 'd_year-1', 'd_year', 's_year-1', 's_year']
    ws_year.append(header)
    for row in rows:
        ws_year.append(row)

wb.save(filename='outputs\muda_rb.xlsx')
print(f"Excel file created")
