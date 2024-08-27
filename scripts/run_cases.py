import autotust_v61 as tust

#SEMPRE RODAR O SCRIPT COMO ADMINISTRADOR

rap23 = [41244217.19, 42551207.39, 43105639.57, 46475182.88, 46449217.35, 47993366.19, 48134649.99, 48204543.25]
pdr23 = [80, 70, 60, 50, 50, 50, 50, 50]
pdr_alt1 = [100, 100, 100, 100, 100, 100, 100, 100]
pdr_alt2a = [0, 0, 0, 0, 0, 0, 0, 0]

rap_edf = [41244217.19, 42416358.11, 42951646.92, 45702000.44, 44201906.72, 45366869.76, 45472930.51, 45525730.77]

usinas = [
    {'NOME': 'JAIBA', 'MUST': 500.00, 'COD': 2024, 'BUS01_ONS': 7716, 'BUS01_EPE': 38911},
]

for usina in usinas:
    nome = str(usina['NOME'])
    CASE_PATH = f'D:\\dev\\auto_tust\\cases\\BasePSR_RedeEPE_2022_{nome}'
    tust.run_nodal61(CASE_PATH, rap23, pdr23)