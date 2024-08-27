# AutoTUST

AutoTUST is a Python-based project for managing, analyzing, and visualizing TUST (Tarifa de Uso do Sistema de Transmissão) data. It provides a suite of tools for processing electrical system data, running simulations, and generating reports.

## Features

- Data loading and processing from various file formats (.GER, .DC, .R61, .NOS)
- Running Nodal v61 simulations
- Generating CSV and Excel reports
- Interactive dashboard for data visualization
- Various analysis scripts for specific use cases

## Project Structure

The project consists of multiple Python scripts, each serving a specific purpose:

- `autotust_v61.py`: Core functionality for data loading, processing, and running simulations
- `script_dashboard.py`: Creates an interactive dashboard using Streamlit
- `script_run_v61.py`: Runs the Nodal v61 simulation
- Various other scripts for specific data processing and analysis tasks

## Usage

### Running Nodal v61 Simulation

```python
import autotust_v61 as tust

BASE_PATH = "path/to/your/case/files"
rap = [...]  # List of RAP values
pdr = [...]  # List of PDR values

tust.run_nodal61(BASE_PATH, rap, pdr)
```

### Generating Reports

Various scripts are available for generating reports. For example:

```python
python script_tust2csv.py
```

### Running the Dashboard

```
streamlit run script_dashboard.py
```

## Scripts

The project includes several scripts for different purposes:

- `script_clean_ger.py`: Filters generators based on an Excel file
- `script_dc2xlsx.py`: Converts DC files to Excel format
- `script_ger2xlsx.py`: Converts GER files to Excel format
- `script_insert_gen.py`: Inserts new generators into GER files
- `script_monta_estudos.py`: Sets up study cases for specific power plants
- `script_muda_rb.py`: Analyzes changes in generator parameters
- `script_ralie.py`: Processes RALIE data
- `script_run_cases.py`: Runs multiple case studies
- `script_tust2csv.py`: Converts TUST data to CSV format
- `script_update_bus.py`: Updates bus information for generators
- `script_usinas_entram.py`: Analyzes new power plants entering the system
- `script_usinas_saem.py`: Analyzes power plants leaving the system

Each script is designed for a specific analysis or data processing task within the AutoTUST framework.
