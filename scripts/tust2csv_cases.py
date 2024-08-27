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
                #PEGAR TUST NO .NOS DE 2023 ATÉ O COD DA USINA
                tust_year = generator.tust.get(year, '-')
                row.extend([tust_year])
            
            must = generator.must.get(2030, '-')
            row.extend([must])
            bus23 = generator.bus.get(2023, '-')
            row.extend([bus23])
            bus30 = generator.bus.get(2030, '-')
            row.extend([bus30])
                
            writer.writerow(row)