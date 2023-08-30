import autotust_v61 as tust
import csv

# INPUTS
DB_PATH = r'D:\dev\auto_tust\cases\BasePSR_RedeEPE_2022_Alt1'

generators, _ = tust.load_base(DB_PATH)
csv_file = "outputs/tust2csv.csv"

ss = {'AP': 'N', 'AM': 'N', 'PA': 'N', 'RR': 'N', 'TO': 'N','MA': 'N', 
    'AL': 'NE', 'BA': 'NE', 'CE': 'NE', 'PB': 'NE', 'PE': 'NE', 'PI': 'NE', 'RN': 'NE', 'SE': 'NE',
    'ES': 'SE', 'MG': 'SE', 'RJ': 'SE', 'SP': 'SE', 'GO': 'SE', 'MS': 'SE', 'MT': 'SE', 'DF': 'SE', 'AC': 'SE', 'RO': 'SE',
    'PR': 'S', 'RS': 'S', 'SC': 'S'}

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
            tust = generator.tust.get(year, '-')
            row.extend([tust])
        
        must = generator.must.get(2030, '-')
        row.extend([must])
        bus23 = generator.bus.get(2023, '-')
        row.extend([bus23])
        bus30 = generator.bus.get(2030, '-')
        row.extend([bus30])
            
        writer.writerow(row)