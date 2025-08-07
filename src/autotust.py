"""
AutoTUST - Nodal Automation v1.0
Provides functionality for automating the Nodal v63 process for TUST calculations.
"""

import csv
import logging
import os
from pathlib import Path
import subprocess
import sys
from typing import List, Union, Optional, Tuple

import pandas as pd

from models import Database, Generator, Bus, CycleData
from models import VALID_YEARS, STATE_TO_SUBSYSTEM, SUBSYSTEM_MAP, NODAL_PATH

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


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


def load_r63_file(file_path: Path, year: int, database: Database) -> None:
    """Load data from a .R63 file into the database."""
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
    years = range(2024, 2033)

    db_path = Path(db_path)  # Ensure DB_PATH is a Path object

    for year in years:
        ger_file = db_path / f"{year}-{year + 1}.GER"
        tuh_file = db_path / f"{year}-{year + 1}.TUH"
        r63_file = db_path / f"{year}-{year + 1}.R63"
        nos_file = db_path / f"{year}-{year + 1}.NOS"

        load_ger_file(ger_file, year, database)
        load_tuh_file(tuh_file, year, database)
        load_r63_file(r63_file, year, database)
        load_nos_file(nos_file, year, database)

    database.generators.sort(key=lambda x: x.name)
    for generator in database.generators:
        for year in range(2033, 2040):
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


def _read_param63(file_path: Path) -> List[Union[str, float]]:
    """Read the param.v63 file."""
    param_list = []
    if file_path.exists():
        with open(file_path) as param_file:
            for iline, line in enumerate(param_file):
                contents = line if (iline <= 3 or line == "\n") else float(line)
                param_list.append(contents)
    logger.debug(f"Param63 contents: {param_list}")
    return param_list


def _write_param63(params: List[Union[str, float]], file_path: Path) -> None:
    """Write to the param.v63 file."""
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


def run_nodal63(case_path: Path, cycle_years: List[int], rap: List[float], pdr: List[float], nodal_path: Optional[Path] = None) -> None:
    """Run Nodal v63 for specified cycles."""
    effective_nodal_path = nodal_path or NODAL_PATH
    params_file_path = effective_nodal_path / "param.v63"
    params = _read_param63(params_file_path)
    params[1] = str(effective_nodal_path)

    for i, cycle in enumerate(cycle_years):
        cycle_str = f"{cycle}-{cycle + 1}"
        params[2] = str(case_path / f"{cycle_str}.dc")
        params[3] = str(case_path / cycle_str)
        params[4] = rap[i]
        params[20] = pdr[i]
        _write_param63(params, params_file_path)

        command = "Nodal_F63.exe"
        try:
            subprocess.run(command, check=True, shell=True, cwd=effective_nodal_path)
        except subprocess.CalledProcessError as e:
            logger.error(f"Error running Nodal_F63.exe: {e}")
            return

        log_path = effective_nodal_path / "#ER_nod#.TX1"
        if log_path.exists():
            with open(log_path, "r") as file:
                logger.info(file.read())
        else:
            logger.warning("The file #ER_nod#.TX1 was not found.")


def read_autotust_csv(csv_path: Path) -> Tuple[List[int], List[float], List[int]]:
    """Read cycle years, RAP and PDR values from CSV file."""
    cycle_years, rap_values, pdr_values = [], [], []
    with open(csv_path, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            cycle_years.append(int(row['cycle']))
            rap_values.append(float(row['rap']))
            pdr_values.append(int(row['pdr']))
    return cycle_years, rap_values, pdr_values


def get_tust_results(case_path: Path, database: Database) -> None:
    """Generate TUST results CSV file for specified generators."""
    years = range(2024, 2033)
    input_file = case_path / "autotust_input_generators.csv"
    generator_list = None

    if input_file.exists():
        with open(input_file, 'r') as f:
            generator_list = [line.strip() for line in f.readlines()]
        logger.info(f"Using generator list from {input_file}")
    else:
        logger.info(f"File {input_file} not found. Using all generators.")

    with open(case_path / "autotust_results.csv", mode='w', newline='') as file:
        writer = csv.writer(file)
        header = ["USINA", "SUBSISTEMA", "CEG"] + [str(year) for year in years] + ["MUST_2032", "BUS_2023", "BUS_2032"]
        writer.writerow(header)

        for generator in database.generators:
            if generator_list is None or generator.name in generator_list:
                row = [generator.name]
                subsistema = STATE_TO_SUBSYSTEM.get(generator.uf, '')
                row.extend([subsistema, generator.ceg])
                for year in years:
                    tust_year = generator.tust.get(year, '-')
                    row.extend([tust_year])
                must31 = generator.must.get(2031, '-')
                row.extend([must31])
                bus24 = generator.bus.get(2024, '-')
                row.extend([bus24])
                bus31 = generator.bus.get(2031, '-')
                row.extend([bus31])
                writer.writerow(row)

    logger.info(f"TUST results written to {case_path / 'autotust_results.csv'}")


def run_streamlit() -> None:
    """Run the Streamlit dashboard."""
    if getattr(sys, 'frozen', False):
        # Running as compiled executable
        base_path = sys._MEIPASS
    else:
        # Running from source
        base_path = os.path.dirname(os.path.abspath(__file__))

    dashboard_script = os.path.join(base_path, 'gui.py')

    logger.info(f"Dashboard script path: {dashboard_script}")
    logger.info(f"Dashboard script exists: {os.path.exists(dashboard_script)}")

    if not os.path.exists(dashboard_script):
        logger.error(f"Dashboard script not found at {dashboard_script}")
        logger.info(f"Contents of {base_path}:")
        for root, dirs, files in os.walk(base_path):
            for name in files:
                logger.info(os.path.join(root, name))
        return

    try:
        # Use Python executable from sys.executable to ensure we're using the correct Python
        subprocess.run(["python", "-m", "streamlit", "run", dashboard_script], check=True)
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
