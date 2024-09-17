import argparse
from pathlib import Path
import autotust


def cli():
    """Command-line interface for AutoTUST."""
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

    args = parser.parse_args()

    if args.command == 'nodal':
        csv_path = Path(args.path) / "autotust.csv"
        cycle_years, rap, pdr = autotust.read_autotust_csv(csv_path)
        autotust.run_nodal62(Path(args.path), cycle_years, rap, pdr)

    elif args.command == 'output':
        database = autotust.load_base(Path(args.path))
        autotust.get_tust_results(Path(args.path), database)

    elif args.command == 'clean':
        autotust.clean_ger(args.excel_path, args.db_path, args.output_path)


if __name__ == "__main__":
    cli()
