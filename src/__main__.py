import sys
from src.cli import cli
from autotust import run_streamlit


def main():
    if len(sys.argv) > 1:
        cli()
    else:
        run_streamlit()


if __name__ == "__main__":
    main()
