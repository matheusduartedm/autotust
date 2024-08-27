import os
import csv
import argparse
import subprocess
from typing import List, Dict, Union, Optional
from dataclasses import dataclass, field
from pathlib import Path

NODAL_PATH = Path(r"C:\Program Files (x86)\Nodal_V61")
INITIAL_CYCLE = 2024
FINAL_CYCLE = 2032

SUBSYSTEM_MAP = {
    'N': ['AP', 'AM', 'PA', 'RR', 'TO', 'MA'],
    'NE': ['AL', 'BA', 'CE', 'PB', 'PE', 'PI', 'RN', 'SE'],
    'SE': ['ES', 'MG', 'RJ', 'SP', 'GO', 'MS', 'MT', 'DF', 'AC', 'RO'],
    'S': ['PR', 'RS', 'SC']
}

STATE_TO_SUBSYSTEM = {state: subsystem for subsystem, states in SUBSYSTEM_MAP.items() for state in states}


@dataclass
class Generator:
    type: str = ""
    name: str = ""
    ceg: str = ""
    cegnucleo: Union[int, str] = 0
    uf: str = ""
    must: Dict[int, float] = field(default_factory=dict)
    s: Dict[int, str] = field(default_factory=dict)
    d: Dict[int, str] = field(default_factory=dict)
    bus: Dict[int, int] = field(default_factory=dict)
    tust: Dict[int, float] = field(default_factory=dict)


@dataclass
class Bus:
    num: int = 0
    name: str = ""
    area: int = 0
    circuits: Dict[int, List[int]] = field(default_factory=dict)
    tust: Dict[int, float] = field(default_factory=dict)


@dataclass
class R61:
    year: int = 0
    rap: Optional[float] = None
    mustg: Optional[float] = None
    mustp: Optional[float] = None
    mustfp: Optional[float] = None
    teug: Optional[float] = None
    teup: Optional[float] = None
    teufp: Optional[float] = None


@dataclass
class Database:
    generators: List[Generator] = field(default_factory=list)
    buses: List[Bus] = field(default_factory=list)
    r61_data: List[R61] = field(default_factory=list)

    def add_generator(self, generator: Generator):
        self.generators.append(generator)

    def add_bus(self, bus: Bus):
        self.buses.append(bus)

    def add_r61(self, r61: R61):
        self.r61_data.append(r61)

    def get_generator_by_name(self, name: str) -> Optional[Generator]:
        return next((g for g in self.generators if g.name == name), None)

    def get_bus_by_name(self, name: str) -> Optional[Bus]:
        return next((b for b in self.buses if b.name == name), None)


def _is_end_of_file(line):
    return line[:2].strip() == "X"


def _is_comment(line):
    return len(line) <= 1 or line[0] == "("


def _parse_float(value_str):
    value_str = value_str.replace(".", "").replace(",", ".").strip()
    return float(value_str) if value_str and not value_str.startswith("-") else None


def load_ger_file(file_path: str, year: int, database: Database):
    if not os.path.exists(file_path):
        return

    with open(file_path, "r") as file:
        for line in file:
            if _is_comment(line):
                continue
            if _is_end_of_file(line):
                break
            if len(line) > 0:
                name = line[0:32].strip()
                gen = database.get_generator_by_name(name)
                if not gen:
                    gen = Generator()
                    gen.name = name
                    gen.type = name[0:3]
                    gen.ceg = line[52:62].strip()
                    gen.cegnucleo = int(line[55:60]) if line[55:60].strip().isdigit() else line[55:60].strip()
                    database.add_generator(gen)
                gen.d[year] = line[42:43].strip()
                gen.s[year] = line[44:45].strip()
                gen.must[year] = float(line[32:41].strip())
                gen.bus[year] = int(line[70:75].strip())
    print(f"Geradores carregados para o ano {year}-{year + 1}.")


def load_tuh_file(file_path: str, year: int, database: Database):
    if not os.path.exists(file_path):
        return

    with open(file_path, "r") as file:
        for line_number, line in enumerate(file, 1):
            if line_number <= 11 or _is_comment(line):
                continue
            if _is_end_of_file(line):
                break
            if len(line) > 0:
                name = line[3:35].strip()
                tust = float(line[96:102])
                uf = line[51:53].strip()
                gen = database.get_generator_by_name(name)
                if gen:
                    gen.tust[year] = tust
                    gen.uf = gen.uf or uf
                else:
                    print(f"Gerador {name} não encontrado na lista de geradores.")


def load_r61_file(file_path: str, year: int, database: Database):
    if not os.path.exists(file_path):
        return

    with open(file_path, 'r', encoding='ISO-8859-1') as file:
        lines = file.readlines()
        data = R61()
        data.year = year
        data.rap = _parse_float(lines[7][88:106])
        data.mustg = _parse_float(lines[8][15:26])
        data.mustp = _parse_float(lines[8][55:66])
        data.mustfp = _parse_float(lines[8][75:86])
        teu_values = [_parse_float(lines[i][7:14]) if i < len(lines) else None for i in range(17, 20)]
        data.teug, data.teup, data.teufp = teu_values + [None] * (3 - len(teu_values))

    database.add_r61(data)


