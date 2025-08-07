from dataclasses import dataclass, field
from typing import Dict, List, Optional, Union
from collections import defaultdict
from pathlib import Path

NODAL_PATH = Path(r"C:\Program Files (x86)\Nodal_V63")
INITIAL_CYCLE = 2024
FINAL_CYCLE = 2032
VALID_YEARS = set(range(INITIAL_CYCLE, FINAL_CYCLE + 1))

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

    def calculate_avg_tust(self):
        """Calculate the average TUST values."""
        total_tust = defaultdict(lambda: defaultdict(float))
        generator_count = defaultdict(lambda: defaultdict(int))

        for generator in self.generators:
            subsystem = STATE_TO_SUBSYSTEM.get(generator.uf, '')
            for year, tust in generator.tust.items():
                if year in VALID_YEARS and tust > 0:
                    for category in [subsystem, generator.uf, generator.type]:
                        total_tust[category][year] += tust
                        generator_count[category][year] += 1

        avg_tust = {
            category: {year: round(value / generator_count[category][year], 2) for year, value in years.items()}
            for category, years in total_tust.items()
        }

        return avg_tust

    def calculate_must_values(self):
        """Calculate MUST values by type and total."""
        must_values_by_type = defaultdict(lambda: defaultdict(int))
        for generator in self.generators:
            for year, must in generator.must.items():
                must_values_by_type[generator.type][year] += must

        must_total_values = {
            year: sum(values[year] for values in must_values_by_type.values())
            for year in must_values_by_type[next(iter(must_values_by_type))].keys()
        }

        return must_values_by_type, must_total_values