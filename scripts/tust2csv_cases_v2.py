import autotust_v61 as tust
import csv

ss = {'AP': 'N', 'AM': 'N', 'PA': 'N', 'RR': 'N', 'TO': 'N','MA': 'N', 
    'AL': 'NE', 'BA': 'NE', 'CE': 'NE', 'PB': 'NE', 'PE': 'NE', 'PI': 'NE', 'RN': 'NE', 'SE': 'NE',
    'ES': 'SE', 'MG': 'SE', 'RJ': 'SE', 'SP': 'SE', 'GO': 'SE', 'MS': 'SE', 'MT': 'SE', 'DF': 'SE', 'AC': 'SE', 'RO': 'SE',
    'PR': 'S', 'RS': 'S', 'SC': 'S'}

usinas = [
    {'NOME': 'ARINOS', 'MUST': 337.00, 'COD': 2024, 'BUS01_ONS': 4349, 'BUS01_EPE': 39813},
    {'NOME': 'JAIBA', 'MUST': 500.00, 'COD': 2024, 'BUS01_ONS': 3389, 'BUS01_EPE': 38911},
    {'NOME': 'BARRO', 'MUST': 330.00, 'COD': 2024, 'BUS01_ONS': 229, 'BUS01_EPE': 3947},
]

for usina in usinas:
    nome = str(usina['NOME'])
    CASE_PATH = f'D:\\dev\\auto_tust\\cases\\BasePSR_RedeEPE_2022_{nome}'
    generators, buses, _ = tust.load_base(CASE_PATH)
    bus_num_to_bus_ons = {bus.num: bus for bus in buses.values() if isinstance(bus, tust.BusOns)}

    csv_file = CASE_PATH + "/tust2csv.csv"

    years = range(2023, 2041)
    with open(csv_file, mode='w', newline='') as file:
        writer = csv.writer(file)
        header = ["USINA", "SUBSISTEMA", "CEG"] + [str(year) for year in years]
        writer.writerow(header)

        for name, generator in generators.items():
            row = [name]
            
            subsistema = ss.get(generator.uf, '')
            row.extend([subsistema, generator.ceg])

            previous_numeric_tust = None
            for year in years:
                tust_value = None
                if year < usina['COD']:
                    bus01 = bus_num_to_bus_ons[usina['BUS01_ONS']]
                    bus02 = bus_num_to_bus_ons[usina['BUS02_ONS']] if 'BUS02_ONS' in usina else None

                    if bus01 and bus02:
                        tust_value = (bus01.tust.get(year, 0) + bus02.tust.get(year, 0)) / 2
                    elif bus01:
                        tust_value = bus01.tust.get(year, 0)
                    else:
                        tust_value = '-'
                else:
                    if year > 2031 and previous_numeric_tust is not None:
                        tust_value = previous_numeric_tust - 0.02
                    else:
                        tust_value = generator.tust.get(year, '-')
                    
                if isinstance(tust_value, (int, float)):
                    previous_numeric_tust = tust_value
                
                row.extend([tust_value])

            writer.writerow(row)