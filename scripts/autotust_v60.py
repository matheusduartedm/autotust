import os
import csv
import subprocess
import streamlit as st
import plotly.graph_objects as go
import numpy as np
import pandas as pd


class Generator:
    def __init__(self):
        self.name = ""
        self.must = {}
        self.bus = {}
        self.tust = {}

    def __str__(self):
        return f"<{self.name}>,<{self.must}>,<{self.bus}>,<{self.tust}>"
    
    def __repr__(self):
        return self.__str__()

    def set_tust(self, year, value):
        self.tust[year] = value

    def get_tust(self, year):
        return self.tust.get(year)


def _is_comment(line):
    return len(line) <= 1 or line[0] == "("


def _is_end_of_file(line):
    return line[:2].strip() == "X"


def _load_r60_data(r60_file):
    data = {}
    with open(r60_file, 'r', encoding='ISO-8859-1') as file:
        lines = file.readlines()
        # Extract RAP Total
        rap_total_str = lines[7][88:106].replace(".", "").replace(",", ".")
        data["RAP Total"] = float(rap_total_str) if rap_total_str.strip() not in ["", "------"] else None
        # Extract MUST Geração
        must_ger_str = lines[8][15:26].replace(".", "").replace(",", ".")
        data["MUST Geração"] = float(must_ger_str) if must_ger_str.strip() not in ["", "------"] else None
        # Extract MUST Consumo_P
        must_cp_str = lines[8][55:66].replace(".", "").replace(",", ".")
        data["MUST Consumo_P"] = float(must_cp_str) if must_cp_str.strip() not in ["", "------"] else None
        # Extract MUST Consumo_FP
        must_fp_str = lines[8][75:86].replace(".", "").replace(",", ".")
        data["MUST Consumo_FP"] = float(must_fp_str) if must_fp_str.strip() not in ["", "------"] else None
        # Extract TEU
        teu_values = []
        for i in range(17, 20):
            if i < len(lines):
                teu_str = lines[i][8:14].replace(",", ".")
                teu_values.append(float(teu_str) if teu_str.strip() not in ["", "------"] else None)
            else:
                teu_values.append(None)
        # Add TEUcf if it's missing
        if len(lines) < 20:
            teu_values.append(None)
        data["TEUg"] = teu_values[0]
        data["TEUcp"] = teu_values[1]
        data["TEUcf"] = teu_values[2]

    return data


def load_base(DB_PATH):
    generators = {}
    r60_data = {
        "RAP Total": {},
        "MUST Geração": {},
        "MUST Consumo_P": {},
        "MUST Consumo_FP": {},
        "TEUg": {},
        "TEUcp": {},
        "TEUcf": {},
    }
    years = range(2022, 2031)
    for year in years:
        ger_file = DB_PATH + f"\\{year}-{year+1}.GER"
        tuh_file = DB_PATH + f"\\{year}-{year+1}.TUH"
        r60_file = DB_PATH + f"\\{year}-{year+1}.R60"

        with open(ger_file, "r") as file:
            for line in file:
                if _is_comment(line):
                    continue

                if len(line) > 0:
                    name = line[0:32].strip()
                    if name not in generators:
                        generator = Generator()
                        generator.name = name
                        generators[name] = generator
                    generators[name].must[year] = float(line[32:41])
                    generators[name].bus[year] = int(line[70:75])

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

                    if name in generators:
                        generator = generators[name]
                        generators[name].tust[year] = tust

                    else:
                        print(f"Gerador {name} não encontrado na lista de geradores.")
        # Load .R60 data
        year_data = _load_r60_data(r60_file)
        for key in r60_data.keys():
            r60_data[key][year] = year_data[key]

        print(f"Geradores carregados para o ano {year}-{year+1}.")
    
    generators = sorted(generators.items(), key=lambda x: x[0])
    generators = dict(generators)

    # Adicionar anos extras para o dashboard
    extra_years = range(2031, 2040)
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
            
    return generators, r60_data


