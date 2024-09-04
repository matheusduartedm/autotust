"""
AutoTUST - Nodal Automation v1.0
Provides functionality for automating the Nodal v62 process for TUST calculations.
"""

import csv
import argparse
import subprocess
import logging
from typing import List, Dict, Union, Optional, Tuple
from dataclasses import dataclass, field
from pathlib import Path
import pandas as pd

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

NODAL_PATH = Path(r"C:\Program Files (x86)\Nodal_V62")
INITIAL_CYCLE = 2024
FINAL_CYCLE = 2033

SUBSYSTEM_MAP = {
    'N': ['AP', 'AM', 'PA', 'RR', 'TO', 'MA'],
    'NE': ['AL', 'BA', 'CE', 'PB', 'PE', 'PI', 'RN', 'SE'],
    'SE': ['ES', 'MG', 'RJ', 'SP', 'GO', 'MS', 'MT', 'DF', 'AC', 'RO'],
    'S': ['PR', 'RS', 'SC']
}

STATE_TO_SUBSYSTEM = {state: subsystem for subsystem, states in SUBSYSTEM_MAP.items() for state in states}


@dataclass
class Generator:
    """Represents a generator in the power system."""
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
    """Represents a bus in the power system."""
    num: int = 0
    name: str = ""
    area: int = 0
    circuits: Dict[int, List[int]] = field(default_factory=dict)
    tust: Dict[int, float] = field(default_factory=dict)


@dataclass
class CycleData:
    """Represents data for a specific cycle."""
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
    """Main database for storing generators, buses, and cycle data."""
    generators: List[Generator] = field(default_factory=list)
    buses: List[Bus] = field(default_factory=list)
    cycle_data: List[CycleData] = field(default_factory=list)

    def add_generator(self, generator: Generator) -> None:
        self.generators.append(generator)

    def add_bus(self, bus: Bus) -> None:
        self.buses.append(bus)

    def add_cycle_data(self, cycle_data: CycleData) -> None:
        self.cycle_data.append(cycle_data)

    def get_generator_by_name(self, name: str) -> Optional[Generator]:
        return next((g for g in self.generators if g.name == name), None)

    def get_bus_by_name(self, name: str) -> Optional[Bus]:
        return next((b for b in self.buses if b.name == name), None)


def _is_end_of_file(line: str) -> bool:
    return line[:2].strip() == "X"


def _is_comment(line: str) -> bool:
    return len(line) <= 1 or line[0] == "("


def _parse_float(value_str: str) -> Optional[float]:
    value_str = value_str.replace(".", "").replace(",", ".").strip()
    return float(value_str) if value_str and not value_str.startswith("-") else None


def load_ger_file(file_path: Path, year: int, database: Database) -> None:
    """Load data from a .GER file into the database."""
    if not file_path.exists():
        logger.warning(f"File {file_path} does not exist.")
        return

    with open(file_path, "r") as file:
        for line in file:
            if _is_comment(line):
                continue
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
    logger.info(f"Generators loaded for cycle {year}-{year + 1}.")


def load_tuh_file(file_path: Path, year: int, database: Database) -> None:
    """Load data from a .TUH file into the database."""
    if not file_path.exists():
        logger.warning(f"File {file_path} does not exist.")
        return

    with open(file_path, "r") as file:
        for line_number, line in enumerate(file, 1):
            if line_number <= 11 or _is_comment(line) or _is_end_of_file(line):
                continue
            if len(line) > 0:
                name = line[3:35].strip()
                tust = float(line[96:102])
                uf = line[51:53].strip()
                gen = database.get_generator_by_name(name)
                if gen:
                    gen.tust[year] = tust
                    gen.uf = gen.uf or uf
                else:
                    logger.warning(f"Generator {name} not found in the generator list.")


