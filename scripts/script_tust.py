import autotust_v60


case_path = r"C:\Users\matheusduarte\Desktop\BasePSR_Alt1e2A_RAP_Leilao_NovaTransicao"
cycles = ["2022-2023","2023-2024","2024-2025","2025-2026","2026-2027","2027-2028","2028-2029","2029-2030","2030-2031"]


#convert_ger(tust_path,cycles)
#convert_dc(tust_path,cycles)
#convert_tuh(tust_path,cycles)
#convert_nos(tust_path,cycles)
autotust_v60.run(case_path, cycles)