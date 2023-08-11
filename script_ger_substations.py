from openpyxl import Workbook
import autotust_v61 as tust

# INPUTS
DB_PATH = r'D:\dev\auto_tust\cases\BasePSR_v2'
barras_de_interesse = [5926, 6220, 4350, 6221, 6070]

# INICIANDO VARIÁVEIS
years = range(2023, 2032)
summary_data = {"year": [year for year in years]}
yearly_data = []
bus_must_data = {}

# ITERAÇÃO SOBRE OS ANOS
for year in years:
    generators, _ = tust.load_ger(DB_PATH, year)
    buses = tust.load_dc(DB_PATH, year)
    total_must = 0
    bus_must = {}
    bus_gen_names = {barra: [] for barra in barras_de_interesse}

    for generator in generators.values():
        must = generator.must.get(year, 0)
        total_must += must
        bus = generator.bus[year]

        if bus in barras_de_interesse:
            bus_must[bus] = bus_must.get(bus, 0) + must
            bus_gen_names[bus].append(generator.name)

    yearly_data.append({"year": year, "bus_gen_names": bus_gen_names, "bus_must": bus_must})

# OUTPUTS EM EXCEL
wb = Workbook()
ws_summary = wb.active
ws_summary.title = "Resumo"

for data in yearly_data:
    for bus, must in data['bus_must'].items():
        bus_key = str(bus)
        if bus_key not in summary_data:
            summary_data[bus_key] = ['' for _ in range(len(years))]
        summary_data[bus_key][data['year'] - years[0]] = must

for key, row in summary_data.items():
    ws_summary.append([key] + row)

for data in yearly_data:
    ws_year = wb.create_sheet(title=str(data['year']))
    header = ['Geradores'] + barras_de_interesse
    ws_year.append(header)
    max_length = max([len(names) for names in data['bus_gen_names'].values()])
    for i in range(max_length):
        row_data = ['']
        for barra in barras_de_interesse:
            if i < len(data['bus_gen_names'][barra]):
                row_data.append(data['bus_gen_names'][barra][i])
            else:
                row_data.append('')
        ws_year.append(row_data)

wb.save(filename='outputs\ger_substations.xlsx')
print(f"Excel file created")
