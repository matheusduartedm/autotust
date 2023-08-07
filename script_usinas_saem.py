import pandas as pd
from openpyxl import Workbook
import autotust_v61 as tust

# INPUTS
DB_PATH = r'D:\dev\auto_tust\cases\BasePSR'
ralie_df = pd.read_excel('ralie-usina.xlsx').set_index('IdeNucleoCEG')
ralie_unidade_df = pd.read_excel('ralie-unidade-geradora.xlsx').set_index('IdeNucleoCEG')

# INICIANDO VARIÁVEIS
years = range(2023, 2032)
previous_generators = {}
summary_data = []
yearly_data = []

# ITERAÇÃO SOBRE OS ANOS
for year in years:
    current_generators, _ = tust.load_ger(DB_PATH, year)
    missing_generators = set(previous_generators.keys()) - set(current_generators.keys())
    rows = []
    total_must = 0
    for generator_name in missing_generators:
        generator = previous_generators[generator_name]

        must = generator.must.get(year - 1, 0)
        additional_columns = ['', '', '', '']
        data_cod = ''

        if generator.cegnucleo in ralie_df.index:
            additional_columns = ralie_df.loc[generator.cegnucleo, ['DscViabilidade', 'DscSituacaoObra', 'DscSitCCT', 'DscSitCust']].tolist()

        if generator.cegnucleo in ralie_unidade_df.index:
            data_cod = ralie_unidade_df.query('IdeNucleoCEG == @generator.cegnucleo')['DatPrevisaoOpComercialSFG'].iloc[0]

        row = [generator.type, generator.name, must, generator.ceg, generator.cegnucleo] + additional_columns + [data_cod]
        total_must += must
        rows.append(row)

    previous_generators = current_generators
    summary_data.append([year, total_must])
    yearly_data.append({"year": year, "rows": rows})

# OUTPUTS EM EXCEL
wb = Workbook()
ws_summary = wb.active
ws_summary.title = "Resumo"
ws_summary.append(['Year', 'Total MUST'])

for row in summary_data:
    ws_summary.append(row)

for data in yearly_data:
    ws_year = wb.create_sheet(title=str(data['year']))
    header = ['type', 'name', 'must', 'ceg', 'cegnucleo', 'DscViabilidade', 'DscSituacaoObra', 'DscSitCCT', 'DscSitCust', 'DatPrevisaoOpComercialSFG']
    ws_year.append(header)
    for row in data['rows']:
        ws_year.append(row)

wb.save(filename='outputs\saem.xlsx')
print(f"Excel file created")
