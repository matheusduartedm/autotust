import autotust_v61 as tust
import csv

ss = {'AP': 'N', 'AM': 'N', 'PA': 'N', 'RR': 'N', 'TO': 'N','MA': 'N', 
    'AL': 'NE', 'BA': 'NE', 'CE': 'NE', 'PB': 'NE', 'PE': 'NE', 'PI': 'NE', 'RN': 'NE', 'SE': 'NE',
    'ES': 'SE', 'MG': 'SE', 'RJ': 'SE', 'SP': 'SE', 'GO': 'SE', 'MS': 'SE', 'MT': 'SE', 'DF': 'SE', 'AC': 'SE', 'RO': 'SE',
    'PR': 'S', 'RS': 'S', 'SC': 'S'}

usinas = [
    {'NOME': 'MACEDONIA_F1_F2', 'MUST': 600.00, 'COD': 2027, 'BUS01_ONS': 536, 'BUS01_EPE': 2618, 'BUS02_ONS': 563, 'BUS02_EPE': 2632},
    {'NOME': 'BARRA', 'MUST': 237.60, 'COD': 2027, 'BUS01_ONS': 4350, 'BUS01_EPE': 38900, 'BUS02_ONS': 4333, 'BUS02_EPE': 26470},
    {'NOME': 'BARRA_UFV', 'MUST': 418.58, 'COD': 2027, 'BUS01_ONS': 4350, 'BUS01_EPE': 38900, 'BUS02_ONS': 4333, 'BUS02_EPE': 26470},
    {'NOME': 'ASAS_PUREZA', 'MUST': 547.70, 'COD': 2027, 'BUS01_ONS': 5128, 'BUS01_EPE': 360},
]

for usina in usinas:
    nome = str(usina['NOME'])
    CASE_PATH = f'D:\\dev\\auto_tust\\cases\\BasePSR_RedeEPE_2022_{nome}_ALT1'
    generators, _ = tust.load_base(CASE_PATH)
    csv_file = "outputs/tust2csv.csv"

    years = range(2023, 2032)
    with open(csv_file, mode='w', newline='') as file:
        writer = csv.writer(file)
        header = ["USINA", "SUBSISTEMA", "CEG"] + [str(year) for year in years] + ["MUST", "BUS_2023", "BUS_2030"]
        writer.writerow(header)

        for name, generator in generators.items():
            row = [name]
            
            subsistema = ss.get(generator.uf, '')
            row.extend([subsistema, generator.ceg])

            for year in years:
                tust_year = generator.tust.get(year, '-')
                row.extend([tust_year])
            
            must = generator.must.get(2030, '-')
            row.extend([must])
            bus23 = generator.bus.get(2023, '-')
            row.extend([bus23])
            bus30 = generator.bus.get(2030, '-')
            row.extend([bus30])
                
            writer.writerow(row)