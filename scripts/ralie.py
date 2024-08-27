import pandas as pd
from openpyxl import Workbook
import autotust_v61 as tust

# INPUTS
DB_PATH = r'D:\dev\auto_tust\cases\BasePSR'
ralie_df = pd.read_excel('inputs\ralie-usina.xlsx').set_index('IdeNucleoCEG')
ralie_unidade_df = pd.read_excel('inputs\ralie-unidade-geradora.xlsx').set_index('IdeNucleoCEG')

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

        additional_columns = ['', '', '', '']
        if generator.cegnucleo in ralie_df.index:
            additional_columns = ralie_df.loc[generator.cegnucleo, ['DscViabilidade', 'DscSituacaoObra', 'DscSitCCT', 'DscSitCust']].tolist()

        data_cod = ''
        if generator.cegnucleo in ralie_unidade_df.index:
            data_cod = ralie_unidade_df.query('IdeNucleoCEG == @generator.cegnucleo')['DatPrevisaoOpComercialSFG'].iloc[0]

        row = [generator.type, generator.name, must, generator.ceg, generator.cegnucleo] + additional_columns + [data_cod]
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
    header = ['type', 'name', 'must', 'ceg', 'cegnucleo', 'DscViabilidade', 'DscSituacaoObra', 'DscSitCCT', 'DscSitCust', 'DatPrevisaoOpComercialSFG']
    ws_year.append(header)
    for row in data['rows']:
        ws_year.append(row)

wb.save(filename='outputs/dados_ralie.xlsx')
print(f"Excel file created")
