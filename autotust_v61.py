import os
import csv
import subprocess

class Generator:
    def __init__(self):
        self.type = ""
        self.name = ""
        self.must = {}
        self.s = {}
        self.d = {}
        self.ceg = ""
        self.cegnucleo = 0
        self.bus = {}
        self.tust = {}
        self.uf = ""


class BusOns:
    def __init__(self):
        self.num = 0
        self.name = ""
        self.area = 0
        self.circuits = {}
        self.tust = {}


class BusEpe:
    def __init__(self):
        self.num = 0
        self.name = ""
        self.area = 0
        self.circuits = {}
        self.tust = {}


def _is_comment(line):
    return len(line) <= 1 or line[0] == "("


def _is_end_of_file(line):
    return line[:2].strip() == "X"


def _load_r61_data(r61_file):
    data = {}
    with open(r61_file, 'r', encoding='ISO-8859-1') as file:
        lines = file.readlines()
        # Extract rap
        rap_total_str = lines[7][88:106].replace(".", "").replace(",", ".")
        data["rap"] = float(rap_total_str) if rap_total_str.strip() not in ["", "------"] else None
        # Extract mustg
        must_ger_str = lines[8][15:26].replace(".", "").replace(",", ".")
        data["mustg"] = float(must_ger_str) if must_ger_str.strip() not in ["", "------"] else None
        # Extract mustp
        must_cp_str = lines[8][55:66].replace(".", "").replace(",", ".")
        data["mustp"] = float(must_cp_str) if must_cp_str.strip() not in ["", "------"] else None
        # Extract mustfp
        must_fp_str = lines[8][75:86].replace(".", "").replace(",", ".")
        data["mustfp"] = float(must_fp_str) if must_fp_str.strip() not in ["", "------"] else None
        # Extract TEU
        teu_values = []
        for i in range(17, 20):
            if i < len(lines):
                teu_str = lines[i][7:14].replace(",", ".")
                teu_values.append(float(teu_str) if teu_str.strip().strip('-') != "" else None)

            else:
                teu_values.append(None)

        if len(lines) < 20:
            teu_values.append(None)
        data["teug"] = teu_values[0]
        data["teup"] = teu_values[1]
        data["teufp"] = teu_values[2]

    return data


def load_dc(DB_PATH, year):
    dc_file = DB_PATH + f"\\{year}-{year+1}.DC"
    
    if os.path.exists(dc_file):
        buses = {}
        found_dbar = False
        found_dlin = False
        
        with open(dc_file, "r") as file:
            for line in file:
                stripped_line = line.strip()

                if stripped_line == "DBAR":
                    found_dbar = True
                    continue
                
                elif stripped_line == "DLIN":
                    found_dlin = True
                    continue
                
                if stripped_line == "99999":
                    found_dbar = found_dlin = False
                
                if not found_dbar and not found_dlin:
                    continue
                
                if _is_comment(line):
                    continue

                if len(stripped_line) > 0:
                    if found_dbar:
                        bus = Bus()
                        bus.num = int(line[0:5].strip())
                        bus.name = line[10:22].strip()
                        bus.area = int(line[76:78].strip())
                        buses[bus.num] = bus
                    elif found_dlin:
                        from_bus = int(line[0:5].strip())
                        to_bus = int(line[10:15].strip())
                        
                        if from_bus in buses:
                            if year not in buses[from_bus].circuits:
                                buses[from_bus].circuits[year] = []
                            if to_bus not in buses[from_bus].circuits[year]:
                                buses[from_bus].circuits[year].append(to_bus)
                        
                        if to_bus in buses:
                            if year not in buses[to_bus].circuits:
                                buses[to_bus].circuits[year] = []
                            if from_bus not in buses[to_bus].circuits[year]:
                                buses[to_bus].circuits[year].append(from_bus)

        return buses