def load_r62_file(file_path: Path, year: int, database: Database) -> None:
    """Load data from a .R62 file into the database."""
    if not file_path.exists():
        logger.warning(f"File {file_path} does not exist.")
        return

    with open(file_path, 'r', encoding='ISO-8859-1') as file:
        lines = file.readlines()
        data = CycleData(year=year)
        data.rap = _parse_float(lines[7][88:106])
        data.mustg = _parse_float(lines[8][15:26])
        data.mustp = _parse_float(lines[8][55:66])
        data.mustfp = _parse_float(lines[8][75:86])
        teu_values = [_parse_float(lines[i][7:14]) if i < len(lines) else None for i in range(17, 20)]
        data.teug, data.teup, data.teufp = teu_values + [None] * (3 - len(teu_values))

    database.add_cycle_data(data)


def load_nos_file(file_path: Path, year: int, database: Database) -> None:
    """Load data from a .NOS file into the database."""
    if not file_path.exists():
        logger.warning(f"File {file_path} does not exist.")
        return

    with open(file_path, "r") as file:
        for line_number, line in enumerate(file, 1):
            if _is_end_of_file(line):
                break
            if line_number <= 11 or _is_comment(line):
                continue
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
                    logger.error(f"Error processing line {line_number} of file {file_path}: {e}")
                    logger.debug(f"Line content: {line.strip()}")


def load_base(db_path: Path) -> Database:
    """Load all data files into the database."""
    database = Database()
    years = range(2022, 2032)

    db_path = Path(db_path)  # Ensure DB_PATH is a Path object

    for year in years:
        ger_file = db_path / f"{year}-{year + 1}.GER"
        tuh_file = db_path / f"{year}-{year + 1}.TUH"
        r62_file = db_path / f"{year}-{year + 1}.R62"
        nos_file = db_path / f"{year}-{year + 1}.NOS"

        load_ger_file(ger_file, year, database)
        load_tuh_file(tuh_file, year, database)
        load_r62_file(r62_file, year, database)
        load_nos_file(nos_file, year, database)

    database.generators.sort(key=lambda x: x.name)
    for generator in database.generators:
        for year in range(2032, 2040):
            generator.tust[year] = generator.tust.get(year - 1, 0) - 0.02

    csv_file = db_path / "autotust_list.csv"
    years = list(range(2022, 2040))
    with open(csv_file, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["GENERATOR"] + [str(year) for year in years])
        for generator in database.generators:
            row = [generator.name] + [generator.tust.get(year, 0) for year in years]
            writer.writerow(row)

    return database


def _read_param62(file_path: Path) -> List[Union[str, float]]:
    """Read the param.v62 file."""
    param_list = []
    if file_path.exists():
        with open(file_path) as param_file:
            for iline, line in enumerate(param_file):
                contents = line if (iline <= 3 or line == "\n") else float(line)
                param_list.append(contents)
    logger.debug(f"Param62 contents: {param_list}")
    return param_list


def _write_param62(params: List[Union[str, float]], file_path: Path) -> None:
    """Write to the param.v62 file."""
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


def run_nodal62(case_path: Path, rap: List[float], pdr: List[float]) -> None:
    """Run Nodal v62 for all cycles."""
    params_file_path = NODAL_PATH / "param.v62"
    params = _read_param62(params_file_path)
    params[1] = str(NODAL_PATH)

    for i, cycle in enumerate(range(INITIAL_CYCLE, FINAL_CYCLE)):
        cycle_str = f"{cycle}-{cycle + 1}"
        params[2] = str(case_path / f"{cycle_str}.dc")
        params[3] = str(case_path / cycle_str)
        params[4] = rap[i]
        params[20] = pdr[i]
        _write_param62(params, params_file_path)

        command = "Nodal_F62.exe"
        try:
            subprocess.run(command, check=True, shell=True, cwd=NODAL_PATH)
        except subprocess.CalledProcessError as e:
            logger.error(f"Error running Nodal_F62.exe: {e}")
            return

        log_path = NODAL_PATH / "#ER_nod#.TX1"
        if log_path.exists():
            with open(log_path, "r") as file:
                logger.info(file.read())
        else:
            logger.warning("The file #ER_nod#.TX1 was not found.")


