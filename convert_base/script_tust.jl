include("convert_base.jl")

cycles = ["2022-2023","2023-2024","2024-2025","2025-2026","2026-2027","2027-2028","2028-2029","2029-2030","2030-2031"]
tust_path = raw"C:\Users\matheusduarte\Desktop\TUST\BasePSR_Alt1e2A_RAP_Leilao_NovaTransicao"

#convert_ger(tust_path,cycles)
#convert_dc(tust_path,cycles)
#convert_tuh(tust_path,cycles)
#convert_nos(tust_path,cycles)
convert_all_base(tust_path, cycles)