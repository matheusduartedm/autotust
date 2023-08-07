import pandas as pd
from openpyxl import Workbook
import autotust_v61 as tust

# INPUTS
DB_PATH = r'D:\dev\auto_tust\cases\BasePSR'
ralie_df = pd.read_excel('ralie-usina.xlsx').set_index('IdeNucleoCEG')
ralie_unidade_df = pd.read_excel('ralie-unidade-geradora.xlsx').set_index('IdeNucleoCEG')

# INICIANDO VARIÁVEIS
years = range(2023, 2032)
summary_data = {"year": [year for year in years], "total_must": []}
yearly_data = []
bus_must_data = {}
previous_generators = set()

# ITERAÇÃO SOBRE OS ANOS
for year in years:
    generators, _ = tust.load_ger(DB_PATH, year)
    current_generators = set()
    rows = []
    total_must = 0
    bus_must = {}

    for generator in generators.values():
        current_generators.add(generator.name)

        if generator.name in previous_generators:
            continue

        must = generator.must.get(year, 0)
        total_must += must
        bus = generator.bus[year]
        bus_must[bus] = bus_must.get(bus, 0) + must

        additional_columns = ['', '', '', '']
        if generator.cegnucleo in ralie_df.index:
            additional_columns = ralie_df.loc[generator.cegnucleo, ['DscViabilidade', 'DscSituacaoObra', 'DscSitCCT', 'DscSitCust']].tolist()

        data_cod = ''
        if generator.cegnucleo in ralie_unidade_df.index:
            data_cod = ralie_unidade_df.query('IdeNucleoCEG == @generator.cegnucleo')['DatPrevisaoOpComercialSFG'].iloc[0]

        row = [generator.type, generator.name, must, generator.ceg, generator.cegnucleo] + additional_columns + [data_cod]
        rows.append(row)

    previous_generators = current_generators    
    summary_data["total_must"].append(total_must)
    yearly_data.append({"year": year, "rows": rows})
    bus_must_data[year] = bus_must

# OUTPUTS EM EXCEL
wb = Workbook()
ws_summary = wb.active
ws_summary.title = "Resumo"

for year, bus_must in bus_must_data.items():
    for bus, must in bus_must.items():
        bus_key = str(bus)
        if bus_key not in summary_data:
            summary_data[bus_key] = ['' for _ in range(len(years))]
        summary_data[bus_key][year - years[0]] = must

for key, row in summary_data.items():
    ws_summary.append([key] + row)

for data in yearly_data:
    ws_year = wb.create_sheet(title=str(data['year']))
    header = ['type', 'name', 'must', 'ceg', 'cegnucleo', 'DscViabilidade', 'DscSituacaoObra', 'DscSitCCT', 'DscSitCust', 'DatPrevisaoOpComercialSFG']
    ws_year.append(header)
    for row in data['rows']:
        ws_year.append(row)

wb.save(filename='outputs\entram.xlsx')
print(f"Excel file created")
