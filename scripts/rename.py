import os

directory = r'D:\dev\auto_tust\bases\BasePSR_RedeEPE_2022_TUSDg'

for filename in os.listdir(directory):
    if filename.startswith("2026-2027"):
        old_file = os.path.join(directory, filename)
        new_file = os.path.join(directory, filename.replace("2026-2027", "2027-2028"))
        os.rename(old_file, new_file)
        print(f"Renomeado: {old_file} para {new_file}")