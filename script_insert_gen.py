import pandas as pd

df_usinas = pd.read_excel('inputs/usinas_compiladas.xlsx')

CASE_PATH = 'D:\\dev\\auto_tust\\cases\\BasePSR_RedeEPE_2022_EDF'

for _, usina in df_usinas.iterrows():
    nome = str(usina['NOME'])
    
    for year in range(2024, 2032):
        must = float(usina[year])
        
        if must == 0:
            continue
        
        bus01 = int(usina['BUS01_ONS']) if year <= 2026 else int(usina['BUS01_EPE'])
        ger_file = CASE_PATH + f"\\{year}-{year+1}.GER"
        
        with open(ger_file, "r") as f:
            conteudo = f.readlines()
        
        nova_linha = f'AAA {nome:28s} {must:8.2f}                             {bus01:5d}\n'
        conteudo.insert(1, nova_linha)
        
        with open(ger_file, "w") as f:
            f.writelines(conteudo)