def load_nos_file(file_path: str, year: int, database: Database):
    if not os.path.exists(file_path):
        return

    with open(file_path, "r") as file:
        for line_number, line in enumerate(file, 1):
            if line_number <= 11 or _is_comment(line):
                continue
            if _is_end_of_file(line):
                break
            if len(line) > 0:
                try:
                    name = line[8:21].strip()
                    tust = float(line[37:43].strip()) if line[37:43].strip() else 0
                    bus = database.get_bus_by_name(name)
                    if not bus:
                        bus = Bus()
                        bus.num = int(line[2:7].strip())
                        bus.name = line[8:20].strip()
                        database.add_bus(bus)
                    bus.tust[year] = tust
                except ValueError as e:
                    print(f"Erro ao processar linha {line_number} do arquivo {file_path}: {e}")
                    print(f"Conteúdo da linha: {line.strip()}")


def load_base(DB_PATH):
    database = Database()
    years = range(2022, 2032)

    for year in years:
        ger_file = os.path.join(DB_PATH, f"{year}-{year + 1}.GER")
        tuh_file = os.path.join(DB_PATH, f"{year}-{year + 1}.TUH")
        r61_file = os.path.join(DB_PATH, f"{year}-{year + 1}.R61")
        nos_file = os.path.join(DB_PATH, f"{year}-{year + 1}.NOS")

        load_ger_file(ger_file, year, database)
        load_tuh_file(tuh_file, year, database)
        load_r61_file(r61_file, year, database)
        load_nos_file(nos_file, year, database)

    database.generators.sort(key=lambda x: x.name)
    for generator in database.generators:
        for year in range(2032, 2040):
            generator.tust[year] = generator.tust.get(year - 1, 0) - 0.02

    csv_file = os.path.join(DB_PATH, "autotust_list.csv")
    years = list(range(2022, 2040))
    with open(csv_file, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["GENERATOR"] + [str(year) for year in years])
        for generator in database.generators:
            row = [generator.name] + [generator.tust.get(year, 0) for year in years]
            writer.writerow(row)

    return database


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


def run_nodal61(case_path, rap, pdr):
    params_file_path = os.path.join(NODAL_PATH, "param.v61")
    params = _read_param61(params_file_path)
    params[1] = str(NODAL_PATH)

    for i, cycle in enumerate(range(INITIAL_CYCLE, FINAL_CYCLE)):
        cycle_str = f"{cycle}-{cycle + 1}"
        params[2] = os.path.join(case_path, f"{cycle_str}.dc")
        params[3] = os.path.join(case_path, cycle_str)
        params[4] = rap[i]
        params[20] = pdr[i]
        _write_param61(params, params_file_path)

        command = "Nodal_F61.exe"
        subprocess.run(command, check=True, shell=True, cwd=NODAL_PATH)

        log_path = os.path.join(NODAL_PATH, "#ER_nod#.TX1")
        if os.path.exists(log_path):
            with open(log_path, "r") as file:
                print(file.read())
        else:
            print("O arquivo #ER_nod#.TX1 não foi encontrado.")


def read_autotust_csv(csv_path):
    with open(csv_path, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        rap_values, pdr_values = [], []
        for row in reader:
            rap_values.append(float(row['rap']))
            pdr_values.append(int(row['pdr']))
    return rap_values, pdr_values


def get_tust_results(case_path, database: Database):
    years = range(2023, 2032)
    with open(os.path.join(case_path, "autotust_results.csv"), mode='w', newline='') as file:
        writer = csv.writer(file)
        header = ["USINA", "SUBSISTEMA", "CEG"] + [str(year) for year in years] + ["MUST", "BUS_2023", "BUS_2030"]
        writer.writerow(header)

        for generator in database.generators:
            row = [generator.name]
            subsistema = STATE_TO_SUBSYSTEM.get(generator.uf, '')
            row.extend([subsistema, generator.ceg])
            for year in years:
                tust_year = generator.tust.get(year, '-')
                row.extend([tust_year])
            must = generator.must.get(2030, '-')
            row.extend([must])
            bus23 = generator.bus.get(2023, '-')
            row.extend([bus23])
            bus30 = generator.bus.get(2030, '-')
            row.extend([bus30])
            writer.writerow(row)


def run_streamlit_dashboard():
    dashboard_script = os.path.join(os.path.dirname(__file__), 'scripts', 'dashboard.py')
    subprocess.run(["streamlit", "run", dashboard_script], check=True)


def main():
    parser = argparse.ArgumentParser(description="AutoTUST - Nodal Automation v1.0")
    subparsers = parser.add_subparsers(dest='command', help='commands')

    nodal_parser = subparsers.add_parser('nodal', help='Run Nodal v61')
    nodal_parser.add_argument('path', type=str, help='Path to the case folder')

    output_parser = subparsers.add_parser('output', help='Get TUST results')
    output_parser.add_argument('path', type=str, help='Path to the case folder')

    dashboard_parser = subparsers.add_parser('dashboard', help='Run Streamlit Dashboard')

    args = parser.parse_args()

    if args.command == 'nodal':
        csv_path = os.path.join(args.path, "autotust.csv")
        rap, pdr = read_autotust_csv(csv_path)
        run_nodal61(args.path, rap, pdr)

    elif args.command == 'output':
        database = load_base(args.path)
        get_tust_results(args.path, database)

    elif args.command == 'dashboard':
        run_streamlit_dashboard()


if __name__ == "__main__":
    main()
