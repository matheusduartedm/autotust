import os
import csv
import subprocess
import argparse


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
                rap=[41244217.19, 42551207.39, 43105639.57, 46475182.88, 46449217.35, 47993366.19, 48134649.99,
                     48204543.25],
                pdr=[80, 70, 60, 50, 50, 50, 50, 50]):
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
        cycle = f"{icycle}-{icycle + 1}"
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


def read_autotust_csv(csv_path):
    with open(csv_path, newline='') as csvfile:
        reader = csv.DictReader(csvfile, delimiter='\t')
        rap_values, pdr_values = [], []
        for row in reader:
            rap_values.append(float(row['rap']))
            pdr_values.append(int(row['pdr']))
    return rap_values, pdr_values


def main():
    parser = argparse.ArgumentParser(description="AutoTUST - Nodal Automation v1.0")
    subparsers = parser.add_subparsers(dest='command', help='commands')
    nodal_parser = subparsers.add_parser('nodal', help='Run Nodal v61')
    nodal_parser.add_argument('path', type=str, help='Path to the case folder')

    args = parser.parse_args()

    if args.command == 'nodal':
        csv_path = os.path.join(args.path, "autotust.csv")
        rap, pdr = read_autotust_csv(csv_path)
        run_nodal61(args.path, rap, pdr)


if __name__ == "__main__":
    main()