def read_autotust_csv(csv_path: Path) -> Tuple[List[float], List[int]]:
    """Read RAP and PDR values from CSV file."""
    rap_values, pdr_values = [], []
    with open(csv_path, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            rap_values.append(float(row['rap']))
            pdr_values.append(int(row['pdr']))
    return rap_values, pdr_values


def get_tust_results(case_path: Path, database: Database) -> None:
    """Generate TUST results CSV file."""
    years = range(2023, 2032)
    with open(case_path / "autotust_results.csv", mode='w', newline='') as file:
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


def run_streamlit_dashboard() -> None:
    """Run the Streamlit dashboard."""
    dashboard_script = Path(__file__).parent / 'scripts' / 'dashboard.py'
    try:
        subprocess.run(["streamlit", "run", str(dashboard_script)], check=True)
    except subprocess.CalledProcessError as e:
        logger.error(f"Error running Streamlit dashboard: {e}")


def clean_ger(excel_path: str, db_path: str, output_path: str) -> None:
    """Clean GER files based on the input Excel file."""
    excel = pd.ExcelFile(excel_path)
    years = range(2024, 2032)
    geradores_retirados_total = {}

    for year in years:
        ger_file = Path(db_path) / f"{year}-{year+1}.GER"
        new_ger_file = Path(db_path) / f"{year}-{year+1}_filtered.GER"

        sheet = str(year) if year < 2028 else str(2027)
        df = excel.parse(sheet)
        geradores_retirar = set(df[df['Status'] == 'Retirar']['name'])
        
        geradores_retirados = []
        if ger_file.exists():
            with open(ger_file, "r") as file, open(new_ger_file, "w") as new_file:
                for line in file:
                    name = line[0:32].strip()
                    if name in geradores_retirar:
                        geradores_retirados.append(name)
                        new_file.write('(' + line)
                    else:
                        new_file.write(line)
        geradores_retirados_total[year] = geradores_retirados
        logger.info(f"Ano {year}: {len(geradores_retirados)} geradores retirados.")

    df_geradores_retirados = pd.DataFrame(dict([(k, pd.Series(v)) for k, v in geradores_retirados_total.items()]))
    df_geradores_retirados.to_csv(Path(output_path) / "geradores_retirados.csv", index=False)
    logger.info("Cleaning process completed.")


def main() -> None:
    """Main function to run the AutoTUST program."""
    parser = argparse.ArgumentParser(description="AutoTUST - Nodal Automation v1.0")
    subparsers = parser.add_subparsers(dest='command', help='commands')

    nodal_parser = subparsers.add_parser('nodal', help='Run Nodal v62')
    nodal_parser.add_argument('path', type=str, help='Path to the case folder')

    output_parser = subparsers.add_parser('output', help='Get TUST results')
    output_parser.add_argument('path', type=str, help='Path to the case folder')

    clean_parser = subparsers.add_parser('clean', help='Clean GER files')
    clean_parser.add_argument('excel_path', type=str, help='Path to the Excel file with generators to remove')
    clean_parser.add_argument('db_path', type=str, help='Path to the database folder')
    clean_parser.add_argument('output_path', type=str, help='Path to save the output CSV file')

    subparsers.add_parser('dashboard', help='Run Streamlit Dashboard')

    args = parser.parse_args()

    if args.command == 'nodal':
        csv_path = Path(args.path) / "autotust.csv"
        rap, pdr = read_autotust_csv(csv_path)
        run_nodal62(Path(args.path), rap, pdr)

    elif args.command == 'output':
        database = load_base(Path(args.path))
        get_tust_results(Path(args.path), database)

    elif args.command == 'clean':
        clean_ger(args.excel_path, args.db_path, args.output_path)

    elif args.command == 'dashboard':
        run_streamlit_dashboard()


if __name__ == "__main__":
    main()