def load_ger(DB_PATH, year):
    ger_file = DB_PATH + f"\\{year}-{year+1}.GER"
    if os.path.exists(ger_file):
        generators = {}
        duplicated_generators = {}
        with open(ger_file, "r") as file:
            for line in file:
                if _is_comment(line):
                    continue

                if len(line) > 0:
                    name = line[0:32].strip()
                    generator = Generator()
                    generator.name = name
                    generator.type = name[0:3]
                    generator.ceg = line[52:62].strip()
                    if generator.ceg[-7:][:5].strip():
                        generator.cegnucleo = int(generator.ceg[-7:][:5]) if generator.ceg[-7:][:5].isdigit() else generator.ceg[-7:][:5]

                    if name not in generators:
                        generators[name] = generator
                    else:
                        if name not in duplicated_generators:
                            duplicated_generators[name] = [generators[name]]

                    generator.d[year] = line[42:43].strip()
                    generator.s[year] = line[44:45].strip()
                    generator.must[year] = float(line[32:41].strip())
                    generator.bus[year] = int(line[70:75].strip())

        return generators, duplicated_generators


def load_base(DB_PATH):
    generators = {}
    buses = {}
    r61_data = {
        "rap": {},
        "mustg": {},
        "mustp": {},
        "mustfp": {},
        "teug": {},
        "teup": {},
        "teufp": {},
    }
    years = range(2022, 2032)
    for year in years:
        ger_file = DB_PATH + f"\\{year}-{year+1}.GER"
        tuh_file = DB_PATH + f"\\{year}-{year+1}.TUH"
        r61_file = DB_PATH + f"\\{year}-{year+1}.R61"
        nos_file = DB_PATH + f"\\{year}-{year+1}.NOS"

        if os.path.exists(ger_file):
            with open(ger_file, "r") as file:
                for line in file:
                    if _is_comment(line):
                        continue

                    if len(line) > 0:
                        name = line[0:32].strip()
                        if len(line) > 0:
                            name = line[0:32].strip()
                            if name not in generators:
                                generator = Generator()
                                generator.name = name
                                generator.type = name[0:3]
                                generator.ceg = line[52:62].strip()
                                if generator.ceg[-7:][:5].strip():
                                    generator.cegnucleo = int(generator.ceg[-7:][:5]) if generator.ceg[-7:][:5].isdigit() else generator.ceg[-7:][:5]
                                generators[name] = generator
                            generators[name].d[year] = line[42:43].strip()
                            generators[name].s[year] = line[44:45].strip()
                            generators[name].must[year] = float(line[32:41].strip())
                            generators[name].bus[year] = int(line[70:75].strip())
                print(f"Geradores carregados para o ano {year}-{year+1}.")


        if os.path.exists(tuh_file):
            with open(tuh_file, "r") as file:
                line_number = 0

                for line in file:
                    line_number += 1

                    if line_number <= 11:
                        continue

                    if _is_comment(line):
                        continue

                    if _is_end_of_file(line):
                        break

                    if len(line) > 0:
                        name = line[3:35].strip()
                        tust = float(line[96:102])
                        uf = line[51:53].strip()
                        if name in generators:
                            generator = generators[name]
                            generators[name].tust[year] = tust
                            generators[name].uf = generators[name].uf if generators[name].uf else uf

                        else:
                            print(f"Gerador {name} não encontrado na lista de geradores.")

        if os.path.exists(r61_file):
            year_data = _load_r61_data(r61_file)
            for key in r61_data.keys():
                r61_data[key][year] = year_data[key]

        if os.path.exists(nos_file):
            with open(nos_file, "r") as file:
                line_number = 0

                for line in file:
                    line_number += 1

                    if line_number <= 11:
                        continue

                    if _is_comment(line):
                        continue

                    if _is_end_of_file(line):
                        break

                    if len(line) > 0:
                        name = line[8:21].strip()
                        tust = float(line[37:43].strip()) if line[37:43].strip() else 0
                        if name not in buses:
                            bus = BusOns() if year <= 2026 else BusEpe()
                            bus.num = int(line[2:7].strip())
                            bus.name = line[8:20].strip()
                            bus.tust[year] = tust
                            buses[name] = bus
                        else:
                            buses[name].tust[year] = tust

    # Ordenar os geradores por nome  
    generators = sorted(generators.items(), key=lambda x: x[0])
    generators = dict(generators)

    # Adicionar anos extras para o dashboard
    extra_years = range(2032, 2040)
    for name in generators:
        generator = generators[name]
        for year in extra_years:
            generator.tust[year] = generator.tust.get(year-1, 0) - 0.02

    combined_years = list(years) + list(extra_years)

    # Criar o arquivo CSV
    csv_file = DB_PATH + "\\" + "autotust_list.csv"
    with open(csv_file, mode='w', newline='') as file:
        writer = csv.writer(file)
        header = ["GENERATOR"] + [str(year) for year in combined_years]
        writer.writerow(header)

        for name, generator in generators.items():
            row = [name]
            for year in combined_years:
                tust = generator.tust.get(year, 0)
                row.extend([tust])
            writer.writerow(row)

    return generators, buses, r61_data
   

