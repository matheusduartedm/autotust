# AutoTUST

AutoTUST is a comprehensive Python-based tool for automating and analyzing TUST (Tarifa de Uso do Sistema de Transmissão) calculations in the Brazilian electrical system. It provides a suite of functionalities for processing electrical system data, running Nodal v61 simulations, and generating insightful reports and visualizations.

## Features

- Data loading and processing from various file formats (.GER, .TUH, .R61, .NOS)
- Automated execution of Nodal v61 simulations
- Generation of CSV reports for TUST results
- Interactive Streamlit dashboard for data visualization and analysis
- Various utility scripts for specific data processing tasks

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/your-username/autotust.git
   cd autotust
   ```

2. Create and activate a virtual environment:
   ```
   make_venv.bat
   ```

3. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

## Usage

AutoTUST can be used in three main ways:

1. Run Nodal v61 simulations:
   ```
   autotust nodal path/to/case/folder
   ```

2. Generate TUST results:
   ```
   autotust output path/to/case/folder
   ```

3. Launch the Streamlit dashboard:
   ```
   autotust dashboard
   ```

## Project Structure

- `autotust.py`: Main script containing core functionality
- `dashboard.py`: Streamlit dashboard for data visualization
- `scripts/`: Folder containing various utility scripts
- `bases/`: Directory for storing case data
- `make_exe.bat`: Script for building the executable
- `make_venv.bat`: Script for setting up the virtual environment
- `requirements.txt`: List of Python dependencies
- `autotust.spec`: PyInstaller specification file

## Building the Executable

To create a standalone executable:

```
make_exe.bat
```

The executable will be created in the `dist/` directory.

## Contributing

Contributions to AutoTUST are welcome! Please feel free to submit pull requests, create issues or spread the word.

## License

This project is licensed under the MIT License - see the LICENSE file for details.