def create_dashboard(generators, r60_data):
    # Sidebar
    st.sidebar.title("Navigation")
    tab_names = ["Assumptions", "Results"]
    tab = st.sidebar.radio("", tab_names)

    if tab == "Results":
        st.write("## Results")
        generator_ids = list(generators.keys())
        generator_id = st.selectbox("Select the generator:", generator_ids)
        if generator_id in generators:
            generator = generators[generator_id]

            years = list(generator.tust.keys())
            tust_values = list(generator.tust.values())

            years = [int(year) for year in years]  # Convert years to integers

            # Calculate the average of tust_values for the specific generator
            average_generator = np.mean(tust_values)
            average_generator_line = [average_generator] * len(years)

            # Calculate the global average of all generators
            all_tust_values = []
            for g in generators.values():
                all_tust_values.extend(list(g.tust.values()))
            average_global = np.mean(all_tust_values)
            average_global_line = [average_global] * len(years)

            fig = go.Figure()
            fig.add_trace(go.Scatter(x=years, y=tust_values, mode='markers+lines', name='TUST'))
            fig.add_trace(go.Scatter(x=years, y=average_generator_line, mode='lines', name='Average (Generator)'))
            fig.add_trace(go.Scatter(x=years, y=average_global_line, mode='lines', name='Average (Global)'))

            fig.update_layout(title=f"TUST per Tariff Cycle for {generator_id}", xaxis_title='Tariff Cycle', yaxis_title='TUST [R$/kW.month - ref. Jun/2023]')
            st.plotly_chart(fig)

            # Calculate the nominal TUST
            iat = st.number_input("Enter the value of IAT (%):", value=4.0, step=0.5)
            risk_expansion = st.number_input("Enter the value of Risk Expansion (%):", value=5.0, step=0.5)
            limit = iat + risk_expansion  # define limit

            cumulative_iat = 1 + (iat / 100)
            tust_nominal_values = []
            controlled_tust = []
            limit_upper_values = []
            limit_lower_values = []

            for i, year in enumerate(years):
                cumulative_iat *= (1 + (iat / 100))
                tust_nominal = generator.tust[year] * cumulative_iat
                tust_nominal_values.append(tust_nominal)

                if i == 0:  # for the first year
                    controlled_tust.append(tust_nominal)
                    limit_upper_values.append(tust_nominal)
                    limit_lower_values.append(tust_nominal)
                else:  # for subsequent years
                    controlled_tust_prev = controlled_tust[i-1]
                    limit_upper = (controlled_tust_prev * 0.8 + tust_nominal * 0.2) * (1 + limit / 100)
                    limit_lower = (controlled_tust_prev * 0.8 + tust_nominal * 0.2) * (1 - limit / 100)
                    limit_upper_values.append(limit_upper)
                    limit_lower_values.append(limit_lower)

                    # The controlled_tust for the current year will be between the upper and lower limits
                    controlled_tust_current = max(min(tust_nominal, limit_upper), limit_lower)
                    controlled_tust.append(controlled_tust_current)

            fig_nominal = go.Figure()
            fig_nominal.add_trace(go.Scatter(x=years, y=limit_upper_values, mode='lines', name='Upper Limit', line=dict(width=0)))
            fig_nominal.add_trace(go.Scatter(x=years, y=limit_lower_values, mode='lines', name='Lower Limit', line=dict(width=0), fill='tonexty'))
            fig_nominal.add_trace(go.Scatter(x=years, y=tust_nominal_values, mode='markers+lines', name='TUST Nominal'))
            fig_nominal.add_trace(go.Scatter(x=years, y=controlled_tust, mode='markers+lines', name='TUST Controlled'))
            fig_nominal.update_layout(title=f"TUST Nominal per Tariff Cycle for {generator_id} (IAT = {iat}%)", xaxis_title='Tariff Cycle', yaxis_title='TUST Nominal [R$/kW.month - ref. Jun/Cycle]')
            st.plotly_chart(fig_nominal)

            # Create a download button for the selected generator
            data = pd.DataFrame.from_dict(generator.tust, orient='index', columns=['TUST'])
            data.index.name = 'Year'
            csv = data.to_csv().encode()
            st.download_button(label="Download generator data", data=csv, file_name=f"{generator_id}_tust_data.csv", mime="text/csv")

            # Create a download button for all generators
            all_data = pd.concat([pd.DataFrame.from_dict(g.tust, orient='index', columns=['TUST']).assign(Generator_id=gid) for gid, g in generators.items()])
            all_data.index.name = 'Year'
            all_csv = all_data.to_csv().encode()
            st.download_button(label="Download all data", data=all_csv, file_name="all_tust_data.csv", mime="text/csv")

        else:
            st.write(f"Generator {generator_id} not found.")
    

    elif tab == "Assumptions":
        st.write("## Assumptions")

        # Display the RAP data
        rap_years = list(r60_data["RAP Total"].keys())
        rap_values = list(r60_data["RAP Total"].values())

        fig_rap = go.Figure(data=[go.Bar(x=rap_years, y=rap_values)])
        fig_rap.update_layout(title="RAP Total by Year", xaxis_title="Year", yaxis_title="RAP Total")
        st.plotly_chart(fig_rap)

        # Display the MUST data
        must_years = list(r60_data["MUST Geração"].keys())
        must_ger_values = list(r60_data["MUST Geração"].values())
        must_cp_values = list(r60_data["MUST Consumo_P"].values())
        must_fp_values = list(r60_data["MUST Consumo_FP"].values())

        fig_must = go.Figure()
        fig_must.add_trace(go.Bar(x=must_years, y=must_ger_values, name="MUST Geração"))
        fig_must.add_trace(go.Bar(x=must_years, y=must_cp_values, name="MUST Consumo_P"))
        fig_must.add_trace(go.Bar(x=must_years, y=must_fp_values, name="MUST Consumo_FP"))
        fig_must.update_layout(title="MUST Data by Year", xaxis_title="Year", yaxis_title="Value")
        st.plotly_chart(fig_must)

        # Display the TEU data
        teu_years = list(r60_data["TEUg"].keys())
        teu_g_values = list(r60_data["TEUg"].values())
        teu_cp_values = list(r60_data["TEUcp"].values())
        teu_cf_values = list(r60_data["TEUcf"].values())

        fig_teu = go.Figure()
        fig_teu.add_trace(go.Bar(x=teu_years, y=teu_g_values, name="TEUg"))
        fig_teu.add_trace(go.Bar(x=teu_years, y=teu_cp_values, name="TEUcp"))
        fig_teu.add_trace(go.Bar(x=teu_years, y=teu_cf_values, name="TEUcf"))
        fig_teu.update_layout(title="TEU Data by Year", xaxis_title="Year", yaxis_title="Value")
        st.plotly_chart(fig_teu)
    

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
				param_file.write(f"{value}")
			elif 6 <= iparam <= 10:
				param_file.write(f"{value:05.1f}\n")
			elif iparam == 11:
				param_file.write(f"{value}")
			elif iparam <= 12:
				param_file.write(f"{value:013.2f}\n")
			else:
				param_file.write(f"{value:05.2f}\n")


