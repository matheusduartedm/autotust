import csv
import pandas as pd

study_path = r"C:\Users\matheusduarte\Desktop\Teste\infos.csv"
study = pd.read_csv(study_path)

cycles = [
    "2022-2023", "2023-2024", "2024-2025", "2025-2026", "2026-2027",
    "2027-2028", "2028-2029", "2029-2030", "2030-2031"
]

df_tust = pd.DataFrame({
    "NOME": [],
    "TUST_22_23": [],
    "TUST_23_24": [],
    "TUST_24_25": [],
    "TUST_25_26": [],
    "TUST_26_27": [],
    "TUST_27_28": [],
    "TUST_28_29": [],
    "TUST_29_30": [],
    "TUST_30_31": []
})

for plant in range(len(study)):
    name = study.loc[plant, "NOME"]
    bus01_ons = study.loc[plant, "BUS01_ONS"]
    bus01_epe = study.loc[plant, "BUS01_EPE"]
    
    tust_dict = {}
    
    for cycle in cycles:
        tuh_path = study.loc[plant, "PATH"] + "\\tuh_" + cycle + ".csv"
        try:
            tuh = pd.read_csv(tuh_path)
            line = tuh.index[tuh["NAME"] == name][0]
            tust = tuh.loc[line, "TUST"]
            tust_dict[cycle] = tust
        except FileNotFoundError:
            nos_path = study.loc[plant, "PATH"] + "\\nos_" + cycle + ".csv"
            nos = pd.read_csv(nos_path)
            if bus01_ons in nos["NUMBER"].values:
                line = nos.index[nos["NUMBER"] == bus01_ons][0]
            else:
                line = nos.index[nos["NUMBER"] == bus01_epe][0]
            tust = float(nos.loc[line, "TUSTB"])
            tust_dict[cycle] = tust
    
    df_tust = df_tust.append({
        "NOME": name,
        "TUST_22_23": tust_dict["2022-2023"],
        "TUST_23_24": tust_dict["2023-2024"],
        "TUST_24_25": tust_dict["2024-2025"],
        "TUST_25_26": tust_dict["2025-2026"],
        "TUST_26_27": tust_dict["2026-2027"],
        "TUST_27_28": tust_dict["2027-2028"],
        "TUST_28_29": tust_dict["2028-2029"],
        "TUST_29_30": tust_dict["2029-2030"],
        "TUST_30_31": tust_dict["2030-2031"]
    }, ignore_index=True)

csv_path = os.path.join(result_path, "tust.csv")
df_tust.to_csv(csv_path, index=False)