def _read_param61(file_path):
    param_list = []
    if os.path.exists(file_path):
        with open(file_path) as param_file:
            for iline, line in enumerate(param_file):
                contents = line if (iline <= 3 or line == "\n") else float(line)
                param_list.append(contents)
    print(param_list)
    return param_list


def _write_param61(params, file_path):
	with open(file_path, "w") as param_file:
		for iparam, value in enumerate(params):
			if iparam == 0:
				param_file.write(f"{value}")
			elif 1 <= iparam <= 3:
				param_file.write(f"{value}\n")
			elif iparam == 4:
				param_file.write(f"{value:013.2f}\n")
			elif iparam == 5:
				param_file.write(f"{value}\n")
			elif 6 <= iparam <= 10:
				param_file.write(f"{value:05.1f}\n")
			elif iparam <= 11:
				param_file.write(f"{value:013.2f}\n")
			else:
				param_file.write(f"{value:05.2f}\n")


""" def create_param_file(file_path, case_path, cycle):
        params = []
        params.append(os.path.join(case_path, cycle + ".dc"))
        params.append(os.path.join(case_path, cycle))
        # ...
        _write_param(params, file_path) """


def run_nodal61(case_path, 
                rap = [41244217.19, 42551207.39, 43105639.57, 46475182.88, 46449217.35, 47993366.19, 48134649.99, 48204543.25], 
                pdr = [80, 70, 60, 50, 50, 50, 50, 50]):
    NODAL_PATH = r"C:\Program Files (x86)\Nodal_V61"
    cycle_begin = 2024
    cycle_end = 2032
    working_path = NODAL_PATH
    params_file_path = os.path.join(NODAL_PATH, "param.v61")
    
    """ 	if not os.exists(params_file_path):
        create_param_file(params_file_path, case_path, cycle_begin) """

    params = _read_param61(params_file_path)
    params[1] = NODAL_PATH
    for i, icycle in enumerate(range(cycle_begin, cycle_end)):
        cycle = f"{icycle}-{icycle+1}"
        params[2] = case_path + f"\{cycle}.dc"
        params[3] = case_path + f"\{cycle}"
        params[4] = rap[i]
        params[20] = pdr[i]
        _write_param61(params, params_file_path)
        command = "Nodal_F61.exe"
        subprocess.run(command, check=True, shell=True, cwd=NODAL_PATH)

        log_path = os.path.join(NODAL_PATH, "#ER_nod#.TX1")		
        if os.path.exists(log_path):
            with open(log_path, "r") as file:
                file_content = file.read()
                print(file_content)
        else:
            print("O arquivo #ER_nod#.TX1 não foi encontrado.")