""" def create_param_file(file_path, case_path, cycle):
	params = []
	params.append(os.path.join(case_path, cycle + ".dc"))
	params.append(os.path.join(case_path, cycle))
	# ...
	_write_param(params, file_path) """


def run_nodal61(case_path, rap = [34878790.43, 40271940.87, 41069253.80, 42026676.05, 42533399.85, 46770103.61, 43872400.04, 45880764.06, 46073219.29], pdr = [100, 90, 80, 70, 60, 50, 50, 50, 50]):
    NODAL_PATH = r"C:\Program Files (x86)\Nodal_V61"
    cycle_begin = 2022
    cycle_end = 2031
    working_path = NODAL_PATH
    params_file_path = os.path.join(NODAL_PATH, "param.v61")
    
    """ 	if not os.exists(params_file_path):
        create_param_file(params_file_path, case_path, cycle_begin) """

    params = _read_param(params_file_path)
    params[1] = NODAL_PATH
    for i, icycle in enumerate(range(cycle_begin, cycle_end)):
        cycle = f"{icycle}-{icycle+1}"
        params[2] = case_path + f"\{cycle}.dc"
        params[3] = case_path + f"\{cycle}"
        params[4] = rap[i]
        params[20] = pdr[i]
        _write_param(params, params_file_path)
        command = "Nodal_F61.exe"
        subprocess.run(command, check=True, shell=True, cwd=NODAL_PATH)

        log_path = os.path.join(NODAL_PATH, "#ER_nod#.TX1")		
        if os.path.exists(log_path):
            with open(log_path, "r") as file:
                file_content = file.read()
                print(file_content)
        else:
            print("O arquivo #ER_nod#.TX1 não foi encontrado.")


def _read_param60(file_path):
	param_list = []
	if os.path.exists(file_path):
		with open(file_path) as param_file:
			for iline, line in enumerate(param_file):
				contents = line.strip() if iline <= 3 else float(line)
				param_list.append(contents)
	return param_list


def _write_param60(params, file_path):
	with open(file_path, "w") as param_file:
		for iparam, value in enumerate(params):
			if iparam <= 3:
				param_file.write(f"{value}\n")
			elif iparam == 4:
				param_file.write(f"{value:013.2f}\n")
			elif iparam == 5:
				param_file.write(f"{value:010.5f}\n")
			elif 6 <= iparam <= 10:
				param_file.write(f"{value:05.1f}\n")
			elif 11 <= iparam <= 12:
				param_file.write(f"{value:013.2f}\n")
			else:
				param_file.write(f"{value:05.2f}\n")


def run_nodal60(case_path, rap = [34878790.43, 40271940.87, 41069253.80, 42026676.05, 42533399.85, 46770103.61, 43872400.04, 45880764.06, 46073219.29], pdr = [100, 90, 80, 70, 60, 50, 50, 50, 50]):
    NODAL_PATH = r"C:\Program Files (x86)\Nodal_V60"
    working_path = NODAL_PATH
    params_file_path = os.path.join(NODAL_PATH, "param.v60")
    params = _read_param60(params_file_path)
    params[1] = NODAL_PATH
    for i, icycle in enumerate(range(2022, 2031)):
        cycle = f"{icycle}-{icycle+1}"
        params[2] = case_path + f"\{cycle}.dc"
        params[3] = case_path + f"\{cycle}"
        params[4] = rap[i]
        params[20] = pdr[i]
        _write_param60(params, params_file_path)
        command = "Nodal_F60.exe"
        subprocess.run(command, check=True, shell=True, cwd=NODAL_PATH)

        log_path = os.path.join(NODAL_PATH, "#ER_nod#.TX1")		
        if os.path.exists(log_path):
            with open(log_path, "r") as file:
                file_content = file.read()
                print(file_content)
        else:
            print("O arquivo #ER_nod#.TX1 não foi encontrado.")