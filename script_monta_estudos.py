import shutil

usinas = [
    {'NOME': 'JAIBA', 'MUST': 500.00, 'COD': 2024, 'BUS01_ONS': 7716, 'BUS01_EPE': 38911},
]

BASE_PATH = r'D:\dev\auto_tust\bases\BasePSR_RedeEPE_2022'

for usina in usinas:
    nome = str(usina['NOME'])
    must = float(usina['MUST'])
    cod = int(usina['COD'])

    CASE_PATH = f'D:\\dev\\auto_tust\\cases\\BasePSR_RedeEPE_2022_{nome}'
    shutil.copytree(BASE_PATH, CASE_PATH)
    
    for year in range(cod, 2032):
        bus01 = int(usina['BUS01_ONS']) if year <= 2026 else int(usina['BUS01_EPE'])
        bus02_ons = usina.get('BUS02_ONS')
        bus02_epe = usina.get('BUS02_EPE')
        bus02 = int(bus02_ons) if bus02_ons and year <= 2026 else int(bus02_epe) if bus02_epe and year > 2026 else None

        ger_file = CASE_PATH + f"\\{year}-{year+1}.GER"
        
        with open(ger_file, "r") as f:
            conteudo = f.readlines()
        
        if bus02:
            nova_linha = f'AAA {nome:28s} {must:8.2f}                             {bus01:5d}50.00{bus02:5d}50.00\n'
        else:
            nova_linha = f'AAA {nome:28s} {must:8.2f}                             {bus01:5d}\n'
        
        conteudo.insert(1, nova_linha)
        
        with open(ger_file, "w") as f:
            f.writelines(conteudo)
